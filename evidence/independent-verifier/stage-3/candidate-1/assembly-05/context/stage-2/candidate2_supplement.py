"""Independent final wire/browser and actual prepared reference-trace supplements."""
import argparse, asyncio, copy, datetime as dt, json, re, sys, time
from pathlib import Path
from urllib.parse import quote, urlsplit, parse_qs
sys.set_int_max_str_digits(0)
from reconstruction_probe import Wire, fixture, encoded, parse, same, Number, sha, DAY, validate_release
from reconstruction_oracle import seeded_trace
PARTIAL={}

def oracle(release,out):
    w=Wire(out);model=seeded_trace();f=fixture();r=f['restaurants'][0]
    r['tables']=[dict(id=k,label='Seat '+k,capacity=v) for k,v in model['tables'].items()]
    r['combinable']=model['pairs'];base=release['urls']['target'];token=w.setup(base,f)
    refs={};identities={};observed=[]
    PARTIAL.update(results=w.assertions,trace=w.trace,detail=dict(seed=model['seed'],operations=observed),counts=dict(requests=0))
    def local(m):return DAY+'T'+f'{18+m//60:02}:{m%60:02}'
    def changes(op):return dict(table_ids=op['table_ids'],party_size=op['party_size'],starts_at_local=local(op['start']))
    for entry in model['operations']:
        op=entry['operation'];kind=op['kind'];i=entry['index'];raw=None;key=None
        if kind=='create':
            raw=encoded(dict(restaurant_id='r',**changes(op['record'])));method,path='POST','/reservations';key='oracle-'+str(i)
        elif kind=='patch':method,path='PATCH','/reservations/'+refs[op['reference']];raw=encoded(changes(op))
        elif kind=='cancel':method,path='POST','/reservations/'+refs[op['reference']]+'/cancel'
        elif kind=='moves':
            method,path='POST','/reservation-moves';key='oracle-'+str(i)
            raw=encoded(dict(moves=[dict(reference=refs[x['reference']],**changes(x)) for x in op['moves']]))
        elif kind=='availability':
            method,path='GET','/availability?restaurant_id=r&date='+DAY+'&party_size='+str(op['party_size'])
        else:method,path='GET','/reservations'
        status,value,_=w.call(base,method,path,raw,token,key);expected=entry['expected']
        w.check('prepared-oracle-status-'+str(i),status==expected['status'])
        if expected.get('code'):w.check('prepared-oracle-code-'+str(i),value['error']['code']==expected['code'])
        if kind=='create' and status==201:refs[op['record']['reference']]=value['reference']
        if kind=='availability':
            slot=next(x for x in value['slots'] if x['starts_at_local']==local(op['start']))
            w.check('prepared-oracle-options-'+str(i),same(slot['available_options'],expected['options']))
        status,current,_=w.call(base,'GET','/reservations',token=token)
        inverse={v:k for k,v in refs.items()};normalized=[]
        for item in current['reservations']:
            ref=inverse[item['reference']]
            immutable={k:item[k] for k in ['reference','reservation_id','restaurant_id','created_at']}
            if ref in identities:w.check('prepared-oracle-identity-'+str(i)+'-'+ref,same(identities[ref],immutable))
            else:identities[ref]=immutable
            t=dt.datetime.fromisoformat(item['starts_at_local']);minutes=(t.hour-18)*60+t.minute
            record=next(x for x in entry['resulting_records'] if x['reference']==ref)
            normalized.append(dict(reference=ref,owner='A',table_ids=item['table_ids'],party_size=item['party_size'],start=minutes,end=minutes+90,status=item['status'],created_at=record['created_at']))
        w.check('prepared-oracle-state-'+str(i),status==200 and same(sorted(normalized,key=lambda x:x['reference']),sorted(entry['resulting_records'],key=lambda x:x['reference'])))
        observed.append(dict(index=i,operation=op,expected=expected,observed_status=status if kind=='read' else w.trace[-2]['status'],resulting_records=normalized))
    # New batch rules are exercised against fresh confirmed current state, independently of legacy bodies.
    token=w.setup(base);raw=encoded(dict(restaurant_id='r',table_id='a',starts_at_local=DAY+'T18:00',party_size=2))
    _,receipt,_=w.call(base,'POST','/reservations',raw,token,'batch-fields')
    bad=encoded(dict(moves=[dict(reference=receipt['reference'],table_id='a',table_ids=['a'])]))
    status,value,_=w.call(base,'POST','/reservation-moves',bad,token,'failed-batch-fields')
    w.check('new-batch-both-fields',status==422 and value['error']['code']=='validation_failed')
    status,value,_=w.call(base,'POST','/reservation-moves',encoded(dict(moves=[dict(reference=receipt['reference'],table_ids=['a'])])),token,'failed-batch-fields')
    w.check('new-batch-both-fields-key-reusable',status==201 and value['reservations'][0]['reference']==receipt['reference'])
    return w.assertions,w.trace,dict(seed=model['seed'],operations=observed,scope='actual current-candidate HTTP outcomes and full resulting records; no service helper used',private_exports_saved=False),dict(requests=w.request_count)

