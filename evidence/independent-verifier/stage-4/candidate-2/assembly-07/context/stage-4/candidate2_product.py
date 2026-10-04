"""Own current browser observations, full bound, privacy and genuine Stage3 bridge.

All faults transport actual HTTP responses. Private credentials/exports never saved.
"""
import argparse,asyncio,copy,hashlib,json,sys,time
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from stage4_probe import Client,fixture,closure,DAY,integer,same,raw
from candidate2_full_bound import construct,policy,PAIRS,saved
from stage4_oracle import booking,instant,seating_plan
from semantic_oracle import parse,encode,Number
from stage3_metrics import STYLE

class Review:
    def __init__(self,r,out):
        self.r=r;self.out=out;self.c=Client(r['urls']['target'],out/'api',r['candidate']);self.checks=[];self.traffic=[];self.forwards=[];self.images=[];self.started=time.monotonic()
    def check(self,name,condition,detail=None):
        self.checks.append(dict(requirement_id='TK4-product-'+name,passed=bool(condition),detail=detail,candidate=self.r['candidate']))
        if not condition:raise AssertionError(name)
    async def page(self,browser,who='m',width=375):
        context=await browser.new_context(viewport=dict(width=width,height=900));page=await context.new_page();page.set_default_timeout(7000)
        page.on('request',lambda q:self.traffic.append(dict(method=q.method,path=urlsplit(q.url).path,body_sha256=hashlib.sha256(q.post_data_buffer or b'').hexdigest())))
        await self.login(page,who);return context,page
    async def login(self,page,who):
        await page.goto(self.c.base+'/login');await page.get_by_test_id('login-email').fill(who+'@stage3.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click();await page.get_by_test_id('current-user').wait_for()
    async def manager(self,page,b):
        await page.locator('a[href="/manage"]').click();await page.get_by_test_id('replan-form').wait_for()
        await page.get_by_test_id('replan-table').select_option(b['table_id']);await page.get_by_test_id('replan-from').fill(b['from']);await page.get_by_test_id('replan-to').fill(b['to'])
    async def submit(self,page,testid,path,status=201):
        async with page.expect_response(lambda r:urlsplit(r.url).path==path and r.request.method=='POST') as pending:await page.get_by_test_id(testid).click()
        response=await pending.value;value=parse(await response.body());self.check(testid+'-actual-status',response.status==status,dict(status=response.status,expected=status));return value
    async def series(self,page,s,anchor):
        await page.goto(self.c.base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(anchor['reference']);await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('reservation-detail').wait_for();await page.get_by_test_id('series-lookup-id').fill(s['series_id']);await page.get_by_test_id('series-refresh').click();await page.get_by_test_id('series-occurrences').wait_for()
    async def shot(self,page,name):
        p=self.out/(name+'.png');await page.screenshot(path=str(p),full_page=True);metrics=await page.evaluate(STYLE)
        self.check(name+'-width',metrics['scroll']<=metrics['client'],dict(scroll=metrics['scroll'],client=metrics['client']))
        self.check(name+'-contrast',bool(metrics['text']) and all(t['ratio']>=t['minimum'] for t in metrics['text']),metrics)
        self.images.append(dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),width=page.viewport_size['width']))
    async def full(self,browser):
        c=self.c;construction=next(construct(i) for i in range(160) if 'error' not in construct(i)['expected']);f=fixture();r=f['restaurants'][0];r.update(slot_minutes=30,reservation_duration_minutes=90,cancellation_cutoff_minutes=0,combinable=copy.deepcopy(PAIRS))
        for t in r['tables']:t['capacity']=construction['original_capacities'][t['id']]
        c.setup(f);old=c.preview(construction['old_closure'],key='old');c.response('product-prior-closure',c.apply(old,key='old-apply'),201);issued=[]
        for item in construction['booking_constructions']:
            if item['name']=='late-a':c.response('product-later-policy',c.call('POST','/restaurants/r/policies',policy(r,construction['later_capacities']),token=c.tokens['m'],key='later'),201)
            issued.append(c.make([item['table']],DAY+'T'+item['clock'],item['party'],key=item['name']))
        c.response('product-latest-capacities',c.call('POST','/restaurants/r/policies',policy(r,{t:1 for t in 'abcdef'}),token=c.tokens['m'],key='latest'),201)
        models=[booking(b['reference'],b['table_ids'],instant(b['starts_at']),instant(b['ends_at']),{k:integer(v) for k,v in b['accepted_terms']['capacities'].items()},integer(b['party_size'])) for b in issued];expected=seating_plan(tuple('abcdef'),PAIRS,models,[construction['old_model']],construction['proposed_model']);before=c.public_state()
        context,page=await self.page(browser,width=1280);await self.manager(page,construction['proposed_closure']);plan=await self.submit(page,'replan-preview-submit','/restaurants/r/replans');await page.get_by_test_id('replan-proposal').wait_for()
        for k in ['assignments','moved_count','unused_seats']:self.check('full-bound-objective-'+k,same(plan[k],expected[k]))
        self.check('full-bound-count',len(plan['assignments'])==6);self.check('full-bound-readonly',same(before,c.public_state()));self.check('full-bound-proposed-only',await page.get_by_test_id('replan-unapplied').is_visible() and await page.get_by_test_id('replan-applied').count()==0)
        rows=await page.get_by_test_id('replan-assignments').locator('li').all_inner_texts();self.check('full-bound-human-reference-order',len(rows)==6 and all(a['reference'] in text and all('Hospitality '+t in text for t in a['table_ids']) for a,text in zip(plan['assignments'],rows)))
        self.check('full-bound-visible-objective',await page.get_by_test_id('replan-moved-count').inner_text()==encode(plan['moved_count']) and await page.get_by_test_id('replan-unused-seats').inner_text()==encode(plan['unused_seats']))
        await self.shot(page,'full-bound-proposal-desktop');applied=await self.submit(page,'replan-apply-submit','/restaurants/r/replans/'+plan['plan_id']+'/apply');await page.get_by_test_id('replan-applied').wait_for();self.check('full-bound-committed',integer(applied['restaurant_revision'])==integer(plan['restaurant_revision'])+1)
        fixed={issued[0]['reference'],issued[-1]['reference']}
        for old in issued:
            now=c.lookup(old['reference']);self.check('full-bound-identity-history',all(same(old[k],now[k]) for k in ['reservation_id','reference','party_size','starts_at','ends_at','accepted_terms','created_at']) and (same(old,now) if old['reference'] in fixed else True))
        await self.shot(page,'full-bound-applied-desktop');await context.close()
    async def members(self,browser):
        c=self.c
        for width in [375,1280]:
            c.seed();anchor=c.make();s=c.adopt(anchor,count=4);refs=[o['reference'] for o in s['occurrences']]
            c.response('product-moved-date-exception',c.call('PATCH','/reservations/'+refs[1],dict(starts_at_local='2035-06-13T18:00',party_size=2),token=c.tokens['u']),200);c.response('product-cancel-member',c.call('POST','/reservations/'+refs[2]+'/cancel',{},token=c.tokens['u']),200)
            p=c.preview(closure(start=DAY+'T17:00:00+00:00',end='2035-06-27T20:00:00+00:00'));c.response('product-series-repair',c.apply(p),201);before=c.current_series(s)
            context,page=await self.page(browser,'u',width);await self.series(page,s,anchor);await page.get_by_test_id('series-amend-from-index').fill('1');await page.get_by_test_id('series-amend-local-time').fill('19:00');await page.get_by_test_id('series-amend-local-time').press('Tab')
            for _ in range(6):
                if await page.get_by_test_id('series-amend-submit').evaluate('e=>document.activeElement===e'):break
                await page.keyboard.press('Tab')
            self.check('series-real-keyboard-focus',await page.get_by_test_id('series-amend-submit').evaluate('e=>document.activeElement===e && parseFloat(getComputedStyle(e).outlineWidth)>0'))
            async with page.expect_response(lambda r:r.request.method=='POST' and urlsplit(r.url).path=='/series/'+s['series_id']+'/amend') as pending:await page.keyboard.press('Enter')
            response=await pending.value;self.check('series-keyboard-actual-status',response.status==201);receipt=parse(await response.body());await page.get_by_test_id('series-amend-results').wait_for();text=await page.get_by_test_id('series-amend-results').inner_text();self.check('series-distinct-member-results',all(word in text for word in ['Before selected index','Permanent exception','Cancelled','Changed by this request']) and all(ref in text for ref in refs))
            now=c.current_series(s);self.check('series-once-and-stable',integer(now['revision'])==integer(before['revision'])+1 and [o['reference'] for o in now['occurrences']]==refs and [o['exception'] for o in now['occurrences']]==[False,True,False,False]);self.check('series-current-selection-original-date',now['occurrences'][3]['reservation']['starts_at_local']=='2035-06-25T19:00' and same(now['occurrences'][3]['reservation']['table_ids'],before['occurrences'][3]['reservation']['table_ids']) and now['occurrences'][1]['reservation']['starts_at_local']=='2035-06-13T18:00')
            await self.shot(page,'series-member-states-'+str(width));await page.get_by_test_id('series-amend-use-current').click();await page.get_by_test_id('series-amend-from-index').fill('0');await self.submit(page,'series-amend-submit','/series/'+s['series_id']+'/amend');await page.get_by_test_id('series-amend-results').wait_for();self.check('series-unchanged-distinct','Unchanged by this request' in await page.get_by_test_id('series-amend-results').inner_text())
            await page.get_by_test_id('series-amend-use-current').click();actual=c.current_series(s);c.response('product-external-amend',c.amend(actual,time='20:00',key='external'),201);before_bytes=c.export();await page.get_by_test_id('series-amend-local-time').fill('21:00');await self.submit(page,'series-amend-submit','/series/'+s['series_id']+'/amend',409);await page.get_by_test_id('series-amend-error').wait_for();self.check('series-stale-no-partial',before_bytes==c.export() and await page.get_by_test_id('series-amend-confirmation').count()==0);await self.shot(page,'series-stale-'+str(width))
            await page.get_by_test_id('series-refresh').click();await page.get_by_test_id('series-amend-use-current').click();await self.submit(page,'series-amend-submit','/series/'+s['series_id']+'/amend');await page.get_by_test_id('series-amend-confirmation').wait_for();await context.close()
    async def types(self,browser):
        c=self.c
        for lost in [False,True]:
            c.seed();anchor=c.make();context,page=await self.page(browser);b=closure();await self.manager(page,b);records=[]
            async def forward(route):
                q=route.request
                if q.method!='POST':await route.continue_();return
                body=parse(q.post_data_buffer);body['to']=None;response=await context.request.fetch(q.url,method='POST',headers=q.headers,data=raw(body));payload=await response.body();records.append(dict(status=response.status,body_sha256=hashlib.sha256(q.post_data_buffer).hexdigest(),key_sha256=hashlib.sha256(q.headers['idempotency-key'].encode()).hexdigest(),fault='Real forwarded to:null, not a native text input'))
                if lost and len(records)==1:await route.abort('failed')
                else:await route.fulfill(response=response,body=payload)
            await page.route('**/restaurants/r/replans',forward);before=c.export();await page.get_by_test_id('replan-preview-submit').click();await page.get_by_test_id('replan-uncertain' if lost else 'replan-error').wait_for()
            self.check('types-no-false-proposal',before==c.export() and await page.get_by_test_id('replan-proposal').count()==0 and await page.get_by_test_id('replan-applied').count()==0);self.check('types-inputs-retained',await page.get_by_test_id('replan-from').input_value()==b['from'] and await page.get_by_test_id('replan-to').input_value()==b['to']);await self.shot(page,'field-type-'+('lost' if lost else 'refused'))
            if lost:
                await page.get_by_test_id('replan-preview-submit').click();await page.get_by_test_id('replan-error').wait_for();self.check('types-same-retry',records[0]['body_sha256']==records[1]['body_sha256'] and records[0]['key_sha256']==records[1]['key_sha256'])
            self.check('types-actual400',all(x['status']==400 for x in records));self.forwards+=records;await page.unroute('**/restaurants/r/replans',forward)
            await page.get_by_test_id('replan-to').fill(DAY+'T20:30:00+00:00');await self.submit(page,'replan-preview-submit','/restaurants/r/replans');await page.get_by_test_id('replan-proposal').wait_for();await self.shot(page,'field-type-corrected-proposal-'+str(lost));await context.close()
        c.seed();c.make();context,page=await self.page(browser,'u');await page.locator('a[href="/manage"]').click();await page.get_by_test_id('manager-permission').wait_for();self.check('nonmanager-no-form',await page.get_by_test_id('replan-form').count()==0);await context.close()
        context,page=await self.page(browser,'m');await page.goto(c.base+'/lookup');ref=c.response('private-list',c.call('GET','/reservations',token=c.tokens['u']),200)['reservations'][0]['reference'];await page.get_by_test_id('lookup-reference-input').fill(ref);await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('reservation-error').wait_for();self.check('manager-private-refused',await page.get_by_test_id('reservation-detail').count()==0 and await page.get_by_test_id('reservation-history').count()==0);await context.close()
    async def numeric(self,browser):
        c=self.c;huge='9'*4301;f=fixture();f['restaurants'][0]['tables']=[dict(id='a',label='Window',capacity=2),dict(id='b',label='Garden',capacity=Number(huge))];f['restaurants'][0]['combinable']=[];c.setup(f);c.make(party=2);context,page=await self.page(browser);b=closure(start=DAY+'T18:00:00.000000000000000001+00:00');await self.manager(page,b);p=await self.submit(page,'replan-preview-submit','/restaurants/r/replans');await page.get_by_test_id('replan-proposal').wait_for();self.check('numeric-4301-visible',await page.get_by_test_id('replan-unused-seats').inner_text()==str(int(huge)-2));self.check('numeric-exact-fraction-visible',await page.get_by_test_id('replan-from').input_value()==b['from'] and b['from'] in await page.get_by_test_id('replan-proposal').inner_text());await self.shot(page,'numeric-exact-objective-mobile');await context.close()
    async def racesui(self,browser):
        c=self.c;c.seed();c.make();context,page=await self.page(browser);started=asyncio.Event();release=asyncio.Event();finished=asyncio.Event()
        async def delayed_detail(route):
            response=await context.request.fetch(route.request.url,headers=route.request.headers);body=await response.body();self.forwards.append(dict(kind='held-manager-detail',status=response.status,sha256=hashlib.sha256(body).hexdigest()));started.set();await release.wait();await route.fulfill(response=response,body=body);finished.set()
        await page.route('**/restaurants/r',delayed_detail);await page.locator('a[href="/manage"]').click();await asyncio.wait_for(started.wait(),7);await page.get_by_test_id('manager-restaurant-select').select_option('r2');await page.get_by_test_id('replan-form').wait_for();self.check('manager-B-current','Cedar Table' in await page.get_by_test_id('replan-table').inner_text());release.set();await asyncio.wait_for(finished.wait(),7);await page.wait_for_timeout(100);self.check('manager-A-cannot-restore','Cedar Table' in await page.get_by_test_id('replan-table').inner_text() and await page.get_by_test_id('manager-restaurant-select').input_value()=='r2');await page.unroute('**/restaurants/r',delayed_detail)
        await page.get_by_test_id('manager-restaurant-select').select_option('r');await page.get_by_test_id('replan-form').wait_for();b=closure();await page.get_by_test_id('replan-from').fill(b['from']);await page.get_by_test_id('replan-to').fill(b['to']);started=asyncio.Event();release=asyncio.Event();finished=asyncio.Event()
        async def delayed_preview(route):
            q=route.request;response=await context.request.fetch(q.url,method=q.method,headers=q.headers,data=q.post_data_buffer);body=await response.body();self.forwards.append(dict(kind='held-manager-preview',status=response.status,sha256=hashlib.sha256(body).hexdigest()));self.check('manager-held-real-preview',response.status==201);started.set();await release.wait();await route.fulfill(response=response,body=body);finished.set()
        await page.route('**/restaurants/r/replans',delayed_preview);await page.get_by_test_id('replan-preview-submit').click();await asyncio.wait_for(started.wait(),7);await page.get_by_test_id('manager-restaurant-select').select_option('r2');await page.get_by_test_id('replan-form').wait_for();release.set();await asyncio.wait_for(finished.wait(),7);await page.wait_for_timeout(100);self.check('manager-old-proposal-discarded',await page.get_by_test_id('replan-proposal').count()==0 and await page.get_by_test_id('manager-restaurant-select').input_value()=='r2');await context.close()
        c.seed();context,page=await self.page(browser,'u');await page.get_by_test_id('restaurant-select').select_option('r');await page.get_by_test_id('date-input').fill(DAY);await page.get_by_test_id('party-size-input').fill('1');await page.get_by_test_id('search-button').click();await page.get_by_test_id('slot-a-18:00').click();await page.get_by_test_id('booking-submit').click();await page.get_by_test_id('confirmation-current-tables').wait_for();ref=await page.get_by_test_id('confirmation-reference').inner_text();original=await page.get_by_test_id('confirmation-details').inner_text();started=asyncio.Event();release=asyncio.Event();finished=asyncio.Event();armed={'yes':True}
        async def delayed_current(route):
            if not armed['yes']:await route.continue_();return
            armed['yes']=False;q=route.request;response=await context.request.fetch(q.url,headers=q.headers);body=await response.body();self.forwards.append(dict(kind='held-original-current-read',status=response.status,sha256=hashlib.sha256(body).hexdigest()));started.set();await release.wait();await route.fulfill(response=response,body=body);finished.set()
        await page.route('**/reservations/'+ref,delayed_current);await page.get_by_test_id('confirmation-refresh').click();await asyncio.wait_for(started.wait(),7);plan=c.preview();applied=c.response('product-current-apply',c.apply(plan),201);tables=applied['reservations'][0]['table_ids'];await page.get_by_test_id('confirmation-refresh').click();await page.get_by_test_id('confirmation-current-tables').filter(has_text='Hospitality '+tables[0]).wait_for();release.set();await asyncio.wait_for(finished.wait(),7);await page.wait_for_timeout(100);current_text=await page.get_by_test_id('confirmation-current-tables').inner_text();self.check('current-read-A-cannot-restore',all('Hospitality '+t in current_text for t in tables));self.check('original-confirmation-immutable',await page.get_by_test_id('confirmation-details').inner_text()==original and await page.get_by_test_id('confirmation-reference').inner_text()==ref);await self.shot(page,'current-assignment-original-confirmation-mobile');await page.locator('[data-open-reference]').click();await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('reservation-detail').wait_for();self.check('lookup-applied-history-authoritative','reassigned' in (await page.get_by_test_id('reservation-detail').inner_text()).lower() or plan['plan_id'] in await page.get_by_test_id('reservation-detail').inner_text());await self.shot(page,'current-lookup-reassigned-mobile');await context.close()
    async def bridge(self,browser):
        c=self.c;source=self.r['urls']['accepted-s3'];c.setup(fixture(),url=source);route_target={'url':source};records=[];original=None
        context=await browser.new_context(viewport=dict(width=375,height=900));page=await context.new_page();page.set_default_timeout(7000);page.on('request',lambda q:self.traffic.append(dict(method=q.method,path=urlsplit(q.url).path,body_sha256=hashlib.sha256(q.post_data_buffer or b'').hexdigest())))
        async def forward(route):
            nonlocal original
            q=route.request;p=urlsplit(q.url)
            if p.path in ['/','/login','/lookup','/signup','/manage'] or p.path.startswith('/assets/') or p.path.endswith(('.js','.css','.ico')):await route.continue_();return
            response=await context.request.fetch(route_target['url']+p.path+('?' + p.query if p.query else ''),method=q.method,headers=q.headers,data=q.post_data_buffer);payload=await response.body();record=dict(path=p.path,method=q.method,status=response.status,source=route_target['url'],bytes=len(payload),response_sha256=hashlib.sha256(payload).hexdigest(),body_sha256=hashlib.sha256(q.post_data_buffer or b'').hexdigest(),key_sha256=hashlib.sha256(q.headers.get('idempotency-key','').encode()).hexdigest());records.append(record)
            if p.path=='/series' and q.method=='POST' and original is None:
                original=parse(payload);self.check('bridge-source-adoption201',response.status==201);await route.abort('failed')
            else:await route.fulfill(response=response,body=payload)
        await page.route('**/*',forward);await self.login(page,'u');await page.evaluate('window.independentDocumentIdentity="retained-document"');await page.get_by_test_id('restaurant-select').select_option('r');await page.get_by_test_id('date-input').fill(DAY);await page.get_by_test_id('party-size-input').fill('1');await page.get_by_test_id('search-button').click();await page.get_by_test_id('slot-a-18:00').click();await page.get_by_test_id('booking-submit').click();await page.get_by_test_id('confirmation-reference').wait_for();ref=await page.get_by_test_id('confirmation-reference').inner_text();await page.locator('[data-open-reference]').click();await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('series-count').fill('4');await page.get_by_test_id('series-submit').click();await page.get_by_test_id('series-uncertain').wait_for();self.check('bridge-no-false-agreement',await page.get_by_test_id('series-confirmation').count()==0)
        refs=[o['reference'] for o in original['occurrences']];c.response('bridge-source-exception',c.call('PATCH','/reservations/'+refs[1],dict(party_size=2),token=c.tokens['u'],url=source),200);c.response('bridge-source-cancel',c.call('POST','/reservations/'+refs[2]+'/cancel',{},token=c.tokens['u'],url=source),200);body=c.export(url=source);c.response('bridge-unchanged-import',c.transfer(source,c.base,body),204);route_target['url']=c.base;await page.get_by_test_id('series-submit').click();await page.get_by_test_id('series-confirmation').wait_for();await page.get_by_test_id('series-occurrences').wait_for();self.check('bridge-retained-document-user',await page.evaluate('window.independentDocumentIdentity')=='retained-document' and 'Diner' in await page.get_by_test_id('current-user').inner_text());list_text=await page.get_by_test_id('series-occurrences').inner_text();self.check('bridge-populated-list',all(r in list_text for r in refs) and 'cancelled' in list_text and 'permanent exception' in list_text)
        adoption=[r for r in records if r['path']=='/series' and r['method']=='POST'];self.check('bridge-original-body-key-receipt',len(adoption)==2 and [r['status'] for r in adoption]==[201,200] and adoption[0]['body_sha256']==adoption[1]['body_sha256'] and adoption[0]['key_sha256']==adoption[1]['key_sha256'] and adoption[0]['response_sha256']==adoption[1]['response_sha256']);await self.shot(page,'genuine-stage3-populated-retry-mobile')
        await page.get_by_test_id('series-amend-local-time').fill('19:00');await self.submit(page,'series-amend-submit','/series/'+original['series_id']+'/amend');await page.get_by_test_id('series-amend-confirmation').wait_for();s=c.current_series(original);c.series_ids=[s['series_id']];p=c.preview(closure(start=DAY+'T17:00:00+00:00',end='2035-06-27T21:00:00+00:00'));c.response('bridge-imported-series-repair',c.apply(p),201);await page.get_by_test_id('series-refresh').click();await page.get_by_test_id('series-occurrences').wait_for();now=c.current_series(s);self.check('bridge-actual-amend-repair',now['occurrences'][1]['exception'] and now['occurrences'][2]['reservation']['status']=='cancelled' and [o['reference'] for o in now['occurrences']]==refs);await self.shot(page,'genuine-stage3-after-repair-mobile');self.forwards+=records;await context.close()

