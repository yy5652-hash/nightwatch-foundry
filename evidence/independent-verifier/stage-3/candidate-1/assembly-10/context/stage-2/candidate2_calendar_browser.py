"""Actual explicit-zone DST/calendar display; independent zoneinfo instant oracle."""
import argparse,asyncio,datetime as dt,json,time
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
from reconstruction_probe import fixture,encoded,parse,sha
async def run(base,candidate,out):
    from playwright.async_api import async_playwright,expect
    checks=[];trace=[];counts=dict(direct=0,browser=0);errors=[];start=time.monotonic();out=Path(out);out.mkdir(exist_ok=False)
    def check(key,value):
        checks.append(dict(requirement_id='TK2R-local-display-'+key,passed=bool(value)))
        if not value:raise AssertionError(key)
    async with async_playwright() as pw:
        http=await pw.request.new_context();browser=await pw.chromium.launch(headless=True)
        try:
            for name,zone,local in [('berlin-spring','Europe/Berlin','2026-03-29T01:30'),('berlin-fall','Europe/Berlin','2026-10-25T02:30'),('new-york-spring','America/New_York','2026-03-08T01:30'),('new-york-fall','America/New_York','2026-11-01T01:30'),('last-date','UTC','9999-12-31T18:00')]:
                f=fixture();r=f['restaurants'][0];r['timezone']=zone
                for hours in r['opening_hours']:hours.update(opens='00:00',closes='23:59')
                async def call(method,path,raw=None,headers=None):
                    response=await http.fetch(base+path,method=method,data=raw,headers=headers or {'content-type':'application/json; charset=utf-8'},timeout=10000 if path.startswith('/_test/') else 5000);data=await response.body();counts['direct']+=1
                    trace.append(dict(event='direct',case=name,method=method,path=path,status=response.status,response_sha256=sha(data)))
                    return response.status,parse(data) if data else None
                status,_=await call('POST','/_test/reset',encoded(f));assert status==204
                status,auth=await call('POST','/auth/login',encoded(dict(email='reconstruct@probe.invalid',password='independent-pass')));assert status==200
                status,receipt=await call('POST','/reservations',encoded(dict(restaurant_id='r',table_ids=['b','a'],party_size=2,starts_at_local=local)),{'content-type':'application/json; charset=utf-8','authorization':'Bearer '+auth['token'],'idempotency-key':name})
                check(name+'-actual-create',status==201)
                wall=dt.datetime.fromisoformat(local).replace(tzinfo=ZoneInfo(zone),fold=0);end=(wall.astimezone(dt.timezone.utc)+dt.timedelta(minutes=90)).astimezone(ZoneInfo(zone));expected=f'{end.hour:02}:{end.minute:02}'
                check(name+'-exact-instant',dt.datetime.fromisoformat(receipt['ends_at']).astimezone(dt.timezone.utc)==end.astimezone(dt.timezone.utc))
                context=await browser.new_context(viewport={'width':375,'height':900},timezone_id='Pacific/Honolulu');page=await context.new_page();page.set_default_timeout(5000)
                def observe(request):counts['browser']+=1
                page.on('request',observe)
                try:
                    await page.goto(base+'/login');await page.get_by_test_id('login-email').fill('reconstruct@probe.invalid');await page.get_by_test_id('login-password').fill('independent-pass');await page.get_by_test_id('login-submit').click();await expect(page.get_by_test_id('current-user')).to_contain_text('Independent Diner')
                    await page.goto(base+'/lookup');await page.get_by_test_id('lookup-reference-input').fill(receipt['reference']);await page.get_by_test_id('lookup-submit').click();await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
                    node=page.locator('dl div').filter(has=page.locator('dt',has_text='Ends at')).locator('dd');shown=await node.inner_text();check(name+'-restaurant-local-end',expected in shown)
                    check(name+'-truthful-wire',await node.locator('time').get_attribute('datetime')==receipt['ends_at'])
                    check(name+'-status',await page.get_by_test_id('reservation-status').inner_text()=='confirmed')
                    widths=await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');check(name+'-mobile',widths['scroll']<=widths['width'])
                    trace.append(dict(event='actual-explicit-zone-display',case=name,restaurant_zone=zone,browser_zone='Pacific/Honolulu',starts_at_local=local,original_ends_at=receipt['ends_at'],oracle_end=end.isoformat(),displayed=shown,widths=widths))
                    await page.screenshot(path=str(out/(name+'-lookup.png')),full_page=True)
                finally:await context.close()
        except Exception as error:errors.append(dict(type=type(error).__name__,message=str(error),classification='recorded-expectation' if isinstance(error,AssertionError) else 'runner-exception'))
        finally:await browser.close();await http.dispose()
    data=dict(candidate=candidate,assertions=len(checks),failures=sum(not x['passed'] for x in checks),counts=counts,errors=errors,seconds=time.monotonic()-start)
    for name,value in [('assertions',checks),('trace',trace),('summary',data)]: (out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(data));return bool(errors or data['failures'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);a=p.parse_args();raise SystemExit(asyncio.run(run(a.base,a.candidate,a.out)))
if __name__=='__main__':main()