def coverage_http(release,out):
    w=Wire(out);PARTIAL.update(results=w.assertions,trace=w.trace,detail={},counts={})
    source=release['urls']['exact-s1'];target=release['urls']['target'];token=w.setup(source)
    raw=encoded(dict(restaurant_id='r',table_id='a',table_ids={'ignored':True},party_size=2,starts_at_local=DAY+'T18:00'))
    status,receipt,_=w.call(source,'POST','/reservations',raw,token,'exact-record');w.check('record-source-create',status==201)
    moves=encoded(dict(moves=[dict(reference=receipt['reference'],party_size=3,table_ids='ignored by Stage1')]))
    status,moved,_=w.call(source,'POST','/reservation-moves',moves,token,'exact-record-moves');w.check('record-source-moves',status==201)
    status,before,_=w.call(source,'GET','/reservations/'+receipt['reference'],token=token)
    snapshot=w.export(source);w.check('record-import',w.transfer(source,target,snapshot)==204)
    status,after,_=w.call(target,'GET','/reservations/'+receipt['reference'],token=token)
    for field in ['reservation_id','reference','created_at','starts_at','ends_at','status']:
        w.check('record-'+field,status==200 and same(before[field],after[field]))
    other_status,other,_=w.call(target,'POST','/auth/signup',encoded(dict(email='record-owner@probe.invalid',password='independent-pass',display_name='Other Diner')))
    outsider,_,_=w.call(target,'GET','/reservations/'+receipt['reference'],token=other['token'])
    w.check('record-user_id',other_status==201 and outsider==404 and after['reference']==before['reference'])
    w.check('record-original-create',w.replay(target,'/reservations',raw,token,'exact-record',receipt))
    w.check('record-original-moves',w.replay(target,'/reservation-moves',moves,token,'exact-record-moves',moved))
    f=fixture();f['reservations']=[dict(id='old',reference='OLD001',user_id='u',restaurant_id='r',table_ids=['b','a'],party_size=2,starts_at_local='2000-01-03T18:00'),dict(id='next',reference='NEXT01',user_id='u',restaurant_id='r',table_id='c',party_size=2,starts_at_local=DAY+'T18:00')]
    token=w.setup(target,f);before=w.export(target)
    sequences=[([dict(reference='NEXT01',party_size=0),dict(reference='OLD001',party_size=0)],422,'validation_failed'),([dict(reference='OLD001',party_size=0),dict(reference='NEXT01',party_size=0)],409,'cutoff_passed'),([dict(reference='NEXT01'),dict(reference='OLD001',party_size=0)],409,'cutoff_passed')]
    for i,(items,expected,code) in enumerate(sequences):
        status,value,_=w.call(target,'POST','/reservation-moves',encoded(dict(moves=items)),token,'order-'+str(i))
        w.check('pair-cutoff-order-'+str(i),status==expected and value['error']['code']==code)
        w.check('pair-cutoff-rollback-'+str(i),w.export(target)==before)
        status,_,_=w.call(target,'POST','/reservation-moves',encoded(dict(moves=[dict(reference='NEXT01')])),token,'order-'+str(i));w.check('pair-cutoff-failed-key-'+str(i),status==201)
        before=w.export(target)
    token=w.setup(target);status,record,_=w.call(target,'POST','/reservations',encoded(dict(restaurant_id='r',table_ids=['a','b'],party_size=2,starts_at_local=DAY+'T18:00')),token,'reverse')
    w.check('reverse-noop-create',status==201)
    for name,payload in [('reverse',dict(table_ids=['a','b'])),('empty',{})]:
        status,changed,_=w.call(target,'PATCH','/reservations/'+record['reference'],encoded(payload),token)
        w.check('noop-all-values-'+name,status==200 and same(record,changed))
    return w.assertions,w.trace,dict(scope='actual accepted Stage1 record invariants and source meanings, pair current-start cutoff/input order/rollback/failed key and reverse/empty no-op values'),dict(requests=w.request_count)