async def run(r,out,family):
    from playwright.async_api import async_playwright
    out.mkdir(parents=True,exist_ok=False);review=Review(r,out);error=None
    try:
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True);await getattr(review,family)(browser);await browser.close()
    except BaseException as exc:error=repr(exc);raise
    finally:
        review.c.save(error)
        for name,value in [('assertions.json',review.checks),('traffic.json',review.traffic),('forwarding.json',review.forwards),('screenshots.json',review.images)]: (out/name).write_text(json.dumps(value,indent=2)+'\n')
        (out/'executed-source.py').write_bytes(Path(__file__).read_bytes());(out/'summary.json').write_text(json.dumps(dict(candidate=r['candidate'],family=family,complete=error is None,error=error,assertions=len(review.checks),failed=sum(not x['passed'] for x in review.checks),direct_api_requests=review.c.count,direct_api_assertions=len(review.c.assertions),browser_requests=len(review.traffic),forwarding_operations=len(review.forwards),screenshots=len(review.images),seconds=time.monotonic()-review.started,private_exports_saved=False),indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);p.add_argument('--family',choices=['full','members','types','numeric','bridge','racesui'],required=True);a=p.parse_args();r=validate(json.loads(Path(a.release).read_text()));asyncio.run(run(r,Path(a.out),a.family))
if __name__=='__main__':main()
