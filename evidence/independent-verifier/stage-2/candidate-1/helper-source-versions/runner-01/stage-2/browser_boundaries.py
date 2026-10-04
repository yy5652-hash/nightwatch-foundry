"""Actual displayed integers and DOM/rendered status spellings, with exact HTTP controls."""
import argparse
import asyncio
import re
from playwright.async_api import async_playwright, expect
from browser import BrowserProbe
from api import pair_fixture, DAY

class Boundaries(BrowserProbe):
    async def boundaries(self):
        values=[('unsafe','9007199254740993'),('scientific','1000000000000000000001'),('overflow','1'+'0'*399+'1')]
        for seating in ['single','pair']:
            for label,digits in values:
                prefix='integer-'+seating+'-'+label+'-'
                n=int(digits); f=pair_fixture(); r=f['restaurants'][0]
                caps=[n,n-1,1,1] if seating=='single' else [n//2,n-n//2,1,1]
                r['combinable']=[] if seating=='single' else [['t1','t0']]
                ids=['t0'] if seating=='single' else ['t1','t0']
                cell='slot-'+'+'.join(ids)+'-18:10'
                for t,cap in zip(r['tables'],caps): t['capacity']=cap
                await self.reset(f)
                status,available=await self.api('GET','/availability?restaurant_id=r&date='+DAY+'&party_size='+digits,exact=True)
                self.check(prefix+'reset',True,204,204)
                self.check(prefix+'api-control',status==200 and any(o['table_ids']==ids and o['capacity']==n for o in available['slots'][0]['available_options']),n,available['slots'][0]['available_options'])
                context,page=await self.page()
                try:
                    await self.login(page); await page.goto(self.args.base+'/')
                    await page.get_by_test_id('restaurant-select').select_option('r')
                    await page.get_by_test_id('date-input').fill(DAY)
                    await page.get_by_test_id('party-size-input').fill(digits)
                    entered=await page.get_by_test_id('party-size-input').input_value()
                    self.check(prefix+'search-input',entered==digits,digits,entered)
                    if entered!=digits:
                        await page.get_by_test_id('search-button').click()
                        self.actions.append(dict(event='unrepresentable-native-control',case=prefix,requested=digits,input_value=entered,search_error=await self.text(page,'search-error')))
                        await self.shot(page,prefix+'input-cleared')
                        continue
                    await page.get_by_test_id('search-button').click()
                    await expect(page.get_by_test_id(cell)).to_be_visible()
                    text=await page.get_by_test_id(cell).inner_text()
                    capacity=re.search(r'(\S+) seats',text)
                    observed=capacity.group(1) if capacity else None
                    self.check(prefix+'capacity-display',observed==digits,digits,observed)
                    await page.get_by_test_id(cell).click()
                    await self.submit(page)
                    ref=await self.text(page,'confirmation-reference')
                    await self.shot(page,prefix+'capacity-confirmed')
                    await page.goto(self.args.base+'/lookup')
                    await page.get_by_test_id('lookup-reference-input').fill(ref)
                    await page.get_by_test_id('lookup-submit').click()
                    await expect(page.get_by_test_id('reservation-detail')).to_be_visible()
                    guest=await page.locator('dl.detail-list div').filter(has=page.locator('dt',has_text='Guests')).locator('dd').inner_text()
                    self.check(prefix+'lookup-display',guest==digits,digits,guest)
                    status=page.get_by_test_id('reservation-status')
                    both=dict(textContent=await status.text_content(),innerText=await status.inner_text(),textTransform=await status.evaluate('(e)=>getComputedStyle(e).textTransform'))
                    self.actions.append(dict(event='exact-status-spellings',case=prefix,observed=both))
                    self.check('status-dom-confirmed',both['textContent']=='confirmed','confirmed',both)
                    await self.shot(page,prefix+'lookup')
                    await page.get_by_test_id('reservation-cancel-button').click()
                    await expect(status).to_have_text('cancelled')
                    both=dict(textContent=await status.text_content(),innerText=await status.inner_text(),textTransform=await status.evaluate('(e)=>getComputedStyle(e).textTransform'))
                    self.actions.append(dict(event='exact-status-spellings-cancelled',case=prefix,observed=both))
                    self.check('status-dom-cancelled',both['textContent']=='cancelled','cancelled',both)
                finally: await context.close()

    async def run(self):
        async with async_playwright() as runtime:
            self.http=await runtime.request.new_context(); self.browser=await runtime.chromium.launch(headless=True)
            try: await self.boundaries()
            except Exception as error:
                self.results.append(dict(requirement_id='BROWSER-CASE-boundaries',passed=False,expected='boundary case completes',observed=str(error)))
            await self.browser.close(); await self.http.dispose()
        import json,time
        for name,value in [('assertions',self.results),('browser-actions',self.actions),('http-operations',self.operations),('browser-network',self.network)]:
            (self.out/(name+'.json')).write_text(json.dumps(value,indent=2))
        summary=dict(stage=2,candidate=self.args.candidate,assertions=len(self.results),failures=sum(not x['passed'] for x in self.results),
            http_operations=len(self.operations),browser_requests=len(self.network),screenshots=len(list(self.out.glob('*.png'))),duration_seconds=time.monotonic()-self.started)
        (self.out/'summary.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary)); return bool(summary['failures'])

def main():
    p=argparse.ArgumentParser()
    for name in ['base','candidate','out']: p.add_argument('--'+name,required=True)
    a=p.parse_args(); raise SystemExit(asyncio.run(Boundaries(a).run()))

if __name__=='__main__': main()