async def overflow_checks(release,out):
    from playwright.async_api import async_playwright,expect
    results=[];trace=[];counts=dict(direct=0,browser=0);PARTIAL.update(results=results,trace=trace,detail={},counts=counts);base=release['urls']['target']
    def check(key,value):
        results.append(dict(requirement_id='TK2-'+key,passed=bool(value)))
        if not value:raise AssertionError(key)
    async with async_playwright() as runtime:
        http=await runtime.request.new_context();browser=await runtime.chromium.launch(headless=True)
        for seating in ['single','pair']:
            digits='1'+'0'*399+'1';n=int(digits);f=fixture();caps=[n,1,1] if seating=='single' else [n//2,n-n//2,1]
            for table,capacity in zip(f['restaurants'][0]['tables'],caps):table['capacity']=capacity
            response=await http.post(base+'/_test/reset',data=encoded(f),headers={'content-type':'application/json; charset=utf-8'});counts['direct']+=1
            assert response.status==204
            context=await browser.new_context(viewport={'width':375,'height':900});page=await context.new_page();page.set_default_timeout(5000)
            def observe(request):
                counts['browser']+=1;trace.append(dict(event='browser-request',path=urlsplit(request.url).path,query=urlsplit(request.url).query,body_sha256=sha((request.post_data or '').encode()),key_sha256=sha(request.headers.get('idempotency-key','').encode())))
            page.on('request',observe);prefix='integer-'+seating+'-overflow-'
            try:
                await page.goto(base+'/login');await page.get_by_test_id('login-email').fill('reconstruct@probe.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click();await expect(page.get_by_test_id('current-user')).to_contain_text('Independent Diner')
                await page.goto(base+'/');await page.get_by_test_id('restaurant-select').select_option('r');await page.get_by_test_id('date-input').fill(DAY);await page.get_by_test_id('party-size-input').fill(digits)
                async with page.expect_request(lambda r:urlsplit(r.url).path=='/availability') as pending:await page.get_by_test_id('search-button').click()
                request=await pending.value;check(prefix+'query',parse_qs(urlsplit(request.url).query)['party_size']==[digits])
                cell=page.get_by_test_id('slot-'+('a' if seating=='single' else 'b+a')+'-18:00');await expect(cell).to_be_visible();check(prefix+'grid',await cell.get_attribute('data-available')=='true');await cell.click();check(prefix+'prefill',await page.get_by_test_id('booking-party-size').input_value()==digits)
                async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:await page.get_by_test_id('booking-submit').click()
                response=await pending.value;receipt=parse(await response.body());body=response.request.post_data;header=response.request.headers
                check(prefix+'body',same(parse(body)['party_size'],n) and re.search(r'"party_size"\s*:\s*'+digits+r'\s*[,}]',body) is not None)
                await expect(page.get_by_test_id('confirmation')).to_be_visible();check(prefix+'success',response.status==201 and await page.get_by_test_id('confirmation-reference').text_content()==receipt['reference'])
                async with page.expect_response(lambda r:urlsplit(r.url).path=='/reservations' and r.request.method=='POST') as pending:await page.get_by_test_id('booking-submit').click()
                retry=await pending.value;replay=parse(await retry.body());check(prefix+'repeat-identity',retry.request.post_data==body and retry.request.headers['idempotency-key']==header['idempotency-key']);check(prefix+'repeat-reference',retry.status==200 and same(replay,receipt))
                response=await http.get(base+'/reservations',headers={'authorization':header['authorization']});counts['direct']+=1;records=parse(await response.body())['reservations'];check(prefix+'one-record',response.status==200 and len(records)==1 and records[0]['reference']==receipt['reference']);check(prefix+'stored',same(records[0]['party_size'],n))
                trace.append(dict(event='actual-current-owned-list',seating=seating,status=response.status,count=len(records),reference=receipt['reference'],party_digits=len(digits),response_sha256=sha(await response.body())))
                await page.screenshot(path=str(out/(seating+'-confirmed.png')),full_page=True)
            finally:await context.close()
        await browser.close();await http.dispose()
    return results,trace,dict(scope='fresh actual 401-digit singleton/pair search/prefill/body/replay/stored-list count obligations'),counts

async def browser_checks(release,out):
    from playwright.async_api import async_playwright,expect
    results=[];trace=[];counts=dict(direct=0,browser=0);base=release['urls']['target']
    PARTIAL.update(results=results,trace=trace,detail=dict(incomplete=True),counts=counts)
    def check(key,condition):
        results.append(dict(requirement_id='TK2R-'+key,passed=bool(condition)))
        if not condition:raise AssertionError(key)
    async with async_playwright() as runtime:
        http=await runtime.request.new_context();browser=await runtime.chromium.launch(headless=True)
        async def call(method,path,raw=None):
            response=await http.fetch(base+path,method=method,data=raw,headers={'content-type':'application/json; charset=utf-8'},timeout=10000 if path.startswith('/_test/') else 5000)
            payload=await response.body();counts['direct']+=1
            trace.append(dict(event='direct-http',method=method,path=path,status=response.status,request_bytes=len(raw or b''),request_sha256=sha(raw or b''),response_bytes=len(payload),response_sha256=sha(payload)))
            return response.status,parse(payload) if payload else None,payload
        forms=['9007199254740993.0','9007199254740993e0','90071992547409930e-1','9.007199254740993E+15','0.9007199254740993e16']
        try:
            for index,spelling in enumerate(forms):
                rid='r?&#=é汉𝄞"';a='a/+%2F"';b='b汉?';c='c&'
                f=fixture((rid,a,b,c));f['restaurants'][0]['tables'][0]['capacity']=Number(spelling)
                f['restaurants'][0]['tables'][1]['capacity']=1
                status,_,_=await call('POST','/_test/reset',encoded(f));check('five-wire-'+str(index)+'-fixture',status==204)
                status,detail,payload=await call('GET','/restaurants/'+quote(rid,safe=''))
                actual=detail['tables'][0]['capacity'];check('five-wire-'+str(index)+'-actual-token',status==200 and isinstance(actual,Number) and actual.raw==spelling and same(actual,9007199254740993))
                context=await browser.new_context(viewport={'width':375,'height':900},timezone_id='Pacific/Honolulu');page=await context.new_page();page.set_default_timeout(5000)
                def observe(req):
                    counts['browser']+=1;trace.append(dict(event='browser-request',method=req.method,path=urlsplit(req.url).path,query=urlsplit(req.url).query,body_sha256=sha((req.post_data or '').encode()),key_sha256=sha(req.headers.get('idempotency-key','').encode())))
                page.on('request',observe)
                try:
                    await page.goto(base+'/login');await page.get_by_test_id('login-email').fill('reconstruct@probe.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click()
                    await expect(page.get_by_test_id('current-user')).to_contain_text('Independent Diner')
                    await page.goto(base+'/');await page.get_by_test_id('restaurant-select').select_option(rid);await page.get_by_test_id('date-input').fill(DAY)
                    field=page.get_by_test_id('party-size-input');digits='9007199254740994';await field.fill(digits)
                    await field.press('ArrowUp');check('search-step-'+str(index),await field.input_value()==str(int(digits)+1));await field.press('ArrowDown');check('search-step-back-'+str(index),await field.input_value()==digits)
                    await field.fill('1');await field.press('ArrowDown');check('search-minimum-'+str(index),await field.input_value()=='1');await field.fill(digits)
                    check('search-semantic-'+str(index),await field.get_attribute('role')=='spinbutton' and await field.get_attribute('inputmode')=='numeric')
                    async with page.expect_request(lambda req:urlsplit(req.url).path=='/availability') as pending:await page.get_by_test_id('search-button').click()
                    request=await pending.value;check('five-wire-'+str(index)+'-query',parse_qs(urlsplit(request.url).query)=={'restaurant_id':[rid],'date':[DAY],'party_size':[digits]})
                    cell=page.get_by_test_id('slot-'+b+'+'+a+'-18:00');await expect(cell).to_be_visible();check('five-wire-'+str(index)+'-pair-capacity',digits in await cell.text_content());await cell.click()
                    check('five-wire-'+str(index)+'-prefill',await page.get_by_test_id('booking-party-size').input_value()==digits)
                    async with page.expect_response(lambda response:urlsplit(response.url).path=='/reservations' and response.request.method=='POST') as pending:await page.get_by_test_id('booking-submit').click()
                    response=await pending.value;receipt=parse(await response.body());body=parse(response.request.post_data)
                    await expect(page.get_by_test_id('confirmation')).to_be_visible()
                    check('five-wire-'+str(index)+'-body',response.status==201 and body['restaurant_id']==rid and body['table_ids']==[b,a] and same(body['party_size'],int(digits)) and re.search(r'"party_size"\s*:\s*'+digits+r'\s*[,}]',response.request.post_data) is not None)
                    labels=await page.get_by_test_id('confirmation-tables').text_content()
                    check('five-wire-'+str(index)+'-labels',all(label in labels for label in ['Window Alcove','Garden Bench']))
                    async with page.expect_response(lambda response:urlsplit(response.url).path=='/reservations' and response.request.method=='POST') as pending:await page.get_by_test_id('booking-submit').click()
                    retry=await pending.value;check('five-wire-'+str(index)+'-retry',retry.status==200 and retry.request.post_data==response.request.post_data and retry.request.headers['idempotency-key']==response.request.headers['idempotency-key'] and same(parse(await retry.body()),receipt))
                    await page.goto(base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(receipt['reference']);await page.get_by_test_id('lookup-submit').click();await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
                    check('five-wire-'+str(index)+'-lookup',digits in await page.get_by_test_id('reservation-detail').text_content() and await page.get_by_test_id('reservation-status').inner_text()=='confirmed')
                    await page.screenshot(path=str(out/('five-wire-'+str(index)+'-lookup.png')),full_page=True)
                    await page.get_by_test_id('reservation-cancel-button').click();await expect(page.get_by_test_id('reservation-status')).to_have_text('cancelled')
                    check('five-wire-'+str(index)+'-opaque-cancel',await page.get_by_test_id('reservation-status').inner_text()=='cancelled' and await page.get_by_test_id('reservation-cancel-button').count()==0)
                    width=await page.evaluate('({scroll:document.documentElement.scrollWidth,width:innerWidth})');check('five-wire-'+str(index)+'-mobile',width['scroll']<=width['width'])
                    trace.append(dict(event='actual-integral-wire-token',spelling=spelling,actual=actual.raw,exact_value='9007199254740993',pair_sum=digits,restaurant_id=rid,table_ids=[b,a],response_sha256=sha(payload),response_not_modified=True))
                    await page.screenshot(path=str(out/('five-wire-'+str(index)+'-cancelled.png')),full_page=True)
                finally:await context.close()
        finally:await browser.close();await http.dispose()
    return results,trace,dict(scope='five actual integral JSON capacity spellings, exact pair sums and actual quoted URI/Unicode numeric control/query/body/retry/lookup/cancel interactions'),counts

def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);p.add_argument('--case',choices=['oracle','browser','coverage','overflow'],required=True);a=p.parse_args()
    release=validate_release(json.loads(Path(a.release).read_text()));out=Path(a.out);out.mkdir(parents=True,exist_ok=False);start=time.monotonic();errors=[]
    try:
        results,trace,detail,counts=(oracle(release,out) if a.case=='oracle' else coverage_http(release,out) if a.case=='coverage' else asyncio.run(overflow_checks(release,out)) if a.case=='overflow' else asyncio.run(browser_checks(release,out)))
    except Exception as error:
        # An incomplete family is not promoted; the driver preserves this exit/log and source.
        errors.append(dict(type=type(error).__name__,message=str(error),classification='recorded-expectation' if isinstance(error,AssertionError) else 'runner-exception'))
        results=PARTIAL.get('results',[]);trace=PARTIAL.get('trace',[]);detail=PARTIAL.get('detail',{});detail['incomplete']=True;counts=PARTIAL.get('counts',{})
        if a.case=='oracle':counts['requests']=sum('index' in x for x in trace)
    # Exact public oracle leaves retain their actual numeric token in evidence metadata.
    def exact_leaf(value):
        if isinstance(value,Number):return {'actual_json_number_token':value.raw}
        raise TypeError(type(value).__name__)
    for name,value in [('assertions',results),('trace',trace),('detail',detail)]: (out/(name+'.json')).write_text(json.dumps(value,indent=2,ensure_ascii=False,default=exact_leaf)+'\n')
    summary=dict(candidate=release['candidate'],case=a.case,assertions=len(results),failures=sum(not x['passed'] for x in results),errors=errors,counts=counts,seconds=time.monotonic()-start)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary));raise SystemExit(bool(errors) or summary['failures']>0)
if __name__=='__main__':main()
