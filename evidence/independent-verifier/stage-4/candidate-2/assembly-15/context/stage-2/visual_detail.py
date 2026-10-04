"""Measured text contrast and genuine keyboard/state captures at both required widths."""
import argparse,asyncio,json,time
from playwright.async_api import async_playwright,expect
from browser import BrowserProbe
from api import pair_fixture,DAY

STYLE="""()=>{
 const rgb=s=>(s.match(/[\\d.]+/g)||[]).map(Number);
 const bg=e=>{let stack=[];for(let x=e;x;x=x.parentElement)stack.push(rgb(getComputedStyle(x).backgroundColor));let c=[255,255,255];for(let x of stack.reverse()){let a=x.length===4?x[3]:1;if(x.length>=3)c=c.map((v,i)=>x[i]*a+v*(1-a));}return c;};
 const lum=c=>c.map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);
 let out=[],walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT),n;
 while(n=walker.nextNode()){
  let e=n.parentElement,s=getComputedStyle(e),r=e.getBoundingClientRect(),text=n.textContent.trim();
  if(!text||!r.width||!r.height||s.visibility!=='visible'||s.display==='none'||s.color==='rgba(0, 0, 0, 0)'||e.closest('button:disabled'))continue;
  let color=rgb(s.color),back=bg(e),a=color.length===4?color[3]:1; color=color.slice(0,3).map((x,i)=>x*a+back[i]*(1-a));
  let first=lum(color),second=lum(back),ratio=(Math.max(first,second)+.05)/(Math.min(first,second)+.05);
  let size=parseFloat(s.fontSize),large=size>=24||(size>=18.666&&Number(s.fontWeight)>=700);
  out.push({text:text.slice(0,160),tag:e.tagName,testid:e.dataset.testid,color,background:back,size,weight:s.fontWeight,ratio,minimum:large?3:4.5});
 }
 return {width:innerWidth,scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,text:out};
}"""
class Visual(BrowserProbe):
    async def capture(self,page,name,width):
        image=await self.shot(page,name)
        metrics=await page.evaluate(STYLE)
        failed=[x for x in metrics['text'] if x['ratio']<x['minimum']]
        self.actions.append(dict(event='contrast-and-overflow',name=name,image=image,metrics=metrics))
        self.check(name+'-text-contrast',not failed,'normal 4.5:1; large 3:1; disabled text excluded',failed)
        self.check(name+'-no-scroll',metrics['scroll']<=metrics['client'],metrics['client'],metrics['scroll'])
    async def flows(self):
        for width in [375,1280]:
            await self.reset()
            context,page=await self.page(width)
            try:
                for route,name in [('/','search'),('/signup','signup'),('/login','login'),('/lookup','lookup')]:
                    await page.goto(self.args.base+route)
                    if route=='/': await self.search(page)
                    await self.capture(page,f'visual-{width}-{name}',width)
                await self.login(page);await self.search(page,party=6)
                await self.capture(page,f'states-{width}-available-unavailable',width)
                cell=page.get_by_test_id('slot-t1+t0-18:10')
                await cell.focus();await page.keyboard.press('Enter')
                await expect(page.get_by_test_id('booking-form')).to_be_visible()
                active=await page.evaluate('()=>document.activeElement.dataset.testid')
                self.check(f'keyboard-{width}-selection-focus',active=='booking-party-size','booking-party-size',active)
                await self.capture(page,f'states-{width}-selected',width)
                async def committed_loss(route):
                    response=await route.fetch();self.actions.append(dict(event='real-commit-before-drop',width=width,status=response.status));await route.abort('connectionfailed')
                await page.route('**/reservations',committed_loss,times=1)
                await page.keyboard.press('Tab');await page.keyboard.press('Enter')
                await expect(page.get_by_test_id('booking-uncertain')).to_be_visible()
                await self.capture(page,f'states-{width}-uncertain',width)
                await page.get_by_test_id('booking-submit').focus();await page.keyboard.press('Enter')
                await expect(page.get_by_test_id('confirmation')).to_be_visible()
                self.check(f'keyboard-{width}-recovery',bool(await self.text(page,'confirmation-reference')))
                await self.capture(page,f'states-{width}-successful',width)
            finally:await context.close()
            f=pair_fixture();f['restaurants'][0]['opening_hours']=[h for h in f['restaurants'][0]['opening_hours'] if h['weekday']=='mon']
            await self.reset(f);context,page=await self.page(width)
            try:
                await self.login(page);await self.open_form(page,'pair')
                await self.api('POST','/reservations',dict(restaurant_id='r',table_ids=['t1','t0'],starts_at_local=DAY+'T18:10',party_size=6),token=self.tokens['u_b'],key='visual-compete')
                await self.submit(page)
                await expect(page.get_by_test_id('booking-error')).to_be_visible()
                await self.capture(page,f'states-{width}-refused',width)
                hold=asyncio.Event();started=asyncio.Event()
                async def delayed(route):
                    response=await route.fetch();started.set();await hold.wait();await route.fulfill(response=response)
                await page.route('**/availability?*',delayed,times=1)
                await page.get_by_test_id('date-input').fill('2035-06-05')
                await page.get_by_test_id('search-button').click();await started.wait()
                await self.capture(page,f'states-{width}-loading',width)
                hold.set();await expect(page.get_by_test_id('no-slots')).to_be_visible()
                await self.capture(page,f'states-{width}-empty',width)
            finally:await context.close()
    async def run(self):
        async with async_playwright() as p:
            self.http=await p.request.new_context();self.browser=await p.chromium.launch(headless=True)
            try:await self.flows()
            except Exception as error:self.results.append(dict(requirement_id='VISUAL-CASE',passed=False,expected='case completes',observed=str(error)))
            await self.browser.close();await self.http.dispose()
        for name,value in [('assertions',self.results),('browser-actions',self.actions),('http-operations',self.operations),('browser-network',self.network)]:
            (self.out/(name+'.json')).write_text(json.dumps(value,indent=2))
        summary=dict(candidate=self.args.candidate,assertions=len(self.results),failures=sum(not x['passed']for x in self.results),http_operations=len(self.operations),browser_requests=len(self.network),screenshots=len(list(self.out.glob('*.png'))),duration_seconds=time.monotonic()-self.started)
        (self.out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary));return bool(summary['failures'])
def main():
    p=argparse.ArgumentParser()
    for k in ['base','candidate','out']:p.add_argument('--'+k,required=True)
    a=p.parse_args();raise SystemExit(asyncio.run(Visual(a).run()))
if __name__=='__main__':main()
