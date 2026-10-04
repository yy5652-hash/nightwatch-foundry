"""Real UI protocol skeleton with executable manager/owner flows.

New selectors are deliberately unbound until observed on the released product.
No native browser launch or API call happens during preparation.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from stage4_probe import Client,fixture,DAY,closure,validate_release,same,integer

REQUIRED=('manager_entry','manager_table','manager_from','manager_to','preview_submit','preview_result','apply_submit','plan_feedback',
          'series_entry','series_revision','series_from_index','series_clock','series_amend_submit','series_current','series_feedback')
def validate_selectors(release):
    bindings=release.get('browser_selectors',{})
    if release.get('selectors_observed_on_candidate') is not True:raise ValueError('Observe actual released product selectors first')
    if any(not isinstance(bindings.get(k),str) or not bindings[k] for k in REQUIRED):raise ValueError('No invented Stage4 selectors')
    proof=Path(release.get('selector_proof_path',''))
    if not proof.is_file() or hashlib.sha256(proof.read_bytes()).hexdigest()!=release.get('selector_proof_sha256'):raise ValueError('Concrete current selector proof required')
    return bindings

async def run(release,out,family):
    from playwright.async_api import async_playwright
    selectors=validate_selectors(release);out.mkdir(parents=True,exist_ok=False)
    c=Client(release['urls']['target'],out/'api',release['candidate']);checks=[];screens=[];error=None
    def check(slug,value,detail=None):
        checks.append(dict(requirement_id='TK4-product-'+slug,passed=bool(value),detail=detail))
        if not value:raise AssertionError(slug)
    async def capture(page,name):
        p=out/(name+'.png');await page.screenshot(path=str(p),full_page=True)
        screens.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),kind='actual full-page screenshot'))
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch()
            for width in (375,1280):
                c.seed();a=c.make();s=c.adopt(a)
                context=await browser.new_context(viewport=dict(width=width,height=900),timezone_id='Pacific/Honolulu')
                page=await context.new_page();traffic=[]
                page.on('request',lambda r:traffic.append(dict(method=r.method,url=r.url,body_sha256=hashlib.sha256((r.post_data or '').encode()).hexdigest())))
                await page.goto(release['urls']['target']+'/login')
                user='m' if family=='manager' else 'u'
                await page.get_by_test_id('login-email').fill(user+'@stage3.invalid')
                await page.get_by_test_id('login-password').fill('independent-pass')
                await page.get_by_test_id('login-submit').click();await page.get_by_test_id('current-user').wait_for()
                if family=='manager':
                    await page.locator(selectors['manager_entry']).click()
                    await page.locator(selectors['manager_table']).select_option('a')
                    b=closure();await page.locator(selectors['manager_from']).fill(b['from']);await page.locator(selectors['manager_to']).fill(b['to'])
                    original=c.lookup(a['reference']);await page.locator(selectors['preview_submit']).click()
                    await page.locator(selectors['preview_result']).wait_for();check('preview-readonly',same(original,c.lookup(a['reference'])))
                    await capture(page,'proposed-'+str(width))
                    async with page.expect_response(lambda r:'/replans/' in r.url and r.url.endswith('/apply') and r.request.method=='POST') as waiting:
                        await page.locator(selectors['apply_submit']).focus();await page.keyboard.press('Enter')
                    response=await waiting.value;check('apply-authoritative',response.status==201)
                    now=c.lookup(a['reference']);check('lookup-current',now['table_ids']!=original['table_ids'])
                    await capture(page,'committed-'+str(width))
                elif family=='amend':
                    await page.goto(release['urls']['target']+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(a['reference'])
                    await page.get_by_test_id('lookup-submit').click();await page.get_by_test_id('reservation-detail').wait_for()
                    # Bindings may locate a same-document series lookup control.
                    await page.locator(selectors['series_entry']).fill(s['series_id']);await page.locator(selectors['series_entry']).press('Enter')
                    await page.locator(selectors['series_current']).wait_for()
                    current=c.current_series(s)
                    await page.locator(selectors['series_revision']).fill(str(integer(current['revision'])))
                    await page.locator(selectors['series_from_index']).fill('0');await page.locator(selectors['series_clock']).fill('19:00')
                    await page.locator(selectors['series_amend_submit']).focus();await page.keyboard.press('Enter')
                    await page.locator(selectors['series_current']).wait_for()
                    # Real API truth and browser-originated response, no DOM getter override.
                    current=c.current_series(s);check('amend-real',all(o['reservation']['starts_at_local'].endswith('T19:00') for o in current['occurrences']))
                    await capture(page,'amended-'+str(width))
                check('mobile' if width==375 else 'desktop',await page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                (out/('traffic-'+str(width)+'.json')).write_text(json.dumps(traffic,indent=2)+'\n')
                await context.close()
            await browser.close()
    except Exception as e:error=repr(e);raise
    finally:
        c.save(error)
        (out/'summary.json').write_text(json.dumps(dict(candidate=release['candidate'],family=family,assertions=len(checks),failed=sum(not x['passed'] for x in checks),
             complete=error is None,error=error,checks=checks,screenshots=screens,scope='actual specified interactions; further recovery/race/upgrade scopes require full independent extension'),indent=2)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--family',choices=['manager','amend'],required=True);p.add_argument('--execute',action='store_true');a=p.parse_args()
    if not a.execute:raise SystemExit('Stage4 execution held')
    release=validate_release(json.loads(a.release.read_text()));validate_selectors(release);asyncio.run(run(release,a.out,a.family))
if __name__=='__main__':main()
