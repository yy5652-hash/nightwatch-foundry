"""Independent real browser recovery from two Stage1 origins and old Stage2 singles/pairs."""
import argparse,asyncio,json,time
from pathlib import Path
from urllib.parse import urlsplit
from reconstruction_probe import validate_release,fixture,encoded,parse,same,sha,DAY
from reconstruction_requirements import ORIGINS

async def run(release,out):
    from playwright.async_api import async_playwright,expect
    out=Path(out);out.mkdir(parents=True,exist_ok=False);checks=[];trace=[];errors=[];stopped=[];count={'direct':0,'browser':0,'forwards':0};started=time.monotonic()
    def check(key,value):
        checks.append(dict(requirement_id='TK2R-upgrade-'+key,passed=bool(value)))
        if not value:raise AssertionError(key)
    async with async_playwright() as pw:
        http=await pw.request.new_context();browser=await pw.chromium.launch(headless=True)
        async def call(base,method,path,raw=None,headers=None,private=False):
            r=await http.fetch(base+path,method=method,data=raw,headers=headers or {'content-type':'application/json; charset=utf-8'},timeout=10000 if path.startswith('/_test/') else 5000)
            data=await r.body();count['direct']+=1
            trace.append(dict(event='direct',base=base,method=method,path=path,status=r.status,request_sha256=sha(raw or b''),response_sha256=sha(data),request_bytes=len(raw or b''),response_bytes=len(data),private_decoded=False if private else None))
            return r.status,None if private or not data else parse(data),data
        try:
            for origin,seating in [('legacy-s1','single'),('exact-s1','single'),('legacy-s2','single'),('legacy-s2','pair')]:
                stem=origin+'-'+seating+'-';source=release['urls'][origin];target=release['urls']['target'];peer=release['urls']['peer'];stage=ORIGINS[origin][1]
                status,_,_=await call(source,'POST','/_test/reset',encoded(fixture()));check(stem+'fixture',status==204)
                context=await browser.new_context(viewport={'width':375 if seating=='pair' else 1280,'height':900},timezone_id='Pacific/Honolulu');page=await context.new_page();page.set_default_timeout(5000)
                routing={'new':False};auth={};capture={};navigation=[]
                page.on('framenavigated',lambda frame:navigation.append(frame.url) if frame==page.main_frame else None)
                def request_observed(r):
                    count['browser']+=1;trace.append(dict(event='browser-request',path=urlsplit(r.url).path,method=r.method,body_sha256=sha((r.post_data or '').encode()),key_sha256=sha(r.headers.get('idempotency-key','').encode())))
                page.on('request',request_observed)
                async def proxy(route):
                    r=route.request;p=urlsplit(r.url)
                    if routing['new'] or not p.path.startswith(('/auth/','/restaurants','/availability','/reservations','/reservation-moves')):await route.continue_();return
                    hdr={k:v for k,v in r.headers.items() if k in ('authorization','idempotency-key','content-type','accept')};path=p.path+('?' +p.query if p.query else '')
                    response=await http.fetch(source+path,method=r.method,headers=hdr,data=r.post_data,timeout=5000);raw=await response.body();count['forwards']+=1
                    if p.path=='/auth/login':auth.update(token=parse(raw).get('token'),status=response.status)
                    trace.append(dict(event='actual-source-forward',origin=origin,seating=seating,path=path,status=response.status,response_sha256=sha(raw)))
                    await route.fulfill(status=response.status,headers={'content-type':response.headers.get('content-type','application/json; charset=utf-8')},body=raw)
                try:
                    await page.route('**/*',proxy);await page.goto(target+'/login')
                    await page.get_by_test_id('login-email').fill('reconstruct@probe.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click();await expect(page.get_by_test_id('current-user')).to_contain_text('Independent Diner');check(stem+'source-auth',auth.get('status')==200 and bool(auth.get('token')))
                    hdr={'content-type':'application/json; charset=utf-8','authorization':'Bearer '+auth['token'],'idempotency-key':'retained-'+stem}
                    retained_body=dict(restaurant_id='r',table_id='c',party_size=2,starts_at_local=DAY+'T20:00')
                    if stage==1:retained_body['table_ids']={'ignored_at_source':True}
                    raw_retained=encoded(retained_body);status,retained,_=await call(source,'POST','/reservations',raw_retained,hdr);check(stem+'retained-create',status==201)
                    moves={'moves':[dict(reference=retained['reference'],party_size=3)]}
                    if stage==1:moves['moves'][0]['table_ids']='originally ignored'
                    raw_moves=encoded(moves);move_hdr={**hdr,'idempotency-key':'move-'+stem};status,move_original,_=await call(source,'POST','/reservation-moves',raw_moves,move_hdr);check(stem+'retained-moves',status==201)
                    await page.goto(target+'/');await page.get_by_test_id('restaurant-select').select_option('r');await page.get_by_test_id('date-input').fill(DAY);party='9' if seating=='pair' else '2';await page.get_by_test_id('party-size-input').fill(party);await page.get_by_test_id('search-button').click();await expect(page.get_by_test_id('availability-grid')).to_be_visible()
                    ids=['b','a'] if seating=='pair' else ['a'];await page.get_by_test_id('slot-'+'+'.join(ids)+'-18:00').click();await expect(page.get_by_test_id('booking-form')).to_be_visible()
                    async def committed_drop(route):
                        r=route.request;capture.update(raw=r.post_data.encode(),key=r.headers['idempotency-key'],authorization=r.headers['authorization'])
                        response=await http.fetch(source+'/reservations',method='POST',headers=r.headers,data=capture['raw'],timeout=5000);data=await response.body();count['forwards']+=1;capture.update(status=response.status,receipt=parse(data));trace.append(dict(event='actual-committed-response-drop',origin=origin,seating=seating,status=response.status,body_sha256=sha(capture['raw']),key_sha256=sha(capture['key'].encode()),receipt_sha256=sha(data)));await route.abort('connectionfailed')
                    await page.route('**/reservations',committed_drop,times=1);await page.get_by_test_id('booking-submit').click();await expect(page.get_by_test_id('booking-uncertain')).to_be_visible();check(stem+'commit',capture['status']==201)
                    confirmation=page.get_by_test_id('confirmation');check(stem+'uncertain',bool(await page.get_by_test_id('booking-uncertain').text_content()) and await page.get_by_test_id('booking-error').count()==0 and (await confirmation.count()==0 or not await confirmation.is_visible()))
                    await page.screenshot(path=str(out/(stem+'uncertain.png')),full_page=True)
                    before=dict(url=page.url,nav=len(navigation),party=await page.get_by_test_id('booking-party-size').input_value(),summary=await page.get_by_test_id('booking-summary').text_content())
                    status,_,export=await call(source,'GET','/_test/export',private=True);status2,_,_=await call(target,'POST','/_test/import',export,private=True);check(stem+'raw-import',status==200 and status2==204);trace.append(dict(event='actual-unchanged-upgrade',origin=origin,seating=seating,bytes=len(export),sha256=sha(export),decoded=False));routing['new']=True
                    check(stem+'same-document',page.url==before['url'] and len(navigation)==before['nav'] and await page.get_by_test_id('booking-party-size').input_value()==before['party'] and await page.get_by_test_id('booking-summary').text_content()==before['summary'])
                    async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:await page.get_by_test_id('booking-submit').click()
                    response=await pending.value;receipt=parse(await response.body());await expect(page.get_by_test_id('confirmation')).to_be_visible()
                    check(stem+'body-key-user',response.request.post_data.encode()==capture['raw'] and response.request.headers['idempotency-key']==capture['key'] and response.request.headers['authorization']==capture['authorization'])
                    check(stem+'original-receipt',response.status==200 and same(receipt,capture['receipt']) and await page.get_by_test_id('confirmation-reference').text_content()==receipt['reference'])
                    check(stem+'original-shape',('table_ids' in receipt)==(stage==2) and ('table_id' in receipt)==(seating=='single'))
                    check(stem+'clear-uncertainty',await page.get_by_test_id('booking-uncertain').count()==0 and await page.get_by_test_id('booking-error').count()==0)
                    check(stem+'same-document',len(navigation)==before['nav'])
                    auth_hdr={'authorization':capture['authorization']};status,current,_=await call(target,'GET','/reservations',headers=auth_hdr);check(stem+'one-booking',status==200 and len(current['reservations'])==2)
                    for path,raw,key,original in [('/reservations',raw_retained,'retained-'+stem,retained),('/reservation-moves',raw_moves,'move-'+stem,move_original)]:
                        status,actual,_=await call(target,'POST',path,raw,{**auth_hdr,'content-type':'application/json; charset=utf-8','idempotency-key':key});check(stem+'retained-originals',status==200 and same(actual,original))
                    # Add one actual exact current write and transfer mixed origin state raw to a peer.
                    extra=encoded(dict(restaurant_id='r',table_ids=['a'],party_size=2,starts_at_local=DAY+'T21:30',ignored=1));new_hdr={**auth_hdr,'content-type':'application/json; charset=utf-8','idempotency-key':'new-'+stem};status,new_receipt,_=await call(target,'POST','/reservations',extra,new_hdr);check(stem+'new-write',status==201)
                    status,_,mixed=await call(target,'GET','/_test/export',private=True);status2,_,_=await call(peer,'POST','/_test/import',mixed,private=True);check(stem+'mixed-peer',status==200 and status2==204)
                    for raw,key,original in [(capture['raw'],capture['key'],capture['receipt']),(extra,'new-'+stem,new_receipt)]:
                        status,actual,_=await call(peer,'POST','/reservations',raw,{**auth_hdr,'content-type':'application/json; charset=utf-8','idempotency-key':key});check(stem+'mixed-originals',status==200 and same(actual,original))
                    await page.goto(target+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(retained['reference']);await page.get_by_test_id('lookup-submit').click();await expect(page.get_by_test_id('reservation-detail')).to_be_visible();check(stem+'lookup-token',await page.get_by_test_id('reservation-status').text_content()=='confirmed' and 'Independent Diner' in await page.get_by_test_id('current-user').text_content());await page.screenshot(path=str(out/(stem+'lookup.png')),full_page=True)
                finally:await context.close()
        except AssertionError as e:stopped.append(dict(recorded_failed_expectation=str(e),dependent_paths='unverified'))
        except Exception as e:errors.append(dict(type=type(e).__name__,message=str(e)))
        finally:await browser.close();await http.dispose()
    data=dict(candidate=release['candidate'],assertions=len(checks),failures=sum(not x['passed'] for x in checks),counts=count,runner_errors=errors,stopped_after_expectation=stopped,seconds=time.monotonic()-started)
    for name,value in [('summary.json',data),('assertions.json',checks),('trace.json',trace)]:(out/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(data));return bool(errors or stopped or data['failures'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate_release(json.loads(Path(a.release).read_text()));raise SystemExit(asyncio.run(run(release,a.out)))
if __name__=='__main__':main()
