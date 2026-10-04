"""Independent actual-browser flows. Faults gate real HTTP; no simulated success."""
import argparse
import asyncio
import copy
import json
import time
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

from playwright.async_api import async_playwright, expect
from api import DAY, pair_fixture, safe, fingerprint
from requirements import ROWS
from integer_values import VALUES, loads_exact, number_exact, party_exact, party_lexeme, trace_exact


class BrowserProbe:
    def __init__(self,args):
        self.args=args
        self.out=Path(args.out)
        self.out.mkdir(parents=True,exist_ok=False)
        self.results=[]
        self.actions=[]
        self.operations=[]
        self.network=[]
        self.visual=[]
        self.started=time.monotonic()
        self.requests=[]

    def check(self,key,condition,expected=None,observed=None):
        self.results.append(dict(requirement_id="TK2-"+key,passed=bool(condition),expected=safe(trace_exact(expected)),observed=safe(trace_exact(observed))))

    async def api(self,method,path,body=None,token=None,key=None,base=None,exact=False):
        headers={"Content-Type":"application/json; charset=utf-8"}
        if token:
            headers["Authorization"]="Bearer "+token
        if key:
            headers["Idempotency-Key"]=key
        began=time.monotonic()
        response=await self.http.fetch((base or self.args.base)+path,method=method,headers=headers,data=json.dumps(body) if body is not None else None,timeout=10000 if path.startswith("/_test/") else 5000)
        value=(loads_exact(await response.text()) if exact else await response.json()) if await response.body() else None
        self.operations.append(dict(method=method,path=path,base=base or self.args.base,body=safe(body),key=key,has_token=bool(token),status=response.status,response=safe(trace_exact(value)),duration_seconds=time.monotonic()-began,exact_numeric_decoder=exact))
        return response.status,value

    async def reset(self,f=None):
        self.f=f or pair_fixture()
        status,_=await self.api("POST","/_test/reset",self.f)
        if status!=204:
            raise RuntimeError("Legal browser fixture reset failed: "+str(status))
        self.tokens={}
        for user in self.f["users"]:
            status,value=await self.api("POST","/auth/login",dict(email=user["email"],password=user["password"]))
            if status!=200:
                raise RuntimeError("Seeded login setup failed")
            self.tokens[user["id"]]=value["token"]

    async def page(self,width=1280):
        context=await self.browser.new_context(viewport={"width":width,"height":900 if width>375 else 812})
        page=await context.new_page()
        page.set_default_timeout(5000)
        page.on("request",self.request)
        page.on("console",lambda message:self.actions.append(dict(event="console",type=message.type,text_sha256=fingerprint(message.text))))
        page.on("pageerror",lambda error:self.actions.append(dict(event="pageerror",text=str(error))))
        return context,page

    def request(self,request):
        headers=request.headers
        try:
            body=loads_exact(request.post_data) if request.post_data is not None else None
        except Exception:
            body=None
        operation=dict(method=request.method,url=request.url,body=safe(trace_exact(body)),key=headers.get("idempotency-key"),
                       authorization_sha256=fingerprint(headers["authorization"]) if "authorization" in headers else None,
                       started_monotonic=time.monotonic())
        self.network.append(operation)
        if request.method=="POST" and urlsplit(request.url).path=="/reservations":
            self.requests.append(dict(body=body,key=headers.get("idempotency-key"),authorization=headers.get("authorization"),raw=request.post_data))

    async def visible(self,page,key):
        locator=page.get_by_test_id(key)
        return await locator.count()>0 and await locator.first.is_visible()

    async def text(self,page,key):
        return await page.get_by_test_id(key).inner_text() if await self.visible(page,key) else ""

    async def shot(self,page,name):
        path=self.out/(name+".png")
        await page.screenshot(path=str(path),full_page=True)
        self.actions.append(dict(event="screenshot",name=name,path=str(path),url=page.url,viewport=page.viewport_size))
        return str(path)

    async def login(self,page):
        await page.goto(self.args.base+"/login")
        await page.get_by_test_id("login-email").fill("a@probe.invalid")
        await page.get_by_test_id("login-password").fill("verifier-pass-A")
        await page.get_by_test_id("login-submit").click()
        await expect(page.get_by_test_id("current-user")).to_contain_text("Diner A")

    async def search(self,page,party=2,rid="r",day=DAY):
        await page.goto(self.args.base+"/")
        await page.get_by_test_id("restaurant-select").select_option(rid)
        await page.get_by_test_id("date-input").fill(day)
        await page.get_by_test_id("party-size-input").fill(str(party))
        await page.get_by_test_id("search-button").click()
        await expect(page.get_by_test_id("availability-grid")).to_be_visible()

    def selection(self,seating):
        return (["t0"],2,["Window Alcove"],"slot-t0-18:10") if seating=="single" else (["t1","t0"],6,["Garden Bench","Window Alcove"],"slot-t1+t0-18:10")

    async def open_form(self,page,seating):
        ids,party,labels,cell=self.selection(seating)
        await self.search(page,party=party)
        await page.get_by_test_id(cell).click()
        await expect(page.get_by_test_id("booking-form")).to_be_visible()
        return ids,party,labels

    async def submit(self,page):
        async with page.expect_response(lambda response:urlsplit(response.url).path=="/reservations" and response.request.method=="POST") as pending:
            await page.get_by_test_id("booking-submit").click()
        response=await pending.value
        value=await response.json()
        return response.status,value

    async def routes(self):
        await self.reset()
        context,page=await self.page()
        try:
            for route,key in [("/","search"),("/signup","signup"),("/login","login"),("/lookup","lookup")]:
                response=await page.goto(self.args.base+route)
                self.check("route-"+key,response.status==200)
                self.check("route-html-"+key,"text/html" in response.headers.get("content-type",""))
                await self.shot(page,"route-"+key)
            await self.login(page)
            for route,key in [("/","search"),("/signup","signup"),("/login","login"),("/lookup","lookup")]:
                await page.goto(self.args.base+route)
                self.check("current-user-"+key,"Diner A" in await self.text(page,"current-user"))
        finally:
            await context.close()

    async def auth(self):
        await self.reset()
        context,page=await self.page()
        try:
            await page.goto(self.args.base+"/signup")
            for key in ["signup-email","signup-password","signup-display-name","signup-submit"]:
                self.check("testid-"+key,await self.visible(page,key))
            await page.get_by_test_id("signup-email").fill("new-diner@probe.invalid")
            await page.get_by_test_id("signup-password").fill("new-diner-pass")
            await page.get_by_test_id("signup-display-name").fill("New Diner")
            await page.get_by_test_id("signup-submit").click()
            await expect(page.get_by_test_id("current-user")).to_contain_text("New Diner")
            self.check("signup-flow","New Diner" in await self.text(page,"current-user"))
            self.check("auth-error-absent",await page.get_by_test_id("auth-error").count()==0)
            self.check("testid-logout-button",await self.visible(page,"logout-button"))
            await page.get_by_test_id("logout-button").click()
            await page.goto(self.args.base+"/login")
            for key in ["login-email","login-password","login-submit"]:
                self.check("testid-"+key,await self.visible(page,key))
            await page.get_by_test_id("login-email").fill("a@probe.invalid")
            await page.get_by_test_id("login-password").fill("wrong-password")
            await page.get_by_test_id("login-submit").click()
            await expect(page.get_by_test_id("auth-error")).to_be_visible()
            self.check("auth-error-present",bool(await self.text(page,"auth-error")))
            await self.login(page)
            self.check("login-flow","Diner A" in await self.text(page,"current-user"))
            await page.get_by_test_id("logout-button").click()
            self.check("logout-state",not await self.visible(page,"current-user"))
            await self.search(page)
            await page.get_by_test_id("slot-t0-18:10").click()
            self.check("signed-out-click",urlsplit(page.url).path=="/login" or await self.visible(page,"auth-error"))
        finally:
            await context.close()

    async def grid(self):
        await self.reset()
        await self.api("POST","/reservations",dict(restaurant_id="r",table_id="t0",starts_at_local=DAY+"T18:10",party_size=2),token=self.tokens["u_b"],key="grid-taken")
        context,page=await self.page()
        try:
            await self.login(page)
            await self.search(page)
            for key in ["restaurant-select","date-input","party-size-input","search-button","availability-grid"]:
                self.check("testid-"+key,await self.visible(page,key))
            actual=await page.get_by_test_id("restaurant-select").locator("option").evaluate_all("elements=>elements.map(e=>e.value)")
            self.check("restaurant-values",set(["r","other"]).issubset(actual),["r","other"],actual)
            self.check("date-value",await page.get_by_test_id("date-input").input_value()==DAY)
            self.check("party-input",await page.get_by_test_id("party-size-input").get_attribute("type")=="number")
            status,value=await self.api("GET","/availability?restaurant_id=r&date="+DAY+"&party_size=2")
            queries=[parse_qs(urlsplit(x["url"]).query) for x in self.network if urlsplit(x["url"]).path=="/availability"]
            self.check("search-runs",dict(restaurant_id=["r"],date=[DAY],party_size=["2"]) in queries)
            for slot in value["slots"]:
                for table in self.f["restaurants"][0]["tables"]:
                    key="slot-"+table["id"]+"-"+slot["starts_at_local"][-5:]
                    cell=page.get_by_test_id(key)
                    present=await cell.count()==1
                    self.check("single-cells",present,key)
                    expected=table["id"] in slot["available_table_ids"]
                    observed=await cell.get_attribute("data-available") if present else None
                    self.check("cell-true" if expected else "cell-false",observed==str(expected).lower(),str(expected).lower(),observed)
                for option in slot["available_options"]:
                    if len(option["table_ids"])==2:
                        key="slot-"+"+".join(option["table_ids"])+"-"+slot["starts_at_local"][-5:]
                        self.check("pair-cell-testid",await page.get_by_test_id(key).count()==1,key)
                        self.check("pair-cell-availability",await page.get_by_test_id(key).get_attribute("data-available")=="true")
            # Disabled native buttons cannot be clicked by Playwright; DOM click is an actual no-op event.
            await page.get_by_test_id("slot-t0-18:10").evaluate("e=>e.click()")
            self.check("unavailable-click",not await self.visible(page,"booking-form"))
            await page.get_by_test_id("slot-t1-18:10").click()
            self.check("available-click",await self.visible(page,"booking-form"))
            await self.shot(page,"grid-selected")
            f=pair_fixture()
            f["restaurants"][0]["opening_hours"]=[]
            await self.api("POST","/_test/reset",f)
            await page.get_by_test_id("search-button").click()
            await expect(page.get_by_test_id("no-slots")).to_be_visible()
            self.check("no-slots",await page.get_by_test_id("availability-grid").count()==0 and bool(await self.text(page,"no-slots")))
            await self.shot(page,"grid-empty")
        finally:
            await context.close()

    async def booking(self,seating):
        await self.reset()
        context,page=await self.page()
        try:
            await self.login(page)
            ids,party,labels=await self.open_form(page,seating)
            for key in ["booking-form","booking-summary","booking-party-size","booking-submit"]:
                self.check("testid-"+key,await self.visible(page,key))
            summary=await self.text(page,"booking-summary")
            self.check(seating+"-form-summary",all(label in summary for label in labels) and "18:10" in summary,labels,summary)
            self.check(seating+"-form-party",await page.get_by_test_id("booking-party-size").input_value()==str(party))
            if seating=="pair":
                self.check("pair-cell-opens",await self.visible(page,"booking-form") and all(label in summary for label in labels))
            status,receipt=await self.submit(page)
            await expect(page.get_by_test_id("confirmation")).to_be_visible()
            original=copy.deepcopy(self.requests[-1])
            for key in ["confirmation","confirmation-reference","confirmation-details"]:
                self.check("testid-"+key,await self.visible(page,key))
            self.check(seating+"-form-retained",await self.visible(page,"booking-form"))
            self.check(seating+"-confirmation",status==201 and await self.visible(page,"confirmation"))
            self.check(seating+"-reference-exact",await self.text(page,"confirmation-reference")==receipt["reference"])
            details=await self.text(page,"confirmation-details")
            self.check(seating+"-confirmation-details","Verifier Kitchen" in details and "18:10" in details and all(label in details for label in labels),labels,details)
            if seating=="pair":
                tables=await self.text(page,"confirmation-tables")
                self.check("pair-confirmation-labels",all(label in tables for label in labels),labels,tables)
                self.check("pair-summary-labels",all(label in summary for label in labels))
            else:
                self.check("single-ui-unchanged",await self.visible(page,"slot-t0-18:10"))
            await self.shot(page,seating+"-confirmed")
            status,repeated=await self.submit(page)
            self.check(seating+"-repeat-reference",status==200 and repeated==receipt and await self.text(page,"confirmation-reference")==receipt["reference"])
            self.check(seating+"-repeat-no-error",await page.get_by_test_id("booking-error").count()==0)
            _,records=await self.api("GET","/reservations",token=self.tokens["u_a"])
            self.check(seating+"-repeat-one-record",len(records["reservations"])==1)
            await page.get_by_test_id("booking-party-size").evaluate("e=>e.dispatchEvent(new Event('input',{bubbles:true}))")
            await self.submit(page)
            self.check(seating+"-same-value-request",self.requests[-1]["key"]==original["key"] and self.requests[-1]["body"]==original["body"])
            await page.get_by_test_id("booking-party-size").fill(str(party-1 if party>1 else party+1))
            await self.submit(page)
            self.check(seating+"-edited-request",self.requests[-1]["key"]!=original["key"] and self.requests[-1]["body"]!=original["body"])
        finally:
            await context.close()

    async def race(self,seating):
        await self.reset()
        context,page=await self.page()
        try:
            await self.login(page)
            seen=asyncio.Event()
            release=asyncio.Event()
            delivered=asyncio.Event()
            async def delayed(route):
                query=parse_qs(urlsplit(route.request.url).query)
                if query.get("restaurant_id")==["r"] and query.get("date")==[DAY] and not seen.is_set():
                    response=await route.fetch()
                    seen.set()
                    await release.wait()
                    try:
                        await route.fulfill(response=response)
                        self.actions.append(dict(event="late-search-A-delivered",seating=seating))
                    except Exception as error:
                        self.actions.append(dict(event="late-search-A-cancelled",seating=seating,error=str(error)))
                    finally:
                        delivered.set()
                else:
                    await route.continue_()
            await page.route("**/availability?**",delayed)
            await page.goto(self.args.base+"/")
            await page.get_by_test_id("restaurant-select").select_option("r")
            await page.get_by_test_id("date-input").fill(DAY)
            await page.get_by_test_id("party-size-input").fill("2")
            await page.get_by_test_id("search-button").click()
            await asyncio.wait_for(seen.wait(),5)
            await self.shot(page,seating+"-search-loading")
            await page.get_by_test_id("restaurant-select").select_option("other")
            await page.get_by_test_id("date-input").fill("2035-06-05")
            party=2 if seating=="single" else 6
            await page.get_by_test_id("party-size-input").fill(str(party))
            await page.get_by_test_id("search-button").click()
            cell="slot-other-t0-18:10" if seating=="single" else "slot-other-t1+other-t0-18:10"
            await expect(page.get_by_test_id(cell)).to_be_visible()
            await page.get_by_test_id(cell).click()
            before_grid=await page.get_by_test_id("availability-grid").inner_text()
            before_form=await page.get_by_test_id("booking-form").inner_text()
            before_labels=await page.get_by_test_id("restaurant-select").input_value()
            release.set()
            await asyncio.wait_for(delivered.wait(),5)
            await page.evaluate("()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
            self.check(seating+"-stale-grid",await page.get_by_test_id("availability-grid").inner_text()==before_grid and await page.get_by_test_id(cell).count()==1)
            self.check(seating+"-stale-labels",await page.get_by_test_id("restaurant-select").input_value()==before_labels and "Orchard" in await self.text(page,"booking-summary"))
            self.check(seating+"-stale-form",await page.get_by_test_id("booking-form").inner_text()==before_form and await page.get_by_test_id("booking-party-size").input_value()==str(party))
            await self.shot(page,seating+"-stale-search")
            await page.unroute("**/availability?**",delayed)
            ids,party,_=await self.open_form(page,seating)
            original_summary=await self.text(page,"booking-summary")
            status,_=await self.api("POST","/reservations",dict(restaurant_id="r",table_ids=ids,starts_at_local=DAY+"T18:10",party_size=party),token=self.tokens["u_b"],key="race-competitor")
            if status!=201:
                raise RuntimeError("Actual competitor setup failed")
            before=len([x for x in self.network if urlsplit(x["url"]).path=="/availability"])
            status,receipt=await self.submit(page)
            await expect(page.get_by_test_id("booking-error")).to_be_visible()
            self.check(seating+"-race-error",status==409 and receipt.get("error",{}).get("code")=="table_unavailable" and bool(await self.text(page,"booking-error")))
            await page.wait_for_timeout(100)
            refreshed=[x for x in self.network if urlsplit(x["url"]).path=="/availability"]
            self.check(seating+"-race-refresh",len(refreshed)>before)
            self.check(seating+"-race-form",await self.visible(page,"booking-form"))
            self.check(seating+"-race-inputs",await page.get_by_test_id("booking-party-size").input_value()==str(party) and await self.text(page,"booking-summary")==original_summary)
            self.check(seating+"-race-no-confirmation",not await self.visible(page,"confirmation"))
            await self.shot(page,seating+"-refused")
            alternative="slot-t2-18:10" if seating=="single" else "slot-t3+t2-18:10"
            await page.get_by_test_id(alternative).click()
            self.check(seating+"-race-change-choice",await self.visible(page,"booking-form") and "Cedar Booth" in await self.text(page,"booking-summary"))
        finally:
            if "release" in locals():
                release.set()
            await context.close()

    async def lost(self,seating):
        for phase in ["precommit","postcommit"]:
            await self.reset()
            context,page=await self.page()
            try:
                await self.login(page)
                await self.open_form(page,seating)
                observed={}
                async def drop(route):
                    observed["body"]=route.request.post_data_json
                    observed["key"]=route.request.headers.get("idempotency-key")
                    if phase=="postcommit":
                        response=await route.fetch()
                        observed["receipt"]=await response.json()
                        observed["status"]=response.status
                    await route.abort("connectionfailed")
                await page.route("**/reservations",drop,times=1)
                await page.get_by_test_id("booking-submit").click()
                await expect(page.get_by_test_id("booking-uncertain")).to_be_visible()
                prefix=seating+"-"+phase+"-"
                self.check(prefix+"uncertain",bool(await self.text(page,"booking-uncertain")))
                self.check(prefix+"no-error",await page.get_by_test_id("booking-error").count()==0)
                self.check(prefix+"no-confirmation",not await self.visible(page,"confirmation"))
                await self.shot(page,seating+"-"+phase+"-uncertain")
                status,receipt=await self.submit(page)
                await expect(page.get_by_test_id("confirmation")).to_be_visible()
                current=self.requests[-1]
                self.check(prefix+"same-key",current["key"]==observed["key"])
                self.check(prefix+"same-body",current["body"]==observed["body"])
                original=observed.get("receipt",receipt)
                self.check(prefix+"retry-reference",status==(200 if phase=="postcommit" else 201) and receipt==original and await self.text(page,"confirmation-reference")==original["reference"])
                self.check(prefix+"clear-uncertainty",await page.get_by_test_id("booking-uncertain").count()==0)
                self.check(prefix+"clear-error",await page.get_by_test_id("booking-error").count()==0)
                _,records=await self.api("GET","/reservations",token=self.tokens["u_a"])
                self.check(prefix+"one-record",len(records["reservations"])==1)
                await self.shot(page,seating+"-"+phase+"-recovered")
            finally:
                await context.close()

    async def lookup(self):
        for seating in ["single","pair"]:
            await self.reset()
            ids,party,labels,_=self.selection(seating)
            _,receipt=await self.api("POST","/reservations",dict(restaurant_id="r",table_ids=ids,starts_at_local=DAY+"T18:10",party_size=party),token=self.tokens["u_a"],key="lookup-seed")
            context,page=await self.page()
            try:
                await self.login(page)
                await page.goto(self.args.base+"/lookup")
                for key in ["lookup-reference-input","lookup-submit"]:
                    self.check("testid-"+key,await self.visible(page,key))
                await page.get_by_test_id("lookup-reference-input").fill(receipt["reference"])
                await page.get_by_test_id("lookup-submit").click()
                await expect(page.get_by_test_id("reservation-detail")).to_be_visible()
                for key in ["reservation-detail","reservation-status"]:
                    self.check("testid-"+key,await self.visible(page,key))
                self.check("lookup-found",await self.visible(page,"reservation-detail"))
                self.check("lookup-confirmed-exact",await self.text(page,"reservation-status")=="confirmed")
                self.check("lookup-cancel-button",await self.visible(page,"reservation-cancel-button"))
                if seating=="pair":
                    tables=await self.text(page,"reservation-tables")
                    self.check("pair-lookup-labels",all(label in tables for label in labels))
                await page.get_by_test_id("reservation-cancel-button").click()
                await expect(page.get_by_test_id("reservation-status")).to_have_text("cancelled")
                self.check("lookup-cancelled-exact",await self.text(page,"reservation-status")=="cancelled")
                self.check("lookup-cancel-absent",await page.get_by_test_id("reservation-cancel-button").count()==0)
                _,value=await self.api("GET","/availability?restaurant_id=r&date="+DAY+"&party_size="+str(party))
                self.check("lookup-cancel",any(option["table_ids"]==ids for option in value["slots"][0]["available_options"]))
                await self.shot(page,seating+"-lookup-cancelled")
                _,private=await self.api("POST","/reservations",dict(restaurant_id="r",table_ids=ids,starts_at_local=DAY+"T18:10",party_size=party),token=self.tokens["u_b"],key="lookup-private")
                for ref in ["NOBOOK01",private["reference"]]:
                    await page.get_by_test_id("lookup-reference-input").fill(ref)
                    await page.get_by_test_id("lookup-submit").click()
                    await expect(page.get_by_test_id("reservation-error")).to_be_visible()
                    self.check("lookup-not-found",bool(await self.text(page,"reservation-error")) and not await self.visible(page,"reservation-detail"))
            finally:
                await context.close()
        f=pair_fixture()
        f["restaurants"][0]["cancellation_cutoff_minutes"]=10**18
        await self.reset(f)
        _,receipt=await self.api("POST","/reservations",dict(restaurant_id="r",table_id="t0",starts_at_local=DAY+"T18:10",party_size=2),token=self.tokens["u_a"],key="lookup-cutoff")
        context,page=await self.page()
        try:
            await self.login(page)
            await page.goto(self.args.base+"/lookup")
            await page.get_by_test_id("lookup-reference-input").fill(receipt["reference"])
            await page.get_by_test_id("lookup-submit").click()
            await expect(page.get_by_test_id("reservation-cancel-button")).to_be_visible()
            await page.get_by_test_id("reservation-cancel-button").click()
            await expect(page.get_by_test_id("reservation-error")).to_be_visible()
            self.check("lookup-cutoff",bool(await self.text(page,"reservation-error")) and await self.text(page,"reservation-status")=="confirmed")
        finally:
            await context.close()

    async def visual_case(self):
        for width in [375,1280]:
            await self.reset()
            context,page=await self.page(width)
            try:
                for route,name in [("/","search"),("/signup","signup"),("/login","login"),("/lookup","lookup")]:
                    await page.goto(self.args.base+route)
                    if route=="/":
                        await self.search(page)
                    image=await self.shot(page,f"visual-{width}-{name}")
                    metrics=await page.evaluate("""()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,
                        inputs:[...document.querySelectorAll('input:not([type=hidden]),select,textarea')].map(e=>({id:e.id,testid:e.dataset.testid,type:e.type,labels:[...(e.labels||[])].map(l=>({text:l.innerText,visible:!!(l.offsetWidth||l.offsetHeight)})),aria:e.getAttribute('aria-label')})),
                        text:[...document.querySelectorAll('label,button,a,h1,h2,p')].filter(e=>e.offsetWidth&&e.offsetHeight).map(e=>({text:e.innerText,color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor,font:getComputedStyle(e).fontSize}))})""")
                    self.check(f"visual-{width}-{name}-no-scroll",metrics["scroll"]<=metrics["client"],metrics["client"],metrics["scroll"])
                    labelled=all(any(label["visible"] and label["text"].strip() for label in item["labels"]) for item in metrics["inputs"])
                    self.check(f"visual-{width}-{name}-labels",bool(metrics["inputs"]) and labelled,"every input has a visible label",metrics["inputs"])
                    await page.locator("body").click(position={"x":1,"y":1})
                    await page.keyboard.press("Tab")
                    focus=await page.evaluate("""()=>{let e=document.activeElement,s=getComputedStyle(e);return {tag:e.tagName,text:e.innerText,testid:e.dataset.testid,outline:s.outline,shadow:s.boxShadow,border:s.border,bounds:e.getBoundingClientRect().toJSON()}}""")
                    focused=await self.shot(page,f"visual-{width}-{name}-keyboard")
                    self.visual.append(dict(route=route,width=width,image=image,keyboard_image=focused,metrics=metrics,focus=focus,
                                            pending_review=[f"TK2-visual-{width}-{name}-usable",f"TK2-visual-{width}-{name}-focus",f"TK2-visual-{width}-{name}-contrast"]))
                await self.login(page)
                await self.open_form(page,"pair")
                await self.shot(page,f"visual-{width}-pair-form")
                await self.submit(page)
                await self.shot(page,f"visual-{width}-pair-success")
            finally:
                await context.close()
        external=[x["url"] for x in self.network if urlsplit(x["url"]).netloc not in {urlsplit(self.args.base).netloc} and not x["url"].startswith(("data:","blob:"))]
        self.check("visual-offline-assets",not external,"all browser resources from packaged service",external)

    async def integer_case(self):
        for seating in ["single","pair"]:
            for label,digits in VALUES:
                prefix="integer-"+seating+"-"+label+"-"
                value=int(digits)
                f=pair_fixture()
                restaurant=f["restaurants"][0]
                if seating=="single":
                    capacities=[value,value-1,1,1]
                    restaurant["combinable"]=[]
                    ids=["t0"]
                    cell="slot-t0-18:10"
                else:
                    capacities=[value//2,value-value//2,1,1]
                    restaurant["combinable"]=[["t1","t0"]]
                    ids=["t1","t0"]
                    cell="slot-t1+t0-18:10"
                for table,capacity in zip(restaurant["tables"],capacities):
                    table["capacity"]=capacity
                try:
                    await self.reset(f)
                except Exception as error:
                    self.check(prefix+"reset",False,204,str(error))
                    continue
                self.check(prefix+"reset",True,204,204)
                status,available=await self.api("GET","/availability?restaurant_id=r&date="+DAY+"&party_size="+digits,exact=True)
                slots=available.get("slots",[]) if isinstance(available,dict) else []
                offered=status==200 and bool(slots) and any(option["table_ids"]==ids for option in slots[0].get("available_options",[]))
                self.check(prefix+"api-control",offered,"fitting exact-party option",available)
                context,page=await self.page()
                try:
                    await self.login(page)
                    await page.goto(self.args.base+"/")
                    await page.get_by_test_id("restaurant-select").select_option("r")
                    await page.get_by_test_id("date-input").fill(DAY)
                    await page.get_by_test_id("party-size-input").fill(digits)
                    self.check(prefix+"search-input",await page.get_by_test_id("party-size-input").input_value()==digits,digits,await page.get_by_test_id("party-size-input").input_value())
                    before=len(self.network)
                    async with page.expect_response(lambda response:urlsplit(response.url).path=="/availability") as pending:
                        await page.get_by_test_id("search-button").click()
                    response=await pending.value
                    queries=[parse_qs(urlsplit(item["url"]).query).get("party_size",[]) for item in self.network[before:] if urlsplit(item["url"]).path=="/availability"]
                    self.check(prefix+"query",bool(queries) and all(query==[digits] for query in queries),[digits],queries)
                    await self.shot(page,prefix+"searched")
                    ready=response.status==200 and await page.get_by_test_id(cell).count()==1 and await page.get_by_test_id(cell).get_attribute("data-available")=="true"
                    self.check(prefix+"grid",ready,dict(status=200,cell=cell,available="true"),dict(status=response.status,cell_count=await page.get_by_test_id(cell).count()))
                    if not ready:
                        continue
                    await page.get_by_test_id(cell).click()
                    await expect(page.get_by_test_id("booking-form")).to_be_visible()
                    prefilled=await page.get_by_test_id("booking-party-size").input_value()
                    self.check(prefix+"prefill",prefilled==digits,digits,prefilled)
                    status,_=await self.submit(page)
                    request=self.requests[-1]
                    self.check(prefix+"body",party_exact(request["raw"],digits),digits,party_lexeme(request["raw"]))
                    self.actions.append(dict(event="exact-party-wire",case=prefix,query_values=queries,body_party_lexeme=party_lexeme(request["raw"]),body_sha256=fingerprint(request["raw"]),key=request["key"]))
                    # Decode raw response text in Python: never let a browser/driver Number round the oracle.
                    _,records=await self.api("GET","/reservations",token=self.tokens["u_a"],exact=True)
                    rows=records.get("reservations",[])
                    receipt=rows[0] if len(rows)==1 else {}
                    self.check(prefix+"success",status==201 and bool(receipt.get("reference")) and await self.text(page,"confirmation-reference")==receipt.get("reference"),201,status)
                    lookup_status,stored=await self.api("GET","/reservations/"+receipt["reference"],token=self.tokens["u_a"],exact=True) if receipt.get("reference") else (0,{})
                    self.check(prefix+"stored",lookup_status==200 and number_exact(stored.get("party_size"),digits),digits,stored.get("party_size"))
                    repeated_status,repeated=await self.submit(page)
                    current=self.requests[-1]
                    self.check(prefix+"repeat-identity",current["key"]==request["key"] and loads_exact(current["raw"])==loads_exact(request["raw"]))
                    self.check(prefix+"repeat-reference",repeated_status==200 and repeated.get("reference")==receipt.get("reference") and await self.text(page,"confirmation-reference")==receipt.get("reference"))
                    _,records=await self.api("GET","/reservations",token=self.tokens["u_a"])
                    self.check(prefix+"one-record",len(records.get("reservations",[]))==1)
                    await self.shot(page,prefix+"confirmed")
                except Exception as error:
                    self.results.append(dict(requirement_id="BROWSER-CASE-"+prefix,passed=False,expected="integer boundary case completes",observed=str(error)))
                finally:
                    await context.close()

    async def run(self):
        async with async_playwright() as runtime:
            self.http=await runtime.request.new_context()
            self.browser=await runtime.chromium.launch(headless=True)
            cases=dict(routes=self.routes,auth=self.auth,grid=self.grid,lookup=self.lookup,visual=self.visual_case,**{"integer-boundary":self.integer_case})
            for seating in ["single","pair"]:
                cases["booking-"+seating]=lambda seating=seating:self.booking(seating)
                cases["race-"+seating]=lambda seating=seating:self.race(seating)
                cases["lost-"+seating]=lambda seating=seating:self.lost(seating)
            selected=list(cases) if self.args.case=="all" else self.args.case.split(",")
            for case in selected:
                try:
                    await cases[case]()
                except Exception as error:
                    self.results.append(dict(requirement_id="BROWSER-CASE-"+case,passed=False,expected="case completes",observed=str(error)))
            await self.browser.close()
            await self.http.dispose()
        (self.out/"assertions.json").write_text(json.dumps(self.results,indent=2))
        (self.out/"browser-actions.json").write_text(json.dumps(self.actions,indent=2))
        (self.out/"http-operations.json").write_text(json.dumps(self.operations,indent=2))
        (self.out/"browser-network.json").write_text(json.dumps(self.network,indent=2))
        (self.out/"visual-review-pending.json").write_text(json.dumps(self.visual,indent=2))
        summary=dict(stage=2,candidate=self.args.candidate,source="Actual independent browser interactions; visual judgment remains pending screenshot review",
                     assertions=len(self.results),failures=sum(not x["passed"] for x in self.results),http_operations=len(self.operations),browser_requests=len(self.network),screenshots=sum(x.get("event")=="screenshot" for x in self.actions),
                     duration_seconds=time.monotonic()-self.started)
        (self.out/"summary.json").write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary))
        return summary["failures"]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",required=True)
    parser.add_argument("--candidate",required=True)
    parser.add_argument("--out",required=True)
    parser.add_argument("--case",default="all")
    args=parser.parse_args()
    if len(args.candidate)!=40 or any(x not in "0123456789abcdef" for x in args.candidate):
        parser.error("A full named committed candidate is required.")
    raise SystemExit(bool(asyncio.run(BrowserProbe(args).run())))


if __name__=="__main__":
    main()
