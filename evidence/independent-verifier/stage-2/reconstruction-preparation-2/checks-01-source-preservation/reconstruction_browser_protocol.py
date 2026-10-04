"""Real browser supplements. Lazy browser import keeps preparation noninteractive."""
import argparse
import asyncio
import json
import re
import time
import datetime as dt
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlsplit,quote,parse_qs
from reconstruction_probe import validate_release,fixture,encoded,parse,same,sha,Number,DAY
from reconstruction_requirements import ORIGINS,ID_CASES

def opaque_ids(label):
    suffix={'reserved':'?&#=', 'unicode':'é汉𝄞', 'spaces':' seat ', 'plus':'+', 'percent':'%2F', 'slash':'/part', 'max64':'x'*63, 'numeric-looking':'9007199254740993'}[label]
    return tuple(prefix+suffix for prefix in ('r','a','b','c'))

def numeric_cases():
    values=('9007199254740993','1000000000000000000001','1'+'0'*399+'1','1'+'0'*4299+'1')
    return [(spelling,seating,digits) for spelling in ('integer','decimal-integral','exponent-integral')
        for seating in ('single','pair') for digits in values]

def token_spelling(digits,spelling):
    return digits if spelling=='integer' else digits+'.0' if spelling=='decimal-integral' else digits+'e0'

