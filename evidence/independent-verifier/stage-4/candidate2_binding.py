"""Bind actual current manager/owner controls through real status transitions."""
import argparse,asyncio,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate
from stage4_probe import Client,closure,integer
SELECTORS=dict(manager_entry='a[href="/manage"]',manager_table='[data-testid="replan-table"]',manager_from='[data-testid="replan-from"]',manager_to='[data-testid="replan-to"]',preview_submit='[data-testid="replan-preview-submit"]',preview_result='[data-testid="replan-proposal"]',preview_uncertain='[data-testid="replan-uncertain"]',preview_error='[data-testid="replan-error"]',apply_submit='[data-testid="replan-apply-submit"]',apply_result='[data-testid="replan-applied"]',apply_uncertain='[data-testid="replan-apply-uncertain"]',apply_error='[data-testid="replan-apply-error"]',plan_feedback='[data-testid="replan-unapplied"]',series_entry='[data-testid="series-lookup-id"]',series_revision='[data-testid="series-amend-expected-revision"]',series_from_index='[data-testid="series-amend-from-index"]',series_clock='[data-testid="series-amend-local-time"]',series_amend_submit='[data-testid="series-amend-submit"]',series_current='[data-testid="series-occurrences"]',series_feedback='[data-testid="series-amend-form"]',series_amend_result='[data-testid="series-amend-confirmation"]',series_amend_uncertain='[data-testid="series-amend-uncertain"]',series_amend_error='[data-testid="series-amend-error"]',lookup_reference='[data-testid="lookup-reference-input"]',lookup_submit='[data-testid="lookup-submit"]',series_load_submit='[data-testid="series-refresh"]')
WORKFLOWS=dict(open_manager=[dict(action='click',selector_key='manager_entry')],open_series=[dict(action='goto',value='/lookup'),dict(action='fill',selector_key='lookup_reference',value='${reference}'),dict(action='click',selector_key='lookup_submit'),dict(action='fill',selector_key='series_entry',value='${series_id}'),dict(action='click',selector_key='series_load_submit')])
async def observe(release,out):
    from playwright.async_api import async_playwright
    c=Client(release['urls']['target'],out/'api',release['candidate']);observed={};traffic=[];error=None
    async def remember(page,keys,state):
        for key in keys:
            node=page.locator(SELECTORS[key]);await node.wait_for(state='visible')
            observed.setdefault(key,[]).append(dict(state=state,count=await node.count(),visible=await node.is_visible(),text=(await node.inner_text())[:1200],tag=await node.evaluate('e=>e.tagName')))
    async def login(page,who):
        await page.goto(c.base+'/login');await page.get_by_test_id('login-email').fill(who+'@stage3.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click();await page.get_by_test_id('current-user').wait_for()
    async def drop_once(page,path):
        async def route_handler(route):
            if route.request.method!='POST':await route.continue_();return
            response=await page.context.request.fetch(route.request.url,method='POST',data=route.request.post_data_buffer,headers=route.request.headers)
            body=await response.body();traffic.append(dict(kind='forward-then-drop',path=path,status=response.status,response_sha256=hashlib.sha256(body).hexdigest()))
            assert response.status==201
            await route.abort('failed');await page.unroute('**'+path,route_handler)
        await page.route('**'+path,route_handler)
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch(headless=True)
            c.seed();anchor=c.make();context=await browser.new_context(viewport=dict(width=375,height=900));page=await context.new_page();page.set_default_timeout(5000)
            await login(page,'m');await remember(page,['manager_entry'],'real-manager-navigation');await page.locator(SELECTORS['manager_entry']).click()
            await remember(page,['manager_table','manager_from','manager_to','preview_submit'],'fixture-listed-manager-form')
            b=closure();await page.locator(SELECTORS['manager_table']).select_option('a');await page.locator(SELECTORS['manager_from']).fill(b['from']);await page.locator(SELECTORS['manager_to']).fill('invalid');await page.locator(SELECTORS['preview_submit']).click();await remember(page,['preview_error'],'actual422-refusal')
            await page.locator(SELECTORS['manager_to']).fill(b['to']);await drop_once(page,'/restaurants/r/replans');await page.locator(SELECTORS['preview_submit']).click();await remember(page,['preview_uncertain'],'actual201-response-lost')
            await page.locator(SELECTORS['preview_submit']).click();await remember(page,['preview_result','apply_submit','plan_feedback'],'original-preview-replay')
            # A real external write invalidates the displayed preview.
            c.make(seats=('f',),local='2035-06-04T21:00',key='later-write')
            await page.locator(SELECTORS['apply_submit']).click();await remember(page,['apply_error'],'actual-stale-plan409')
            await page.get_by_test_id('replan-fresh-preview').click();await page.locator(SELECTORS['preview_result']).wait_for()
            plan=await page.get_by_test_id('replan-plan-id').inner_text();await drop_once(page,'/restaurants/r/replans/'+plan+'/apply');await page.locator(SELECTORS['apply_submit']).click();await remember(page,['apply_uncertain'],'actual-applied201-response-lost')
            await page.locator(SELECTORS['apply_submit']).click();await remember(page,['apply_result'],'original-application-replay')
            await page.screenshot(path=str(out/'actual-manager-elements.png'),full_page=True);await context.close()
            c.seed();anchor=c.make();s=c.adopt(anchor)
            context=await browser.new_context(viewport=dict(width=375,height=900));page=await context.new_page();page.set_default_timeout(5000);await login(page,'u')
            await page.goto(c.base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(anchor['reference']);await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('reservation-detail').wait_for()
            await remember(page,['lookup_reference','lookup_submit','series_entry','series_load_submit'],'actual-owner-lookup')
            await page.locator(SELECTORS['series_entry']).fill(s['series_id']);await page.locator(SELECTORS['series_load_submit']).click();await remember(page,['series_current','series_revision','series_from_index','series_clock','series_amend_submit','series_feedback'],'loaded-genuine-agreement')
            await page.locator(SELECTORS['series_from_index']).fill('99');await page.locator(SELECTORS['series_amend_submit']).click();await remember(page,['series_amend_error'],'visible-invalid-index')
            await page.locator(SELECTORS['series_from_index']).fill('0');await page.locator(SELECTORS['series_clock']).fill('19:00');await drop_once(page,'/series/'+s['series_id']+'/amend');await page.locator(SELECTORS['series_amend_submit']).click();await remember(page,['series_amend_uncertain'],'actual-amended201-response-lost')
            await page.locator(SELECTORS['series_amend_submit']).click();await remember(page,['series_amend_result'],'original-amendment-replay')
            await page.screenshot(path=str(out/'actual-owner-elements.png'),full_page=True);await context.close();await browser.close()
    except BaseException as exc:error=repr(exc);raise
    finally:
        c.save(error);(out/'selector-proof.json').write_text(json.dumps(dict(candidate=release['candidate'],complete=error is None,error=error,selectors=SELECTORS,workflows=WORKFLOWS,observed=observed,traffic=traffic,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),revision_control='Actual revision paragraph and current-revision action; not an editable numeric input'),indent=2)+'\n')
    assert set(observed)==set(SELECTORS)
def main():
    p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args();release=validate(json.loads(Path(a.release).read_text()));out=Path(a.out);out.mkdir(parents=True,exist_ok=False);asyncio.run(observe(release,out))
    proof=out/'selector-proof.json';release.update(browser_selectors=SELECTORS,browser_workflows=WORKFLOWS,selectors_observed_on_candidate=True,selector_proof_path=str(proof),selector_proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
    (out/'browser-release.json').write_text(json.dumps(release,indent=2)+'\n')
if __name__=='__main__':main()
