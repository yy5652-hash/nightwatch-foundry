"""Future real manager/owner committed-loss and malformed-response recovery.

All new selectors and workflow actions must come from current observed proof.
The route forwards real bytes to the real candidate before deliberately losing
or corrupting that response. It never manufactures a successful server result.
"""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from stage4_probe import Client, closure, DAY, same, integer, raw
from stage3_probe import parse
from stage3_metrics import STYLE
sys.path.insert(0,str(ROOT/'repair-1'))
from release_guard import validate

FIELDS = {
    'preview': ['manager_table', 'manager_from', 'manager_to'],
    'apply': ['manager_table', 'manager_from', 'manager_to'],
    'amend': ['series_revision', 'series_from_index', 'series_clock'],
}
NODES = {
    'preview': ['preview_submit', 'preview_result', 'preview_uncertain', 'preview_error'],
    'apply': ['apply_submit', 'apply_result', 'apply_uncertain', 'apply_error'],
    'amend': ['series_amend_submit', 'series_amend_result', 'series_amend_uncertain', 'series_amend_error'],
}


def bindings(release, family):
    proof = json.loads(Path(release['selector_proof_path']).read_text())
    selectors = release['browser_selectors']
    workflows = release.get('browser_workflows', {})
    if proof.get('selectors') != selectors or proof.get('workflows') != workflows:
        raise ValueError('Use exactly the current observed selectors and workflow steps')
    required = FIELDS[family] + NODES[family] + (NODES['preview'][:2] if family == 'apply' else [])
    if any(not isinstance(selectors.get(key), str) or not selectors[key].strip() for key in required):
        raise ValueError('Missing actual current recovery control binding')
    name = 'open_manager' if family != 'amend' else 'open_series'
    steps = workflows.get(name)
    if not steps:
        raise ValueError('Actual observed same-document workflow is required')
    for step in steps:
        if step.get('action') not in ['goto', 'click', 'fill', 'select_option', 'press']:
            raise ValueError('Workflow actions must use real browser controls')
        if step['action'] == 'goto':
            if not step.get('value', '').startswith('/'):
                raise ValueError('Observed workflow must stay at the actual service')
        elif step.get('selector_key') not in selectors:
            raise ValueError('Unobserved workflow selector')
    return selectors, steps


