"""Real recurring uncertainty, private refusals and stale agreement responses.

Transport faults follow a real server commit. Successful response values are
never invented; unchanged retries must recover that actual original receipt.
"""
import argparse,asyncio,hashlib,json
from pathlib import Path
from urllib.parse import urlsplit
from stage3_probe import Client,fixture,create_body,raw,parse,same,integer,validate_release,DAY
from stage3_metrics import STYLE

async def run(release,out):
 from playwright.async_api import async_playwright,expect
 c=Client(release['urls']['target'],out/'api',release['candidate']);checks=[];trace=[];metrics=[];shots=[];error=None
 def check(name,value,detail=None):
  checks.append(dict(requirement_id='TK3-browser-'+name,passed=bool(value),detail=detail))
  if not value:raise AssertionError(name)
 async def capture(page,name,width):
  path=out/(name+'-'+str(width)+'.png');await page.screenshot(path=str(path),full_page=True);shots.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  m=await page.evaluate(STYLE);metrics.append(dict(name=name,width=width,metrics=m));check(name+'-'+str(width)+'-no-page-scroll',m['scroll']<=m['client'])
  check(name+'-'+str(width)+'-contrast',bool(m['text']) and all(t['ratio']>=t['minimum'] for t in m['text']))
  labels=await page.evaluate('''()=>Array.from(document.querySelectorAll('input,select')).filter(e=>e.getBoundingClientRect().height>0).map(e=>({id:e.id,labels:Array.from(e.labels||[]).map(l=>l.innerText.trim())}))''')
  check(name+'-'+str(width)+'-visible-labels',all(v['labels'] and all(v['labels']) for v in labels),labels)
  await page.keyboard.press('Tab');focus=await page.evaluate('''()=>({tag:document.activeElement.tagName,outline:getComputedStyle(document.activeElement).outlineStyle,width:getComputedStyle(document.activeElement).outlineWidth})''')
  check(name+'-'+str(width)+'-keyboard-focus',focus['tag']!='BODY' and focus['outline']!='none' and float(focus['width'].removesuffix('px'))>0,focus)
  check(name+'-'+str(width)+'-real-screenshot',path.is_file() and path.stat().st_size>0)
 async def login(page,user='u'):
  await page.goto(c.base+'/login');await page.get_by_test_id('login-email').fill(user+'@stage3.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click();await expect(page.get_by_test_id('current-user')).to_be_visible()
 async def lookup(page,ref):
  await page.goto(c.base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(ref);await page.get_by_test_id('lookup-submit').click();await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  try:
   for width in (375,1280):
    for fault in ('drop','malformed'):
     c.setup();anchor=c.create();context=await browser.new_context(viewport={'width':width,'height':900},timezone_id='Pacific/Honolulu');page=await context.new_page();page.set_default_timeout(5000)
     page.on('request',lambda r:trace.append(dict(event='browser-request',method=r.method,path=urlsplit(r.url).path,body_sha256=hashlib.sha256(r.post_data_buffer or b'').hexdigest())))
     try:
      await login(page);await lookup(page,anchor['reference']);await page.get_by_test_id('series-count').fill('3');await page.get_by_test_id('series-interval-weeks').fill('1');saved={}
      async def commit_then_fail(route):
       response=await route.fetch();data=await response.body();saved.update(body=route.request.post_data_buffer,key=route.request.headers.get('idempotency-key'),receipt=parse(data),status=response.status)
       trace.append(dict(event='genuine-commit-before-'+fault,status=response.status,response_sha256=hashlib.sha256(data).hexdigest(),request_sha256=hashlib.sha256(saved['body']).hexdigest(),key_sha256=hashlib.sha256(saved['key'].encode()).hexdigest()))
       if fault=='drop':await route.abort('connectionfailed')
       else:await route.fulfill(status=response.status,headers={'content-type':'application/json; charset=utf-8'},body=b'{"series_id":')
      await page.route('**/series',commit_then_fail,times=1)
      await page.get_by_test_id('series-count').focus();await page.keyboard.press('Enter');await expect(page.get_by_test_id('series-uncertain')).to_be_visible()
      check('uncertain-recovery',saved['status']==201 and bool((await page.get_by_test_id('series-uncertain').inner_text()).strip()) and await page.get_by_test_id('series-error').count()==0 and await page.get_by_test_id('series-confirmation').count()==0 and await page.get_by_test_id('series-occurrences').count()==0)
      check('uncertain-form-identity',await page.get_by_test_id('series-count').input_value()=='3' and await page.get_by_test_id('series-interval-weeks').input_value()=='1')
      await capture(page,'uncertain-retry-'+fault,width)
      async with page.expect_response(lambda r:urlsplit(r.url).path=='/series' and r.request.method=='POST') as pending:
       await page.get_by_test_id('series-submit').focus();await page.keyboard.press('Enter')
      response=await pending.value;replayed=parse(await response.body());await expect(page.get_by_test_id('series-occurrences')).to_be_visible()
      check('uncertain-original-receipt',response.status==200 and response.request.post_data_buffer==saved['body'] and response.request.headers['idempotency-key']==saved['key'] and same(replayed,saved['receipt']))
      check('uncertain-clear',await page.get_by_test_id('series-uncertain').count()==0 and await page.get_by_test_id('series-error').count()==0)
      rendered=await page.get_by_test_id('series-occurrences').inner_text()
      check('series-occurrences',all(o['reference'] in rendered for o in saved['receipt']['occurrences']))
      check('series-one-real-agreement',integer(c.response('series-get-current',c.call('GET','/series/'+saved['receipt']['series_id'],token=c.tokens['u']),200)['revision'])==1 and len(c.response('series-ordinary-list',c.call('GET','/reservations',token=c.tokens['u']),200)['reservations'])==3)
      await capture(page,'uncertain-recovered-'+fault,width)
     finally:await context.close()
    c.setup();anchor=c.create(seats=('b','a'),party=5);s=c.response('series-response-status',c.call('POST','/series',dict(anchor_reference=anchor['reference'],count=3,interval_weeks=1),token=c.tokens['u'],key='private'),201)
    context=await browser.new_context(viewport={'width':width,'height':900});page=await context.new_page();page.set_default_timeout(5000)
    page.on('request',lambda r:trace.append(dict(event='browser-request',method=r.method,path=urlsplit(r.url).path,body_sha256=hashlib.sha256(r.post_data_buffer or b'').hexdigest())))
    page.on('request',lambda r:trace.append(dict(event='browser-request',method=r.method,path=urlsplit(r.url).path,body_sha256=hashlib.sha256(r.post_data_buffer or b'').hexdigest())))
    try:
     await login(page,'m');await page.goto(c.base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(anchor['reference']);await page.get_by_test_id('lookup-submit').click();await expect(page.get_by_test_id('reservation-error')).to_be_visible()
     check('manager-privacy',await page.get_by_test_id('reservation-detail').count()==0 and await page.get_by_test_id('reservation-history').count()==0 and await page.get_by_test_id('series-occurrences').count()==0)
     await capture(page,'manager-private-refusal',width)
     await page.get_by_test_id('logout-button').click();check('logout-clears-private',await page.get_by_test_id('current-user').count()==0 and await page.get_by_test_id('reservation-history').count()==0)
    finally:await context.close()
    # Actual cancelled owner still gets its terminal history and accepted terms.
    c.response('history-cancel-empty',c.call('POST','/reservations/'+anchor['reference']+'/cancel',{},token=c.tokens['u']),200)
    context=await browser.new_context(viewport={'width':width,'height':900});page=await context.new_page();page.set_default_timeout(5000)
    try:
     await login(page);await lookup(page,anchor['reference']);await expect(page.get_by_test_id('reservation-history')).to_be_visible();await page.get_by_test_id('reservation-history').locator('summary').last.click()
     check('cancelled-history',await page.get_by_test_id('reservation-status').inner_text()=='cancelled' and 'Cancelled' in await page.get_by_test_id('reservation-history').inner_text() and await page.get_by_test_id('reservation-cancel-button').count()==0)
     await capture(page,'cancelled-history',width)
    finally:await context.close()
   # Out-of-order current agreement A/B reads in one real document.
   c.setup();a=c.create();b=c.response('setup-create',c.call('POST','/reservations',dict(restaurant_id='r2',table_id='x',party_size=2,starts_at_local=DAY+'T18:00'),token=c.tokens['u'],key='r2'),201)
   agreements=[]
   for i,anchor in enumerate((a,b)):agreements.append(c.response('series-response-status',c.call('POST','/series',dict(anchor_reference=anchor['reference'],count=2,interval_weeks=1),token=c.tokens['u'],key='s'+str(i)),201))
   context=await browser.new_context(viewport={'width':375,'height':900});page=await context.new_page();page.set_default_timeout(5000);hold=asyncio.Event();started=asyncio.Event()
   page.on('request',lambda r:trace.append(dict(event='browser-request',method=r.method,path=urlsplit(r.url).path,body_sha256=hashlib.sha256(r.post_data_buffer or b'').hexdigest())))
   try:
    await login(page);await lookup(page,a['reference'])
    async def delayed(route):
     response=await route.fetch();started.set();await hold.wait();await route.fulfill(response=response)
    await page.route('**/series/'+agreements[0]['series_id'],delayed,times=1)
    await page.get_by_test_id('series-lookup-id').fill(agreements[0]['series_id']);await page.get_by_test_id('series-refresh').click();await started.wait()
    await page.get_by_test_id('series-lookup-id').fill(agreements[1]['series_id']);await page.get_by_test_id('series-refresh').click();await expect(page.get_by_test_id('series-occurrences')).to_contain_text('Cedar Kitchen')
    hold.set();await page.wait_for_timeout(100);text=await page.get_by_test_id('series-occurrences').inner_text()
    check('agreement-search-race',all(o['reference'] in text for o in agreements[1]['occurrences']) and all(o['reference'] not in text for o in agreements[0]['occurrences']) and 'Cedar Table' in text)
    await capture(page,'agreement-race-current-B',375)
   finally:hold.set();await context.close()
  except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc));raise
  finally:
   await browser.close();c.save(error)
   (out/'browser-report.json').write_text(json.dumps(dict(candidate=release['candidate'],complete=error is None,error=error,assertions=checks,request_trace=trace,metrics=metrics,screenshots=shots),indent=2)+'\n')
def main():
 p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate_release(json.loads(Path(a.release).read_text()));out=Path(a.out);out.mkdir(parents=True,exist_ok=False);asyncio.run(run(release,out))
if __name__=='__main__':main()
