"""Displayed local start/end truths under the explicit historic wire-offset interpretation."""
import argparse,asyncio,json,time
import datetime as dt
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright,expect
from browser import BrowserProbe
from api import pair_fixture
class Historical(BrowserProbe):
    async def historical(self):
        for zone in ['Europe/Berlin','Europe/Brussels','America/New_York']:
            f=pair_fixture(zone=zone,opens='18:00',closes='23:00');await self.reset(f)
            local='0001-01-01T18:00'
            status,receipt=await self.api('POST','/reservations',dict(restaurant_id='r',table_id='t0',starts_at_local=local,party_size=2),token=self.tokens['u_a'],key='historical-'+zone)
            if status!=201:raise RuntimeError('Historical source booking refused')
            # Independently calculate absolute duration using the zone's exact offset.
            start=dt.datetime(1,1,1,18,tzinfo=ZoneInfo(zone));end=(start.astimezone(dt.timezone.utc)+dt.timedelta(minutes=90)).astimezone(ZoneInfo(zone))
            expected_start='18:00';expected_end=f'{end.hour:02}:{end.minute:02}'
            context,page=await self.page()
            try:
                await self.login(page);await page.goto(self.args.base+'/lookup')
                await page.get_by_test_id('lookup-reference-input').fill(receipt['reference']);await page.get_by_test_id('lookup-submit').click()
                await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
                start_text=await page.get_by_test_id('reservation-detail').locator('h2').inner_text()
                end_text=await page.locator('dl.detail-list div').filter(has=page.locator('dt',has_text='Ends at')).locator('dd').inner_text()
                key=zone.replace('/','-')
                self.check('historical-'+key+'-start-display',expected_start in start_text,expected_start,start_text)
                self.check('historical-'+key+'-end-display',expected_end in end_text,dict(zone=zone,local_clock=expected_end,exact_wire=receipt['ends_at']),end_text)
                await self.shot(page,'historical-'+key+'-lookup')
            finally:await context.close()
    async def run(self):
        async with async_playwright() as p:
            self.http=await p.request.new_context();self.browser=await p.chromium.launch(headless=True)
            try:await self.historical()
            except Exception as e:self.results.append(dict(requirement_id='HISTORICAL-CASE',passed=False,expected='case completes',observed=str(e)))
            await self.browser.close();await self.http.dispose()
        for n,v in [('assertions',self.results),('browser-actions',self.actions),('http-operations',self.operations),('browser-network',self.network)]: (self.out/(n+'.json')).write_text(json.dumps(v,indent=2))
        result=dict(candidate=self.args.candidate,assertions=len(self.results),failures=sum(not x['passed']for x in self.results),http_operations=len(self.operations),browser_requests=len(self.network),screenshots=len(list(self.out.glob('*.png'))),duration_seconds=time.monotonic()-self.started)
        (self.out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return bool(result['failures'])
def main():
    p=argparse.ArgumentParser()
    for k in ['base','candidate','out']:p.add_argument('--'+k,required=True)
    raise SystemExit(asyncio.run(Historical(p.parse_args()).run()))
if __name__=='__main__':main()