async def run(release, out, family, mode):
    from playwright.async_api import async_playwright
    selectors, steps = bindings(release, family)
    out.mkdir(parents=True, exist_ok=False)
    c = Client(release['urls']['target'], out / 'api', release['candidate'])
    checks, transport, traffic, screenshots = [], [], [], []
    error = None
    base = release['urls']['target']
    def check(name, condition, detail=None):
        checks.append(dict(requirement_id='TK4-browser-recovery-' + name, passed=bool(condition), detail=detail))
        if not condition:
            raise AssertionError(name)
    async def screenshot(page, name):
        path = out / (name + '.png')
        await page.screenshot(path=str(path), full_page=True)
        screenshots.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        metrics = await page.evaluate(STYLE)
        check(name + '-width', metrics['scroll'] <= metrics['client'], dict(scroll=metrics['scroll'], client=metrics['client']))
        check(name + '-contrast', bool(metrics['text']) and all(t['ratio'] >= t['minimum'] for t in metrics['text']), metrics)
    async def form(page):
        return {key: (await page.locator(selectors[key]).inner_text() if key=='series_revision' else await page.locator(selectors[key]).input_value()) for key in FIELDS[family]}
    async def workflow(page, values):
        for step in steps:
            value = step.get('value', '')
            for key, replacement in values.items():
                value = value.replace('${' + key + '}', replacement)
            if step['action'] == 'goto':
                await page.goto(base + value)
            else:
                locator = page.locator(selectors[step['selector_key']])
                if step['action'] == 'click':
                    await locator.click()
                else:
                    await getattr(locator, step['action'])(value)
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            for width in [375, 1280]:
                c.seed()
                a = c.make()
                s = c.adopt(a)
                context = await browser.new_context(viewport=dict(width=width, height=900))
                page = await context.new_page()
                page.set_default_timeout(5000)
                page.on('request', lambda request: traffic.append(dict(method=request.method,
                    path=urlsplit(request.url).path, body_sha256=hashlib.sha256(request.post_data_buffer or b'').hexdigest())))
                await page.goto(base + '/login')
                who = 'u' if family == 'amend' else 'm'
                await page.get_by_test_id('login-email').fill(who + '@stage3.invalid')
                await page.get_by_test_id('login-password').fill('independent-pass')
                await page.get_by_test_id('login-submit').click()
                await page.get_by_test_id('current-user').wait_for()
                await workflow(page, dict(series_id=s['series_id'], reference=a['reference']))
                if family == 'amend':
                    check('actual-auto-revision-'+str(width), str(integer(s['revision'])) in await page.locator(selectors['series_revision']).inner_text())
                    await page.locator(selectors['series_from_index']).fill('0')
                    await page.locator(selectors['series_clock']).fill('19:00')
                else:
                    b = closure()
                    await page.locator(selectors['manager_table']).select_option('a')
                    await page.locator(selectors['manager_from']).fill(b['from'])
                    await page.locator(selectors['manager_to']).fill(b['to'])
                    if family == 'apply':
                        await page.locator(selectors['preview_submit']).click()
                        await page.locator(selectors['preview_result']).wait_for()
                attempt = dict(armed=True, records=[], receipt=None)
                async def route_handler(route):
                    request = route.request
                    path = urlsplit(request.url).path
                    selected = request.method == 'POST' and (
                        path == '/restaurants/r/replans' if family == 'preview' else
                        path.startswith('/restaurants/r/replans/') and path.endswith('/apply') if family == 'apply' else
                        path == '/series/' + s['series_id'] + '/amend')
                    if not selected:
                        await route.continue_()
                        return
                    response = await context.request.fetch(request.url, method=request.method,
                        data=request.post_data_buffer, headers=request.headers)
                    payload = await response.body()
                    record = dict(width=width, path=path, method=request.method, status=response.status,
                        body_sha256=hashlib.sha256(request.post_data_buffer or b'').hexdigest(),
                        key_sha256=hashlib.sha256(request.headers.get('idempotency-key', '').encode()).hexdigest(),
                        response_sha256=hashlib.sha256(payload).hexdigest(), injected=mode if attempt['armed'] else None)
                    attempt['records'].append(record)
                    transport.append(record)
                    if attempt['receipt'] is None:
                        attempt['receipt'] = parse(payload)
                    if attempt['armed']:
                        attempt['armed'] = False
                        if mode == 'lost':
                            await route.abort('failed')
                        else:
                            headers = {k: v for k, v in response.headers.items() if k.lower() not in ['content-length', 'content-encoding']}
                            await route.fulfill(status=response.status, headers=headers, body=b'{')
                    else:
                        record['same_original_receipt'] = same(attempt['receipt'], parse(payload))
                        await route.fulfill(status=response.status, headers=dict(response.headers), body=payload)
                await page.route('**/*', route_handler)
                submit_key, result_key, uncertain_key, error_key = NODES[family]
                before_form = await form(page)
                document = await page.evaluate('performance.timeOrigin')
                button = page.locator(selectors[submit_key])
                await button.focus()
                focus = await button.evaluate('e=>({active:e===document.activeElement,style:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth})')
                check('focus-' + str(width), focus['active'] and focus['style'] != 'none' and float(focus['width'].removesuffix('px')) > 0, focus)
                await page.keyboard.press('Enter')
                await page.locator(selectors[uncertain_key]).wait_for()
                check('uncertain-text-' + str(width), bool((await page.locator(selectors[uncertain_key]).inner_text()).strip()))
                check('no-false-result-' + str(width), not await page.locator(selectors[result_key]).is_visible() and not await page.locator(selectors[error_key]).is_visible())
                check('actual-first-success-' + str(width), len(attempt['records']) == 1 and attempt['records'][0]['status'] == 201)
                check('unchanged-form-' + str(width), before_form == await form(page))
                await screenshot(page, family + '-' + mode + '-uncertain-' + str(width))
                await button.focus()
                await page.keyboard.press('Enter')
                await page.locator(selectors[result_key]).wait_for()
                check('same-document-' + str(width), document == await page.evaluate('performance.timeOrigin'))
                check('retry-form-' + str(width), before_form == await form(page))
                records = attempt['records']
                check('original-retry-' + str(width), len(records) == 2 and records[1]['status'] == 200 and
                    records[0]['path'] == records[1]['path'] and records[0]['body_sha256'] == records[1]['body_sha256'] and
                    records[0]['key_sha256'] == records[1]['key_sha256'] and records[1].get('same_original_receipt') is True)
                check('uncertainty-cleared-' + str(width), not await page.locator(selectors[uncertain_key]).is_visible() and not await page.locator(selectors[error_key]).is_visible())
                text = await page.locator(selectors[result_key]).inner_text()
                receipt = attempt['receipt']
                if family != 'amend':
                    check('original-plan-id-' + str(width), receipt['plan_id'] in (text if family=='preview' else await page.get_by_test_id('replan-plan-id').inner_text()))
                else:
                    check('original-series-references-' + str(width), all(o['reference'] in text for o in receipt['occurrences']))
                await screenshot(page, family + '-' + mode + '-recovered-' + str(width))
                await context.close()
            await browser.close()
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        c.save(error)
        (out / 'report.json').write_text(json.dumps(dict(candidate=release['candidate'], family=family, mode=mode,
            complete=error is None, error=error, assertions=checks, transport=transport, browser_requests=traffic,
            screenshots=screenshots, private_exports_saved=False,
            scope='Actual candidate operations only after release; scoped focus/width/contrast, not full accessibility'), indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--family', choices=list(FIELDS), required=True)
    parser.add_argument('--mode', choices=['lost', 'malformed'], required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit('Repaired candidate browser execution held')
    release = validate(json.loads(args.release.read_text()), browser=True)
    asyncio.run(run(release, args.out, args.family, args.mode))


if __name__ == '__main__':
    main()