async def execute(release,out,case):
    from playwright.async_api import async_playwright,expect
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    results=[];trace=[];errors=[];counts=dict(http=0,browser=0);began=time.monotonic()
    def check(key,condition):
        results.append(dict(requirement_id='TK2R-'+key,passed=bool(condition)))
        if not condition:raise AssertionError(key)
    async with async_playwright() as runtime:
        http=await runtime.request.new_context();browser=await runtime.chromium.launch(headless=True)
        async def call(base,method,path,raw=None,headers=None,public=True):
            response=await http.fetch(base+path,method=method,data=raw,headers=headers or {'content-type':'application/json; charset=utf-8'},timeout=10000 if path.startswith('/_test/') else 5000)
            payload=await response.body();counts['http']+=1
            trace.append(dict(event='direct-http',base=base,method=method,path=path,status=response.status,request_bytes=len(raw or b''),request_sha256=sha(raw or b''),response_bytes=len(payload),response_sha256=sha(payload),decoded=public))
            return response.status,parse(payload) if public and payload else None,payload
        async def page_context(width=1280):
            context=await browser.new_context(viewport={'width':width,'height':900},timezone_id='Pacific/Honolulu')
            page=await context.new_page();page.set_default_timeout(5000)
            def observe(request):
                counts['browser']+=1
                trace.append(dict(event='browser-request',method=request.method,path=urlsplit(request.url).path,
                    query=urlsplit(request.url).query,body_sha256=sha((request.post_data or '').encode()),key_sha256=sha(request.headers.get('idempotency-key','').encode()),authorization_present='authorization' in request.headers))
            page.on('request',observe);return context,page
        async def login(page):
            await page.goto(release['urls']['target']+'/login')
            await page.get_by_test_id('login-email').fill('reconstruct@probe.invalid')
            await page.get_by_test_id('login-password').fill('independent-pass')
            await page.get_by_test_id('login-submit').click()
            await expect(page.get_by_test_id('current-user')).to_contain_text('Independent Diner')
        async def search(page,rid,digits):
            await page.goto(release['urls']['target']+'/')
            await page.get_by_test_id('restaurant-select').select_option(rid)
            await page.get_by_test_id('date-input').fill(DAY)
            await page.get_by_test_id('party-size-input').fill(digits)
            async with page.expect_request(lambda r:urlsplit(r.url).path=='/availability') as pending:
                await page.get_by_test_id('search-button').click()
            await expect(page.get_by_test_id('availability-grid')).to_be_visible()
            return await pending.value
        try:
            if case in ('upgrade','all'):
                for origin in ('legacy-s1','exact-s1'):
                    source=release['urls'][origin];target=release['urls']['target'];prefix='browser-'+origin+'-'
                    status,_,_=await call(source,'POST','/_test/reset',encoded(fixture()));check(prefix+'auth',status==204)
                    context,page=await page_context();routing={'current':False};capture={};navigation=[]
                    page.on('framenavigated',lambda frame:navigation.append(frame.url) if frame==page.main_frame else None)
                    async def proxy(route):
                        request=route.request;parsed=urlsplit(request.url)
                        if routing['current'] or not parsed.path.startswith(('/auth/','/restaurants','/availability','/reservations','/reservation-moves')):
                            await route.continue_();return
                        path=parsed.path+('?' + parsed.query if parsed.query else '')
                        headers={k:v for k,v in request.headers.items() if k in ('authorization','idempotency-key','content-type','accept')}
                        response=await http.fetch(source+path,method=request.method,headers=headers,data=request.post_data,timeout=5000)
                        raw=await response.body()
                        trace.append(dict(event='real-source-api-forward',origin=origin,method=request.method,path=path,status=response.status,raw_response_sha256=sha(raw)))
                        await route.fulfill(status=response.status,headers={'content-type':response.headers.get('content-type','application/json; charset=utf-8')},body=raw)
                    try:
                        await page.route('**/*',proxy);await login(page)
                        await search(page,'r','2');await page.get_by_test_id('slot-a-18:00').click()
                        await expect(page.get_by_test_id('booking-form')).to_be_visible()
                        async def drop_committed(route):
                            request=route.request;capture.update(raw=request.post_data.encode(),key=request.headers['idempotency-key'],authorization=request.headers['authorization'])
                            response=await http.fetch(source+'/reservations',method='POST',headers=request.headers,data=capture['raw'],timeout=5000)
                            raw=await response.body();capture.update(status=response.status,receipt=parse(raw),response_raw=raw)
                            await route.abort('connectionfailed')
                        await page.route('**/reservations',drop_committed,times=1)
                        await page.get_by_test_id('booking-submit').click()
                        await expect(page.get_by_test_id('booking-uncertain')).to_be_visible()
                        check(prefix+'commit',capture['status']==201)
                        check(prefix+'uncertain',bool(await page.get_by_test_id('booking-uncertain').text_content()) and await page.get_by_test_id('booking-error').count()==0 and await page.get_by_test_id('confirmation').count()==0)
                        await page.screenshot(path=str(out/(origin+'-uncertain.png')),full_page=True)
                        retained_raw=encoded(dict(restaurant_id='r',table_id='c',starts_at_local=DAY+'T20:00',party_size=2))
                        status,retained,_=await call(source,'POST','/reservations',retained_raw,{'content-type':'application/json; charset=utf-8','authorization':capture['authorization'],'idempotency-key':'retained-'+origin})
                        check(prefix+'retained',status==201)
                        before=dict(url=page.url,input=await page.get_by_test_id('booking-party-size').input_value(),summary=await page.get_by_test_id('booking-summary').text_content(),navigations=len(navigation))
                        status,_,export=await call(source,'GET','/_test/export',public=False)
                        status2,_,_=await call(target,'POST','/_test/import',export,public=False)
                        check(prefix+'export',status==200 and status2==204)
                        trace.append(dict(event='unchanged-raw-upgrade',origin=origin,bytes=len(export),sha256=sha(export),decoded=False))
                        routing['current']=True
                        check(prefix+'no-reload',page.url==before['url'] and len(navigation)==before['navigations'] and await page.get_by_test_id('booking-party-size').input_value()==before['input'] and await page.get_by_test_id('booking-summary').text_content()==before['summary'])
                        async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:
                            await page.get_by_test_id('booking-submit').click()
                        response=await pending.value;receipt=parse(await response.body())
                        check(prefix+'body',response.request.post_data.encode()==capture['raw'])
                        check(prefix+'key',response.request.headers['idempotency-key']==capture['key'])
                        await expect(page.get_by_test_id('confirmation')).to_be_visible()
                        check(prefix+'original',response.status==200 and same(receipt,capture['receipt']) and await page.get_by_test_id('confirmation-reference').text_content()==receipt['reference'])
                        check(prefix+'shape','table_ids' not in capture['receipt'] and 'table_id' in capture['receipt'])
                        await page.goto(target+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(retained['reference']);await page.get_by_test_id('lookup-submit').click()
                        await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
                        check(prefix+'lookup',await page.get_by_test_id('reservation-status').text_content()=='confirmed' and 'Independent Diner' in await page.get_by_test_id('current-user').text_content())
                        status,current,_=await call(target,'GET','/reservations',headers={'authorization':capture['authorization']})
                        check(prefix+'one-record',status==200 and len(current['reservations'])==2)
                        await page.screenshot(path=str(out/(origin+'-retained-lookup.png')),full_page=True)
                    finally:await context.close()
            if case in ('numeric','controls','all'):
                for spelling,seating,digits in numeric_cases():
                    prefix=f'numeric-{spelling}-{seating}-';n=int(digits);f=fixture();tables=f['restaurants'][0]['tables']
                    caps=[n,n-1,1] if seating=='single' else [n//2,n-n//2,1]
                    for table,capacity in zip(tables,caps):table['capacity']=Number(token_spelling(str(capacity),spelling))
                    status,_,_=await call(release['urls']['target'],'POST','/_test/reset',encoded(f));check(prefix+'fixture',status==204)
                    context,page=await page_context(375 if len(digits)>400 else 1280)
                    ids=['a'] if seating=='single' else ['b','a'];cell='slot-'+'+'.join(ids)+'-18:00'
                    try:
                        await login(page);request=await search(page,'r',digits)
                        check(prefix+'query',parse_qs(urlsplit(request.url).query).get('party_size')==[digits])
                        locator=page.get_by_test_id(cell);await expect(locator).to_be_visible()
                        visible=await locator.text_content();check(prefix+'visible-capacity',digits in visible)
                        await locator.click();field=page.get_by_test_id('booking-party-size')
                        check('native-value',await field.input_value()==digits)
                        check('role',await field.get_attribute('role')=='spinbutton' and await field.get_attribute('inputmode')=='numeric')
                        field_id=await field.get_attribute('id')
                        labels=page.locator('label').filter(has=field) if not field_id else page.locator('label[for='+json.dumps(field_id)+']')
                        check('label',await labels.count()>0 and bool((await labels.first.text_content()).strip()) and await labels.first.is_visible())
                        await field.focus()
                        style=await field.evaluate('(e)=>{let s=getComputedStyle(e);return {outline:s.outlineStyle,width:s.outlineWidth,color:s.outlineColor,shadow:s.boxShadow}}')
                        check('focus',style['outline']!='none' and style['width']!='0px' or style['shadow']!='none')
                        control=field.locator('xpath=..')
                        for _ in range(3):
                            if await control.locator('button').count()>=2:break
                            control=control.locator('xpath=..')
                        buttons=control.locator('button');changes=[]
                        for i in range(min(await buttons.count(),2)):
                            await field.fill(digits);button=buttons.nth(i)
                            if not await button.is_visible():continue
                            await button.click();changes.append(int(await field.input_value())-n)
                        check('buttons',sorted(changes)==[-1,1]);await field.fill(digits)
                        await field.press('ArrowUp');check('keyboard',await field.input_value()==str(n+1));await field.press('ArrowDown');check('keyboard',await field.input_value()==digits)
                        corrupt={}
                        async def corrupt_real_committed(route):
                            response=await route.fetch();actual=await response.body()
                            corrupt.update(status=response.status,receipt=parse(actual),actual_sha256=sha(actual))
                            malformed=actual[:-1]+b',0:0}'
                            trace.append(dict(event='real-committed-response-syntax-fault',actual_status=response.status,actual_sha256=sha(actual),fault_sha256=sha(malformed)))
                            await route.fulfill(status=response.status,headers={'content-type':response.headers.get('content-type','application/json; charset=utf-8')},body=malformed)
                        await page.route('**/reservations',corrupt_real_committed,times=1)
                        async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:
                            await page.get_by_test_id('booking-submit').click()
                        broken=await pending.value;raw=broken.request.post_data;sent=parse(raw)
                        await expect(page.get_by_test_id('booking-uncertain')).to_be_visible()
                        check(prefix+'malformed',corrupt['status']==201 and await page.get_by_test_id('confirmation').count()==0 and await page.get_by_test_id('booking-error').count()==0)
                        async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:
                            await page.get_by_test_id('booking-submit').click()
                        response=await pending.value;receipt=parse(await response.body())
                        check(prefix+'body',same(sent.get('party_size'),n) and re.search(r'"party_size"\s*:\s*'+digits+r'\s*[,}]',raw) is not None)
                        check(prefix+'create',corrupt['status']==201 and response.status==200 and same(receipt,corrupt['receipt']) and same(receipt.get('party_size'),n))
                        await expect(page.get_by_test_id('confirmation')).to_be_visible()
                        async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:
                            await page.get_by_test_id('booking-submit').click()
                        replay=await pending.value;check(prefix+'retry',replay.status==200 and replay.request.post_data==raw and replay.request.headers['idempotency-key']==response.request.headers['idempotency-key'] and same(parse(await replay.body()),receipt))
                        await page.goto(release['urls']['target']+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(receipt['reference']);await page.get_by_test_id('lookup-submit').click()
                        await expect(page.get_by_test_id('reservation-detail')).to_be_visible();detail=await page.get_by_test_id('reservation-detail').text_content()
                        check(prefix+'visible-party',digits in detail)
                        widths=await page.evaluate('({scroll:document.documentElement.scrollWidth,width:innerWidth})');check('mobile',widths['scroll']<=widths['width'])
                        trace.append(dict(event='actual-numeric-spelling',spelling_input=spelling,seating=seating,request_party_lexeme=digits,response_sha256=sha(await response.body()),capacity_text_sha256=sha(visible.encode()),party_digits=len(digits)))
                        await page.screenshot(path=str(out/(f'{spelling}-{seating}-{len(digits)}-lookup.png')),full_page=True)
                    finally:await context.close()
                for zone in ('Europe/Berlin','Europe/Brussels','America/New_York'):
                    for origin in ('current','legacy-s1'):
                        source=release['urls']['target'] if origin=='current' else release['urls'][origin]
                        f=fixture();f['restaurants'][0]['timezone']=zone
                        status,_,_=await call(source,'POST','/_test/reset',encoded(f))
                        if status!=204:raise RuntimeError('historical fixture refused')
                        status,auth,_=await call(source,'POST','/auth/login',encoded(dict(email='reconstruct@probe.invalid',password='independent-pass')))
                        if status!=200:raise RuntimeError('historical real login refused')
                        headers={'content-type':'application/json; charset=utf-8','authorization':'Bearer '+auth['token'],'idempotency-key':'historic'}
                        raw=encoded(dict(restaurant_id='r',table_id='a',starts_at_local='0001-01-01T18:00',party_size=2))
                        status,receipt,_=await call(source,'POST','/reservations',raw,headers)
                        if status!=201:raise RuntimeError('historical real create refused')
                        if origin!='current':
                            _,_,export=await call(source,'GET','/_test/export',public=False)
                            status,_,_=await call(release['urls']['target'],'POST','/_test/import',export,public=False)
                            if status!=204:raise RuntimeError('genuine historical replacement refused')
                            status,replay,_=await call(release['urls']['target'],'POST','/reservations',raw,headers)
                            if status!=200 or not same(replay,receipt):raise AssertionError('original historic receipt changed')
                        context,page=await page_context(375)
                        try:
                            await login(page);await page.goto(release['urls']['target']+'/lookup')
                            await page.get_by_test_id('lookup-reference-input').fill(receipt['reference']);await page.get_by_test_id('lookup-submit').click()
                            await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
                            start=dt.datetime(1,1,1,18,tzinfo=ZoneInfo(zone));end=(start.astimezone(dt.timezone.utc)+dt.timedelta(minutes=90)).astimezone(ZoneInfo(zone))
                            expected=f'{end.hour:02}:{end.minute:02}'
                            end_text=await page.locator('dl div').filter(has=page.locator('dt',has_text='Ends at')).locator('dd').text_content()
                            check('historic-current' if origin=='current' else 'historic-legacy',expected in end_text)
                            status_text=page.get_by_test_id('reservation-status')
                            trace.append(dict(event='actual-status-text',dom=await status_text.text_content(),rendered=await status_text.inner_text(),transform=await status_text.evaluate('(e)=>getComputedStyle(e).textTransform')))
                            check('status',await status_text.text_content()=='confirmed')
                            await page.screenshot(path=str(out/('historic-'+origin+'-'+zone.replace('/','-')+'.png')),full_page=True)
                        finally:await context.close()
            if case in ('opaque','all'):
                for label in ID_CASES:
                    rid,a,b,c=opaque_ids(label);f=fixture((rid,a,b,c));status,_,_=await call(release['urls']['target'],'POST','/_test/reset',encoded(f))
                    check('opaque-'+label+'-admission',status==204)
                    context,page=await page_context()
                    try:
                        await login(page);request=await search(page,rid,'2');check('opaque-'+label+'-query',parse_qs(urlsplit(request.url).query)['restaurant_id']==[rid])
                        single=page.get_by_test_id('slot-'+a+'-18:00');pair=page.get_by_test_id('slot-'+b+'+'+a+'-18:00')
                        check('opaque-'+label+'-grid',await single.count()==1 and await pair.count()==1)
                        await pair.click();summary=await page.get_by_test_id('booking-summary').text_content();check('opaque-'+label+'-labels','Window Alcove' in summary and 'Garden Bench' in summary)
                        async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:await page.get_by_test_id('booking-submit').click()
                        response=await pending.value;receipt=parse(await response.body());request_body=response.request.post_data
                        check('opaque-'+label+'-pair-body',response.status==201 and parse(request_body)['table_ids']==[b,a])
                        async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:await page.get_by_test_id('booking-submit').click()
                        replay=await pending.value;check('opaque-'+label+'-retry',replay.status==200 and replay.request.post_data==request_body and replay.request.headers['idempotency-key']==response.request.headers['idempotency-key'])
                        await page.goto(release['urls']['target']+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(receipt['reference']);await page.get_by_test_id('lookup-submit').click();await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
                        check('opaque-'+label+'-lookup',await page.get_by_test_id('reservation-status').text_content()=='confirmed')
                        await page.screenshot(path=str(out/('opaque-'+label+'-lookup.png')),full_page=True)
                    finally:await context.close()
        except Exception as error:errors.append(dict(type=type(error).__name__,message=str(error)))
        finally:
            await browser.close();await http.dispose()
    for name,value in [('assertions',results),('trace',trace),('runner-errors',errors)]: (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    summary=dict(candidate=release['candidate'],case=case,assertions=len(results),failures=sum(not x['passed'] for x in results),runner_errors=errors,counts=counts,seconds=time.monotonic()-began,private_exports_saved=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));return bool(errors or summary['failures'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True)
    p.add_argument('--case',choices=['numeric','opaque','controls','upgrade','all'],default='all');p.add_argument('--execute',action='store_true')
    a=p.parse_args();release=validate_release(json.loads(Path(a.release).read_text()))
    if not a.execute:p.error('explicit execute requires later complete named package; no browser opened')
    return asyncio.run(execute(release,a.out,a.case))

if __name__=='__main__':raise SystemExit(main())
