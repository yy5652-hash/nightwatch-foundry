"""Observe real candidate elements before releasing the prepared browser client."""
import argparse,asyncio,hashlib,json
from pathlib import Path
from urllib.parse import urlsplit
from stage3_probe import Client,validate_release,fixture
SELECTORS=dict(accepted_terms='[data-testid="reservation-current-terms"]',history='[data-testid="reservation-history"]',series_count='[data-testid="series-count"]',
 series_interval='[data-testid="series-interval-weeks"]',series_submit='[data-testid="series-submit"]',series_result='[data-testid="series-occurrences"]',series_error='[data-testid="series-error"]')
async def observe(release,out):
 from playwright.async_api import async_playwright,expect
 c=Client(release['urls']['target'],out/'api',release['candidate']);c.setup();anchor=c.create();observed={};trace=[];error=None
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True);context=await browser.new_context(viewport={'width':375,'height':900});page=await context.new_page();page.set_default_timeout(5000)
   page.on('request',lambda request:trace.append(dict(method=request.method,path=urlsplit(request.url).path,body_sha256=hashlib.sha256((request.post_data or '').encode()).hexdigest())))
   await page.goto(c.base+'/login');await page.get_by_test_id('login-email').fill('u@stage3.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click();await page.get_by_test_id('current-user').wait_for()
   await page.goto(c.base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(anchor['reference']);await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('reservation-history').wait_for()
   for key in ('accepted_terms','history','series_count','series_interval','series_submit'):
    node=page.locator(SELECTORS[key]);await expect(node).to_be_visible();observed[key]=dict(selector=SELECTORS[key],count=await node.count(),visible=True)
   await page.locator(SELECTORS['series_count']).fill('1');await page.locator(SELECTORS['series_submit']).click();await expect(page.locator(SELECTORS['series_error'])).to_be_visible()
   observed['series_error']=dict(selector=SELECTORS['series_error'],visible=True,text=await page.locator(SELECTORS['series_error']).inner_text())
   await page.locator(SELECTORS['series_count']).fill('2');await page.locator(SELECTORS['series_submit']).click();await expect(page.locator(SELECTORS['series_result'])).to_be_visible()
   observed['series_result']=dict(selector=SELECTORS['series_result'],visible=True,text=await page.locator(SELECTORS['series_result']).inner_text())
   await page.screenshot(path=str(out/'actual-bound-elements.png'),full_page=True);await context.close();await browser.close()
 except BaseException as exc:error=dict(type=type(exc).__name__,message=str(exc));raise
 finally:
  c.save(error);(out/'selector-proof.json').write_text(json.dumps(dict(candidate=release['candidate'],complete=error is None,error=error,observed=observed,requests=trace,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
 return observed
def main():
 p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate_release(json.loads(Path(a.release).read_text()));out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
 observed=asyncio.run(observe(release,out));assert set(observed)==set(SELECTORS)
 release.update(browser_selectors=SELECTORS,selectors_observed_on_candidate=True,browser_selector_proof='/evidence/'+out.name+'/selector-proof.json')
 (out/'browser-release.json').write_text(json.dumps(release,indent=2)+'\n')
if __name__=='__main__':main()
