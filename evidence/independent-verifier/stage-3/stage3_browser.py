"""Prepared real-browser Stage 3 protocol; no candidate is currently released.

Stage 3 specifies no new test IDs. Later selector bindings must name real product
elements on the submitted page. A missing binding blocks this protocol, rather
than fabricating a DOM or treating a skipped interaction as a pass.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from stage3_probe import Client,fixture,policy,create_body,raw,validate_release,DAY
from stage3_requirements import S1,S2

SELECTORS=('accepted_terms','history','series_count','series_interval','series_submit','series_result','series_error')
def validate_selectors(release):
    bindings=release.get('browser_selectors',{})
    for key in SELECTORS:
        if not isinstance(bindings.get(key),str) or not bindings[key].strip():raise ValueError('real candidate UI selector required: '+key)
    if release.get('selectors_observed_on_candidate') is not True:raise ValueError('selector binding requires observed candidate UI')
    return bindings

async def run(release,out):
    from playwright.async_api import async_playwright
    selectors=validate_selectors(release);base=release['urls']['target'];c=Client(base,out/'api',release['candidate'])
    observations=[];requests=[];screenshots=[];began=time.monotonic();error=None
    def check(name,condition,detail=None):
        observations.append(dict(requirement_id='TK3-browser-'+name,passed=bool(condition),detail=detail))
        if not condition:raise AssertionError(name)
    async def login(page):
        await page.goto(base+'/login')
        await page.get_by_test_id('login-email').fill('u@stage3.invalid');await page.get_by_test_id('login-password').fill('independent-pass')
        await page.get_by_test_id('login-submit').click();await page.get_by_test_id('current-user').wait_for()
        check('inherited-grid','Diner' in await page.get_by_test_id('current-user').text_content())
    async def lookup(page,ref):
        await page.goto(base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(ref)
        await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('reservation-detail').wait_for()
    async def book(page,seats=('a',),clock='18:00'):
        await page.goto(base+'/');await page.get_by_test_id('restaurant-select').select_option('r')
        await page.get_by_test_id('date-input').fill(DAY);await page.get_by_test_id('party-size-input').fill('2')
        await page.get_by_test_id('search-button').click();await page.get_by_test_id('availability-grid').wait_for()
        await page.get_by_test_id('slot-'+'+'.join(seats)+'-'+clock).click();await page.get_by_test_id('booking-form').wait_for()
    async def capture(page,name,width):
        path=out/(name+'-'+str(width)+'.png');await page.screenshot(path=str(path),full_page=True)
        screenshots.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),width=width))
        dimensions=await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
        check(name+'-'+str(width)+'-no-page-scroll',dimensions['scroll']<=dimensions['width'],dimensions)
        await page.keyboard.press('Tab')
        focus=await page.evaluate('({tag:document.activeElement.tagName,outline:getComputedStyle(document.activeElement).outlineStyle,width:getComputedStyle(document.activeElement).outlineWidth})')
        observations.append(dict(requirement_id='TK3-browser-'+name+'-'+str(width)+'-keyboard-focus',observed=focus,verdict='unverified-visual-review-required'))
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(headless=True)
            for width in [375,1280]:
                c.setup();created=c.create();ref=created['reference']
                c.response('policies-manager-allowed',c.call('POST','/restaurants/r/policies',policy(),token=c.tokens['m'],key='new'),201)
                c.response('terms-amend-new-terms',c.call('PATCH','/reservations/'+ref,dict(party_size=2,table_ids=['b']),token=c.tokens['u']),200)
                context=await browser.new_context(viewport={'width':width,'height':900},timezone_id='Pacific/Honolulu')
                page=await context.new_page()
                page.set_default_timeout(5000)
                page.on('request',lambda request:requests.append(dict(method=request.method,url=request.url,bytes=len((request.post_data or '').encode()),body_sha256=hashlib.sha256((request.post_data or '').encode()).hexdigest())))
                await login(page);await lookup(page,ref)
                terms_node=page.locator(selectors['accepted_terms']);history_node=page.locator(selectors['history'])
                await terms_node.wait_for();await history_node.wait_for()
                await terms_node.locator('summary').click()
                for summary in await history_node.locator('summary').all():await summary.click()
                real=c.lookup(ref);history=c.history(ref)
                term_text=await terms_node.inner_text();history_text=await history_node.inner_text()
                check('accepted-terms',bool(term_text.strip()))
                check('historic-changes',bool(history_text.strip()) and len(history['entries'])==2)
                observations.append(dict(event='term-history-text',reference=ref,terms_text=term_text,history_text=history_text,
                    current_terms_sha256=hashlib.sha256(raw(real['accepted_terms'])).hexdigest(),history_sha256=hashlib.sha256(raw(history)).hexdigest(),
                    verdict='unverified-content-review-required'))
                await capture(page,'terms-history',width)
                await page.locator(selectors['series_count']).fill('3');await page.locator(selectors['series_interval']).fill('1')
                async with page.expect_response(lambda response:urlsplit(response.url).path=='/series' and response.request.method=='POST') as response_info:
                    await page.locator(selectors['series_submit']).click()
                series_response=await response_info.value
                if series_response.status!=201:raise AssertionError('real adoption did not succeed')
                from stage3_probe import parse
                actual_series=parse(await series_response.body())
                await page.locator(selectors['series_result']).wait_for()
                text=await page.locator(selectors['series_result']).inner_text()
                sid=actual_series['series_id']
                c.series_ids=[sid];series=c.response('series-get-current',c.call('GET','/series/'+sid,token=c.tokens['u']),200)
                check('series-occurrences',all(member['reference'] in text for member in series['occurrences']))
                await capture(page,'series-list',width)
                member=series['occurrences'][1]['reference'];other=series['occurrences'][2]['reference']
                c.response('series-patch-exception',c.call('PATCH','/reservations/'+member,dict(party_size=3),token=c.tokens['u']),200)
                c.response('series-cancel-no-exception',c.call('POST','/reservations/'+other+'/cancel',{},token=c.tokens['u']),200)
                # The same document retains the genuine agreement identity.
                # Explicitly refresh current states after the rival API writes.
                await page.get_by_test_id('series-refresh').click()
                await page.get_by_test_id('series-revision').filter(has_text='3').wait_for()
                await page.locator(selectors['series_result']).wait_for()
                text=await page.locator(selectors['series_result']).inner_text()
                check('series-cancelled','cancelled' in text.lower());check('series-exception','exception' in text.lower())
                check('series-occurrences',member in text and other in text)
                await capture(page,'cancelled-exception',width)
                # A fresh actual document has no remembered agreement identity,
                # so it can submit this genuinely already-adopted anchor and
                # display the authoritative refusal. The current document
                # intentionally hides a redundant adoption form once known.
                await context.close()
                context=await browser.new_context(viewport={'width':width,'height':900},timezone_id='Pacific/Honolulu')
                page=await context.new_page();page.set_default_timeout(5000)
                page.on('request',lambda request:requests.append(dict(method=request.method,url=request.url,bytes=len((request.post_data or '').encode()),body_sha256=hashlib.sha256((request.post_data or '').encode()).hexdigest())))
                await login(page);await lookup(page,ref)
                await page.locator(selectors['series_submit']).click();await page.locator(selectors['series_error']).wait_for()
                check('failure-atomic',bool((await page.locator(selectors['series_error']).inner_text()).strip()))
                await capture(page,'refused-adoption',width)
                await context.close()
            await browser.close()
    except BaseException as exc:
        error=dict(kind='failed-expectation' if isinstance(exc,AssertionError) else 'runner-exception',type=type(exc).__name__,message=str(exc));raise
    finally:
        c.save(error)
        (out/'browser-report.json').write_text(json.dumps(dict(candidate=release['candidate'],complete=error is None,error=error,
            seconds=time.monotonic()-began,assertions=observations,request_trace=requests,screenshots=screenshots,
            limitations=['Visual text, focus and contrast require independent human-style screenshot/source review before row binding.']),indent=2)+'\n')

async def upgrade(release,out,origin):
    """Transport-only bridge: genuine source issues login/reference/lost receipt.

    Current unmodified packaged assets are served by the target; API responses come
    from the real source until unchanged raw import completes between requests.
    No request body/key, source response, fixture state or DOM getter is rewritten.
    """
    from playwright.async_api import async_playwright
    base=release['urls']['target'];source=release['urls'][origin];c=Client(base,out/'api',release['candidate'])
    c.setup(url=source);tokens=c.tokens.copy();retained=c.create(url=source,stage=1 if origin=='accepted-s1' else 2)
    routing={'url':source,'drop':False};transport=[];error=None
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True);context=await browser.new_context(viewport={'width':375,'height':900});page=await context.new_page()
        async def route_handler(route):
            request=route.request;path=urlsplit(request.url).path
            if not path.startswith(('/auth/','/restaurants','/availability','/reservations','/reservation-moves','/series')):
                await route.continue_();return
            before=routing['url'];target=before+urlsplit(request.url).path
            if urlsplit(request.url).query:target+='?'+urlsplit(request.url).query
            response=await context.request.fetch(target,method=request.method,data=request.post_data_buffer,headers=request.headers)
            payload=await response.body()
            transport.append(dict(url=target,method=request.method,status=response.status,
                body_sha256=hashlib.sha256(request.post_data_buffer or b'').hexdigest(),response_sha256=hashlib.sha256(payload).hexdigest(),
                key_sha256=hashlib.sha256(request.headers.get('idempotency-key','').encode()).hexdigest(),response_dropped=routing['drop'] and path=='/reservations' and request.method=='POST'))
            if routing['drop'] and path=='/reservations' and request.method=='POST':routing['drop']=False;await route.abort('failed')
            else:await route.fulfill(status=response.status,headers=dict(response.headers),body=payload)
        await page.route('**/*',route_handler)
        try:
            await page.goto(base+'/login');await page.get_by_test_id('login-email').fill('u@stage3.invalid');await page.get_by_test_id('login-password').fill('independent-pass')
            await page.get_by_test_id('login-submit').click();await page.get_by_test_id('current-user').wait_for()
            await page.goto(base+'/');await page.get_by_test_id('restaurant-select').select_option('r');await page.get_by_test_id('date-input').fill(DAY)
            await page.get_by_test_id('party-size-input').fill('2');await page.get_by_test_id('search-button').click();await page.get_by_test_id('slot-c-18:00').click()
            routing['drop']=True;await page.get_by_test_id('booking-submit').click();await page.get_by_test_id('booking-uncertain').wait_for()
            before_form=await page.get_by_test_id('booking-party-size').input_value();document_id=await page.evaluate('performance.timeOrigin')
            await page.screenshot(path=str(out/'uncertain-before-import.png'),full_page=True)
            export=c.export(source);c.response('upgrade-raw-transfer',c.transfer(source,base,export),204);routing['url']=base
            await page.get_by_test_id('booking-submit').click();await page.get_by_test_id('confirmation-reference').wait_for()
            recovered=await page.get_by_test_id('confirmation-reference').text_content()
            if not recovered or before_form!=await page.get_by_test_id('booking-party-size').input_value() or document_id!=await page.evaluate('performance.timeOrigin'):
                raise AssertionError('same actual document/form/reference must survive')
            sent=[x for x in transport if x['method']=='POST' and urlsplit(x['url']).path=='/reservations']
            if len(sent)!=2 or sent[0]['body_sha256']!=sent[1]['body_sha256'] or sent[0]['key_sha256']!=sent[1]['key_sha256'] or sent[1]['status']!=200:
                raise AssertionError('unchanged key/body must recover real original receipt')
            await page.screenshot(path=str(out/'recovered-after-import.png'),full_page=True)
            await page.goto(base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(retained['reference']);await page.get_by_test_id('lookup-submit').click()
            await page.get_by_test_id('reservation-detail').wait_for();await page.screenshot(path=str(out/'retained-lookup.png'),full_page=True)
            if await page.get_by_test_id('reservation-status').text_content()!='confirmed':raise AssertionError('retained original reference lookup')
        except BaseException as exc:
            error=dict(kind='failed-expectation' if isinstance(exc,AssertionError) else 'runner-exception',type=type(exc).__name__,message=str(exc));raise
        finally:
            await context.close();await browser.close();c.save(error)
            (out/'upgrade-report.json').write_text(json.dumps(dict(candidate=release['candidate'],origin=origin,complete=error is None,error=error,transport=transport,private_export_saved=False),indent=2)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True)
    p.add_argument('--mode',choices=['product','accepted-s1','accepted-s2'],default='product');p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:raise SystemExit('Prepared only: later release and --execute required')
    release=validate_release(json.loads(Path(a.release).read_text()));out=Path(a.out)
    if out.exists():raise SystemExit('New unique output required')
    out.mkdir(parents=True)
    asyncio.run(run(release,out) if a.mode=='product' else upgrade(release,out,a.mode))

if __name__=='__main__':main()
