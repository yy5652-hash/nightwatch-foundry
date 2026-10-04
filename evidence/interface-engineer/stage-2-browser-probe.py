"""Original specification-derived black-box browser/integration diagnostics.

Run inside the unchanged official runner image. Credentials remain in memory.
The race trace uses controlled events, not probabilistic sleeps.
"""
import asyncio
import copy
import json
import os
import time
import traceback
from pathlib import Path
from playwright.async_api import async_playwright, expect

BASE = os.environ["S2_BASE"]
LEGACY = os.environ["S1_BASE"]
OUT = Path(os.environ.get("PROBE_OUT", "/out"))
DATE = "2032-06-17"
REPORT = {"seed": 20261004, "candidate": os.environ["CANDIDATE"], "scenarios": [], "trace": [], "assertions": 0}
FIXTURE = {
    "users": [{"id": "u_ada", "email": "ada@example.test", "password": "correct horse", "display_name": "Ada"},
              {"id": "u_ben", "email": "ben@example.test", "password": "correct horse", "display_name": "Ben"}],
    "restaurants": [{"id": "r_garden", "name": "Garden Room", "timezone": "Europe/Berlin", "slot_minutes": 30,
        "reservation_duration_minutes": 60, "cancellation_cutoff_minutes": 0,
        "opening_hours": [{"weekday": day, "opens": "18:00", "closes": "21:00"} for day in ["mon", "tue", "wed", "thu", "fri", "sat"]],
        "tables": [{"id": "t_window", "label": "Window", "capacity": 2}, {"id": "t_garden", "label": "Garden", "capacity": 4}, {"id": "t_corner", "label": "Corner", "capacity": 4}],
        "combinable": [["t_garden", "t_window"], ["t_window", "t_corner"]]},
        {"id": "r_harbor", "name": "Harbor House", "timezone": "America/New_York", "slot_minutes": 30,
        "reservation_duration_minutes": 60, "cancellation_cutoff_minutes": 0,
        "opening_hours": [{"weekday": day, "opens": "19:00", "closes": "21:00"} for day in ["mon", "tue", "wed", "thu", "fri", "sat"]],
        "tables": [{"id": "t_booth", "label": "Harbor booth", "capacity": 6}], "combinable": []}],
    "reservations": [],
}

def check(condition, description):
    REPORT["assertions"] += 1
    if not condition:
        raise AssertionError(description)

def tid(page, name):
    return page.get_by_test_id(name)

async def request(context, base, path, method="GET", data=None, token=None, key=None, raw=None):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token: headers["Authorization"] = "Bearer " + token
    if key: headers["Idempotency-Key"] = key
    response = await context.request.fetch(base + path, method=method, headers=headers, data=raw if raw is not None else data, timeout=10000 if path.startswith('/_test/') else 5000)
    value = None if response.status == 204 else await response.json()
    return response.status, value

async def reset(context, base=BASE, legacy=False):
    fixture = copy.deepcopy(FIXTURE)
    if legacy:
        for restaurant in fixture["restaurants"]: restaurant.pop("combinable")
    status, _ = await request(context, base, "/_test/reset", "POST", fixture)
    check(status == 204, "fixture reset")

async def login(page, name="ada"):
    await page.goto(BASE + "/login")
    await tid(page, "login-email").fill(name + "@example.test")
    await tid(page, "login-password").fill("correct horse")
    await tid(page, "login-submit").click()
    await expect(tid(page, "current-user")).to_have_text(name.capitalize())
    REPORT["assertions"] += 1

async def search(page, restaurant="r_garden", party="2", date=DATE):
    await expect(tid(page, "restaurant-select")).to_be_enabled()
    await tid(page, "restaurant-select").select_option(restaurant)
    await tid(page, "date-input").fill(date)
    await tid(page, "party-size-input").fill(party)
    await tid(page, "search-button").click()
    await expect(tid(page, "availability-grid")).to_be_visible()
    REPORT["assertions"] += 1

async def open_booking(page, tables="t_window", start="18:00"):
    await tid(page, f"slot-{tables}-{start}").click()
    await expect(tid(page, "booking-form")).to_be_visible()
    REPORT["assertions"] += 1

async def confirmed(page):
    await expect(tid(page, "confirmation-reference")).to_be_visible()
    reference = await tid(page, "confirmation-reference").inner_text()
    import re
    check(bool(re.fullmatch(r"[A-Z0-9]{6,12}", reference)), "exact reference text")
    check(await tid(page, "booking-error").count() == 0, "no false refusal")
    check(await tid(page, "booking-uncertain").count() == 0, "uncertainty removed")
    return reference

async def screenshots(page, prefix):
    for width, height, suffix in [(1440, 1000, "desktop"), (375, 812, "mobile")]:
        await page.set_viewport_size({"width": width, "height": height})
        check(await page.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"no horizontal page scroll at {width}")
        await page.screenshot(path=str(OUT / f"{prefix}-{suffix}.png"), full_page=True)

async def scenario(name, callback, browser):
    started = time.perf_counter()
    context = await browser.new_context(viewport={"width": 1440, "height": 1000},timezone_id='Pacific/Honolulu' if name.startswith('local-end-') else 'UTC')
    page = await context.new_page()
    errors=[]
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        await callback(context, page)
        check(not errors, "no uncaught browser errors: " + repr(errors))
        REPORT["scenarios"].append({"name": name, "verdict": "PASS", "seconds": round(time.perf_counter()-started, 3)})
    except Exception:
        REPORT["scenarios"].append({"name": name, "verdict": "FAIL", "seconds": round(time.perf_counter()-started, 3), "error": traceback.format_exc()})
        await page.screenshot(path=str(OUT / f"failure-{name}.png"), full_page=True)
    finally:
        await context.close()

async def transport(context, page):
    await reset(context)
    for path in ["/", "/signup", "/login", "/lookup"]:
        response=await context.request.get(BASE+path)
        check(response.status==200, "direct screen: "+path)
        check(response.headers["content-type"]=="text/html; charset=utf-8", "HTML content type")
        check('src="/assets/app.js"' in await response.text(), "local script")
    for path, content_type in [("/assets/app.js", "text/javascript; charset=utf-8"),("/assets/app.css", "text/css; charset=utf-8")]:
        response=await context.request.get(BASE+path)
        check(response.status==200 and response.headers["content-type"]==content_type, "offline asset: "+path)
    response=await context.request.post(BASE+"/reservations",data='{"party_size":NaN}',headers={"Content-Type":"application/json"})
    check(response.status==400 and (await response.json())["error"]["code"]=="malformed_request", "strict JSON precedes auth")
    response=await context.request.post(BASE+"/auth/signup",data='[]',headers={"Content-Type":"application/json"})
    check(response.status==400, "nonobject refusal")
    response=await context.request.post(BASE+"/_test/reset",data=FIXTURE)
    check(response.status==204 and await response.body()==b"", "empty reset body")
    await page.goto(BASE+"/")
    await search(page)
    check(await tid(page,"current-user").count()==0, "public browse before sign in")
    await tid(page,"slot-t_window-18:00").click()
    await expect(tid(page,"auth-error")).to_be_visible()
    check(await tid(page,"booking-form").count()==0, "signed out choice does not book")
    await screenshots(page,"public-search")

async def auth_keyboard(context,page):
    await reset(context)
    await page.goto(BASE+"/signup")
    for id_ in ["signup-email","signup-password","signup-display-name"]:
        check(bool(await tid(page,id_).evaluate("element=>element.labels.length")), "visible input label: "+id_)
    await tid(page,"signup-display-name").fill("Riley")
    await tid(page,"signup-email").fill("riley@example.test")
    await tid(page,"signup-password").fill("short")
    await tid(page,"signup-submit").click()
    await expect(tid(page,"auth-error")).to_be_visible()
    await tid(page,"signup-password").fill("correct horse")
    await tid(page,"signup-submit").click()
    await expect(tid(page,"current-user")).to_have_text("Riley")
    check(await tid(page,"auth-error").count()==0, "successful auth clears error")
    for route in ["/lookup","/login","/signup","/"]:
        await page.goto(BASE+route)
        await expect(tid(page,"current-user")).to_have_text("Riley")
        REPORT["assertions"]+=1
    await search(page)
    await tid(page,"slot-t_window-18:00").focus()
    await page.keyboard.press("Enter")
    await expect(tid(page,"booking-party-size")).to_be_focused()
    check(await tid(page,"booking-party-size").evaluate("element=>getComputedStyle(element).outlineStyle")!="none", "visible keyboard focus")
    await screenshots(page,"keyboard-booking")
    await tid(page,"slot-t_window-19:00").focus()
    await page.keyboard.press("Enter")
    await expect(tid(page,"booking-party-size")).to_be_focused()
    await page.keyboard.press("Tab")
    await expect(tid(page,"booking-submit")).to_be_focused()
    await page.keyboard.press("Enter")
    await confirmed(page)
    check(await page.evaluate("innerWidth")==375,"mobile keyboard flow viewport")
    await page.screenshot(path=str(OUT/"mobile-keyboard-confirmed.png"),full_page=True)
    await tid(page,"logout-button").click()
    check(await tid(page,"current-user").count()==0 and await tid(page,"booking-form").count()==0, "logout clears identity and private form")

async def ordinary(context,page):
    await reset(context);await login(page);await search(page)
    await open_booking(page)
    writes=[]
    page.on("request",lambda req: writes.append({"key":req.headers.get("idempotency-key"),"body":req.post_data}) if req.method=="POST" and req.url==BASE+"/reservations" else None)
    await tid(page,"booking-submit").click();reference=await confirmed(page)
    check("Window" in await tid(page,"confirmation-details").inner_text(), "human single table label")
    check("18:00" in await tid(page,"booking-summary").inner_text(), "local selection time")
    check(await tid(page,"booking-summary").locator("time").get_attribute("datetime")==DATE+"T18:00","original local datetime retained without request changes")
    await tid(page,"booking-submit").click();check(await confirmed(page)==reference, "unchanged submit exact original reference")
    check(len(writes)==2 and writes[0]==writes[1], "same body and key after success")
    body=json.loads(writes[0]["body"])
    check("table_id" in body and "table_ids" not in body, "legacy single request shape retained")
    await screenshots(page,"single-confirmation")
    await page.get_by_role("link",name="View or cancel reservation").click()
    await tid(page,"lookup-submit").click()
    await expect(tid(page,"reservation-status")).to_have_text("confirmed")
    check("Window" in await tid(page,"reservation-tables").inner_text(), "lookup human label")
    await tid(page,"reservation-cancel-button").click()
    await expect(tid(page,"reservation-status")).to_have_text("cancelled")
    check(await tid(page,"reservation-cancel-button").count()==0, "cancel button absent once cancelled")
    await screenshots(page,"cancelled-lookup")
    REPORT["trace"].append({"scenario":"ordinary", "writes":writes,"reference":reference})

async def lookup_status_exact(context,page):
    await reset(context);await login(page);await search(page);await open_booking(page)
    await tid(page,'booking-submit').click();reference=await confirmed(page)
    await page.goto(BASE+'/lookup')
    await tid(page,'lookup-reference-input').fill(reference);await tid(page,'lookup-submit').click()
    observations=[]
    for status in ['confirmed','cancelled']:
        if status=='cancelled':await tid(page,'reservation-cancel-button').click()
        await expect(tid(page,'reservation-status')).to_have_text(status)
        for width,height,suffix in [(1440,1000,'desktop'),(375,812,'mobile')]:
            await page.set_viewport_size({'width':width,'height':height})
            element=tid(page,'reservation-status')
            observations.append({'status':status,'width':width,'textContent':await element.text_content(),
                'innerText':await element.inner_text(),'text_transform':await element.evaluate('element=>getComputedStyle(element).textTransform')})
            check(await page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'status page no horizontal scrolling')
            await page.screenshot(path=str(OUT/f'exact-status-{status}-{suffix}.png'),full_page=True)
    REPORT['trace'].append({'scenario':'lookup-status-exact','reference':reference,'observations':observations})
    for observation in observations:
        check(observation['textContent']==observation['status'],'exact status DOM text at '+str(observation['width']))
        check(observation['innerText']==observation['status'],'exact status displayed text at '+str(observation['width']))

async def out_of_order(context,page):
    await reset(context);await login(page)
    started=asyncio.Event();release=asyncio.Event();completed=asyncio.Event()
    async def delayed(route):
        if "restaurant_id=r_garden" in route.request.url:
            response=await route.fetch();started.set();await release.wait();await route.fulfill(response=response);completed.set()
        else: await route.continue_()
    await page.route("**/availability?*",delayed)
    await tid(page,"date-input").fill(DATE)
    await tid(page,"search-button").click();await asyncio.wait_for(started.wait(),5)
    await tid(page,"restaurant-select").select_option("r_harbor")
    await tid(page,"party-size-input").fill("5")
    await tid(page,"search-button").click()
    await expect(tid(page,"slot-t_booth-19:00")).to_be_visible()
    await open_booking(page,"t_booth","19:00")
    release.set();await asyncio.wait_for(completed.wait(),5)
    await page.wait_for_timeout(100)
    check(await tid(page,"slot-t_window-18:00").count()==0, "late A cannot restore grid")
    check("Harbor booth" in await tid(page,"booking-summary").inner_text(), "late A cannot restore table/form labels")
    check(await tid(page,"booking-party-size").input_value()=="5", "B party retained")
    check(await tid(page,"restaurant-select").input_value()=="r_harbor", "B restaurant retained")
    await screenshots(page,"search-race")
    REPORT["trace"].append({"scenario":"out-of-order","operations":["A fetch completed but response held","B selected and completed","B form opened","A released"],"winner":"r_harbor"})

async def conflict(context,page,combined=False):
    await reset(context);await login(page);await search(page,party="6" if combined else "2")
    ids="t_garden+t_window" if combined else "t_window"
    await open_booking(page,ids)
    _,auth=await request(context,BASE,"/auth/login","POST",{"email":"ben@example.test","password":"correct horse"})
    other={"restaurant_id":"r_garden","table_id":"t_window","starts_at_local":DATE+"T18:00","party_size":2}
    status,_=await request(context,BASE,"/reservations","POST",other,auth["token"],"competing-client")
    check(status==201,"second client takes selection")
    await tid(page,"booking-submit").click()
    await expect(tid(page,"booking-error")).to_be_visible()
    await expect(tid(page,"availability-grid")).to_be_visible()
    check(await tid(page,"booking-party-size").input_value()==("6" if combined else "2"), "refusal preserves party")
    check("Window" in await tid(page,"booking-summary").inner_text(), "refusal preserves selection")
    check(await tid(page,"confirmation").count()==0 and await tid(page,"booking-uncertain").count()==0,"confirmed refusal only")
    check(await tid(page,"slot-t_window-18:00").get_attribute("data-available")=="false", "occupancy refresh")
    if combined: check(await tid(page,"slot-t_garden+t_window-18:00").count()==0,"unavailable pair disappears")
    await screenshots(page,"combined-conflict" if combined else "single-conflict")

async def lost_response(context,page,combined=False,upgrade=False):
    if upgrade:
        await reset(context,LEGACY,True)
        async def old_api(route):
            target=LEGACY+route.request.url[len(BASE):]
            response=await route.fetch(url=target)
            await route.fulfill(response=response)
        await page.route("**/*",lambda route:old_api(route) if "/assets/" not in route.request.url and route.request.url[len(BASE):].split("?")[0] not in ["/","/login","/signup","/lookup"] else route.continue_())
    else: await reset(context)
    await login(page);await search(page,party="6" if combined else "2");await open_booking(page,"t_garden+t_window" if combined else "t_window")
    source=LEGACY if upgrade else BASE
    # A retained original reference is created by the source process before import.
    status,auth=await request(context,source,"/auth/login","POST",{"email":"ada@example.test","password":"correct horse"})
    retained={"restaurant_id":"r_harbor","table_id":"t_booth","starts_at_local":DATE+"T19:00","party_size":2}
    _,retained_receipt=await request(context,source,"/reservations","POST",retained,auth["token"],"retained-reference")
    writes=[];lost=[]
    async def drop(route):
        writes.append({"key":route.request.headers.get("idempotency-key"),"body":route.request.post_data})
        response=await route.fetch(url=source+"/reservations")
        check(response.status==201,"committed response before connection loss")
        lost.append(await response.json())
        await route.abort("failed")
    await page.route("**/reservations",drop)
    await tid(page,"booking-submit").click()
    await expect(tid(page,"booking-uncertain")).to_be_visible()
    check(bool(await tid(page,"booking-uncertain").inner_text()),"nonempty uncertainty")
    check(await tid(page,"booking-error").count()==0 and await tid(page,"confirmation").count()==0,"lost response cannot claim refusal or confirmation")
    await screenshots(page,"legacy-uncertain" if upgrade else "combined-uncertain" if combined else "single-uncertain")
    # Migration completes between requests: no reload, new login or form edit.
    if upgrade:
        _,snapshot=await request(context,LEGACY,"/_test/export")
        status,_=await request(context,BASE,"/_test/import","POST",snapshot)
        check(status==204,"genuine accepted Stage1 snapshot import")
        check("table_ids" not in lost[0],"real Stage1 original receipt shape")
    await page.unroute_all(behavior="wait")
    async def retry(route):
        writes.append({"key":route.request.headers.get("idempotency-key"),"body":route.request.post_data})
        await route.continue_()
    await page.route("**/reservations",retry)
    await tid(page,"booking-submit").click()
    reference=await confirmed(page)
    check(reference==lost[0]["reference"],"retry recovers original committed reference")
    check(writes[0]==writes[1],"uncertain retry body and key identical")
    await tid(page,"booking-submit").click();check(await confirmed(page)==reference,"repeat success no new reference")
    check(writes[1]==writes[2],"post-recovery unchanged identity")
    check("Window" in await tid(page,"confirmation-tables").inner_text(),"original receipt human label fallback")
    if combined: check("Garden" in await tid(page,"confirmation-tables").inner_text(),"both combined labels")
    if upgrade:
        await page.get_by_role("link",name="Your reservation",exact=True).click()
        await tid(page,"lookup-reference-input").fill(retained_receipt["reference"])
        await tid(page,"lookup-submit").click()
        await expect(tid(page,"reservation-status")).to_have_text("confirmed")
        await expect(tid(page,"current-user")).to_have_text("Ada")
        check("Harbor booth" in await tid(page,"reservation-tables").inner_text(),"retained old reference works without reload")
    REPORT["trace"].append({"scenario":"upgrade" if upgrade else "lost-combined" if combined else "lost-single","writes":writes,"committed_reference":reference,"retained_reference":retained_receipt["reference"]})

async def combinations(context,page):
    await reset(context);await login(page);await search(page,party="6")
    check(await tid(page,"slot-t_garden+t_window-18:00").get_attribute("data-available")=="true","declared canonical order")
    check(await tid(page,"slot-t_window+t_corner-18:00").count()==1,"second declared pair")
    check(await tid(page,"slot-t_garden+t_corner-18:00").count()==0,"no transitive pairs")
    for table in ["t_window","t_garden","t_corner"]: check(await tid(page,f"slot-{table}-18:00").get_attribute("data-available")=="false","capacity unavailable single")
    await open_booking(page,"t_garden+t_window")
    summary=await tid(page,"booking-summary").inner_text()
    check(all(label in summary for label in ["Garden","Window"]),"combined summary both labels")
    await tid(page,"booking-submit").click();await confirmed(page)
    summary=await tid(page,"confirmation-tables").inner_text()
    check(all(label in summary for label in ["Garden","Window"]),"combined confirmation both labels")
    _,availability=await request(context,BASE,f"/availability?restaurant_id=r_garden&date={DATE}&party_size=1")
    check(availability["slots"][0]["available_table_ids"]==["t_corner"],"pair atomically occupies both members")
    await page.get_by_role("link",name="View or cancel reservation").click();await tid(page,"lookup-submit").click()
    await expect(tid(page,"reservation-tables")).to_be_visible()
    summary=await tid(page,"reservation-tables").inner_text()
    check(all(label in summary for label in ["Garden","Window"]),"combined lookup both labels")
    await tid(page,"reservation-cancel-button").click();await expect(tid(page,"reservation-status")).to_have_text("cancelled")
    _,availability=await request(context,BASE,f"/availability?restaurant_id=r_garden&date={DATE}&party_size=1")
    check(availability["slots"][0]["available_table_ids"]==["t_window","t_garden","t_corner"],"cancel atomically releases both members")

async def changed_form(context,page):
    await reset(context);await login(page);await search(page);await open_booking(page)
    writes=[]
    async def drop(route):
        writes.append({"key":route.request.headers.get("idempotency-key"),"body":route.request.post_data})
        await route.abort("failed")
    await page.route("**/reservations",drop)
    await tid(page,"booking-submit").click();await expect(tid(page,"booking-uncertain")).to_be_visible()
    await tid(page,"booking-submit").click();await expect(tid(page,"booking-uncertain")).to_be_visible()
    check(writes[0]==writes[1],"unchanged uncommitted retry identity")
    await tid(page,"booking-party-size").fill("1")
    check(await tid(page,"booking-uncertain").count()==0,"changed request clears old uncertain identity")
    await tid(page,"booking-submit").click();await expect(tid(page,"booking-uncertain")).to_be_visible()
    check(writes[2]["key"]!=writes[1]["key"] and json.loads(writes[2]["body"])["party_size"]==1,"real field change rotates key and body")
    await page.unroute_all()
    await tid(page,"booking-submit").click();await confirmed(page)
    REPORT["trace"].append({"scenario":"changed-form","writes":writes})

async def empty_and_unavailable(context,page):
    await reset(context);await login(page)
    await tid(page,"date-input").fill("2032-06-20") # Sunday is closed.
    await tid(page,"search-button").click();await expect(tid(page,"no-slots")).to_be_visible()
    check(await tid(page,"availability-grid").count()==0,"closed day grid absent")
    await screenshots(page,"closed-day")
    await search(page,party="99")
    check(await tid(page,"slot-t_window-18:00").is_disabled(),"unavailable cell disabled")
    await tid(page,"slot-t_window-18:00").dispatch_event("click")
    check(await tid(page,"booking-form").count()==0,"unavailable does not open form")
    check(await page.locator('[data-testid^="slot-"][data-available="true"]').count()==0,"no options beyond capacity")
    await screenshots(page,"unavailable-grid")
    await page.get_by_role("link",name="Your reservation",exact=True).click()
    await tid(page,"lookup-reference-input").fill("NOBOOK")
    await tid(page,"lookup-submit").click();await expect(tid(page,"reservation-error")).to_be_visible()
    check(await tid(page,"reservation-detail").count()==0,"no fabricated lookup detail")

async def lookup_race_and_refusal(context,page):
    await reset(context);await login(page)
    _,ada=await request(context,BASE,"/auth/login","POST",{"email":"ada@example.test","password":"correct horse"})
    _,ben=await request(context,BASE,"/auth/login","POST",{"email":"ben@example.test","password":"correct horse"})
    body={"restaurant_id":"r_garden","table_id":"t_window","starts_at_local":"2000-01-03T18:00","party_size":2}
    status,past=await request(context,BASE,"/reservations","POST",body,ada["token"],"past-booking")
    check(status==201,"past create allowed for cutoff probe")
    body["starts_at_local"]=DATE+"T18:00"
    _,private=await request(context,BASE,"/reservations","POST",body,ben["token"],"private-booking")
    await page.get_by_role("link",name="Your reservation",exact=True).click()
    await tid(page,"lookup-reference-input").fill(private["reference"])
    await tid(page,"lookup-submit").click();await expect(tid(page,"reservation-error")).to_be_visible()
    check(await tid(page,"reservation-detail").count()==0,"other owner's actual reference stays private")
    await screenshots(page,"private-lookup-refusal")
    started=asyncio.Event();release=asyncio.Event();completed=asyncio.Event()
    async def delayed(route):
        response=await route.fetch();started.set();await release.wait();await route.fulfill(response=response);completed.set()
    await page.route("**/reservations/"+past["reference"],delayed)
    await tid(page,"lookup-reference-input").fill(past["reference"])
    await tid(page,"lookup-submit").click();await asyncio.wait_for(started.wait(),5)
    await tid(page,"lookup-reference-input").fill("NOBOOK")
    check(await tid(page,"lookup-submit").is_enabled(),"editing pending lookup restores submit")
    await tid(page,"lookup-submit").click();await expect(tid(page,"reservation-error")).to_be_visible()
    release.set();await asyncio.wait_for(completed.wait(),5)
    await page.wait_for_timeout(100)
    check(await tid(page,"reservation-detail").count()==0,"stale lookup cannot reveal previous detail")
    await page.unroute_all()
    await tid(page,"lookup-reference-input").fill(past["reference"])
    await tid(page,"lookup-submit").click();await expect(tid(page,"reservation-status")).to_have_text("confirmed")
    await tid(page,"reservation-cancel-button").click();await expect(tid(page,"reservation-error")).to_be_visible()
    await expect(tid(page,"reservation-status")).to_have_text("confirmed")
    check(await tid(page,"reservation-cancel-button").count()==1,"cutoff refusal leaves action and true status")
    await screenshots(page,"cutoff-refusal")

async def loading_auth_stability(context,page):
    await reset(context)
    started=asyncio.Event();release=asyncio.Event();completed=asyncio.Event()
    async def delayed(route):
        response=await route.fetch();started.set();await release.wait();await route.fulfill(response=response);completed.set()
    await page.route("**/restaurants",delayed)
    await page.goto(BASE+"/login")
    await asyncio.wait_for(started.wait(),5)
    await tid(page,"login-email").fill("ada@example.test")
    await tid(page,"login-password").fill("correct horse")
    await screenshots(page,"login-labelled")
    release.set();await asyncio.wait_for(completed.wait(),5);await page.wait_for_timeout(100)
    check(await tid(page,"login-email").input_value()=="ada@example.test" and await tid(page,"login-password").input_value()=="correct horse","catalogue completion preserves typed credentials")
    await tid(page,"login-submit").click();await expect(tid(page,"current-user")).to_have_text("Ada")
    await page.goto(BASE+"/signup")
    await screenshots(page,"signed-in-signup")
    await tid(page,"logout-button").click()
    await screenshots(page,"signup-labelled")

async def concurrent_pair_transport(context,page):
    await reset(context)
    _,auth=await request(context,BASE,"/auth/login","POST",{"email":"ada@example.test","password":"correct horse"})
    body={"restaurant_id":"r_garden","table_ids":["t_window","t_garden"],"starts_at_local":DATE+"T18:00","party_size":6}
    results=await asyncio.gather(*(request(context,BASE,"/reservations","POST",body,auth['token'],'pair-identical') for _ in range(50)))
    statuses=[r[0] for r in results]
    check(statuses.count(201)==1 and statuses.count(200)==49,"50 identical pair requests: one create, 49 replays")
    identical_counts={str(s):statuses.count(s) for s in set(statuses)}
    original=results[statuses.index(201)][1]
    check(all(r[1]==original for r in results),"all concurrent receipts identical JSON")
    check(original['table_ids']==['t_garden','t_window'] and 'table_id' not in original,"pair canonicalization through adapter")
    _,bookings=await request(context,BASE,"/reservations",token=auth['token'])
    check(len(bookings['reservations'])==1,"exactly one persisted pair")
    await reset(context)
    _,auth=await request(context,BASE,"/auth/login","POST",{"email":"ada@example.test","password":"correct horse"})
    results=await asyncio.gather(*(request(context,BASE,"/reservations","POST",body,auth['token'],'pair-competing-'+str(i)) for i in range(50)))
    statuses=[r[0] for r in results]
    check(statuses.count(201)==1 and statuses.count(409)==49,"50 competing pair requests: one create, 49 occupancy refusals")
    check(all(r[1]['error']['code']=='table_unavailable' for r in results if r[0]==409),"all competing refusals specific")
    _,bookings=await request(context,BASE,"/reservations",token=auth['token'])
    check(len(bookings['reservations'])==1,"competition never partially persists")
    _,availability=await request(context,BASE,f"/availability?restaurant_id=r_garden&date={DATE}&party_size=1")
    check(availability['slots'][0]['available_table_ids']==['t_corner'],"both members atomically occupied at read")
    REPORT['trace'].append({'scenario':'concurrent-pair-transport','identical_status_counts':identical_counts,'competing_status_counts':{str(s):statuses.count(s) for s in set(statuses)},'races':50,'persisted':1})

async def large_party_exactness(context,page,party):
    from urllib.parse import urlsplit,parse_qs
    fixture=copy.deepcopy(FIXTURE)
    fixture['restaurants'][0]['tables'][0]['capacity']=party
    fixture['restaurants'][0]['tables'][0]['label']='Window 9007199254740993 "Garden" \\ seat'
    status,_=await request(context,BASE,'/_test/reset','POST',fixture)
    check(status==204,'large capacity reset accepted without an upper cap')
    await login(page)
    searches=[];writes=[]
    def observed(req):
        if '/availability?' in req.url:searches.append(parse_qs(urlsplit(req.url).query)['party_size'][0])
        if req.method=='POST' and req.url==BASE+'/reservations':writes.append({'key':req.headers.get('idempotency-key'),'body':req.post_data})
    page.on('request',observed)
    await search(page,party=str(party))
    single_label=await tid(page,'slot-t_window-18:00').inner_text()
    pair_label=await tid(page,'slot-t_garden+t_window-18:00').inner_text()
    await open_booking(page)
    prefill=await tid(page,'booking-party-size').input_value()
    numeric_role=await tid(page,'booking-party-size').get_attribute('role')
    numeric_mode=await tid(page,'booking-party-size').get_attribute('inputmode')
    accessible_value=await tid(page,'booking-party-size').get_attribute('aria-valuenow')
    await tid(page,'booking-party-size').press('ArrowUp')
    incremented=await tid(page,'booking-party-size').input_value()
    await tid(page,'booking-party-size').press('ArrowDown')
    decremented=await tid(page,'booking-party-size').input_value()
    await tid(page,'booking-submit').click();reference=await confirmed(page)
    await tid(page,'booking-submit').click();check(await confirmed(page)==reference,'large unchanged retry reference')
    await page.get_by_role('link',name='View or cancel reservation').click()
    await tid(page,'lookup-submit').click();await expect(tid(page,'reservation-detail')).to_be_visible()
    guests=await tid(page,'reservation-detail').locator('dl div').filter(has=page.locator('dt',has_text='Guests')).locator('dd').inner_text()
    observations={'party':str(party),'query':searches,'prefill':prefill,'writes':writes,'grid_single':single_label,'grid_pair':pair_label,'lookup_guests':guests,'numeric_role':numeric_role,'numeric_mode':numeric_mode,'accessible_value':accessible_value,'incremented':incremented,'decremented':decremented}
    checks={
        'plain_exact_query':searches==[str(party)],
        'exact_prefill':prefill==str(party),
        'exact_json_numeric_body':len(writes)==2 and all(json.loads(w['body'])['party_size']==party for w in writes),
        'identical_key_body':len(writes)==2 and writes[0]==writes[1],
        'exact_single_capacity':str(party)+' seats' in single_label,
        'exact_pair_sum':str(party+4)+' seats' in pair_label,
        'exact_lookup_guests':guests==str(party),
        'quoted_numeric_label_unchanged':fixture['restaurants'][0]['tables'][0]['label'] in single_label,
        'numeric_control_semantics':numeric_role=='spinbutton' and numeric_mode=='numeric',
        'exact_accessible_value':accessible_value==str(party),
        'exact_keyboard_steps':incremented==str(party+1) and decremented==str(party),
    }
    observations['checks']=checks;REPORT['trace'].append({'scenario':'large-party-exactness','observations':observations})
    await screenshots(page,'large-party-'+str(len(str(party)))+'-'+str(party)[:20])
    for name,passed in checks.items():check(passed,'large-party '+name+': '+json.dumps(observations))

async def corrupt_response_and_numeric_keyboard(context,page):
    await reset(context);await login(page)
    await tid(page,'party-size-input').fill('9007199254740993')
    await tid(page,'party-size-input').press('ArrowUp')
    check(await tid(page,'party-size-input').input_value()=='9007199254740994','exact numeric keyboard increment')
    await tid(page,'party-size-input').press('ArrowDown')
    check(await tid(page,'party-size-input').input_value()=='9007199254740993','exact numeric keyboard decrement')
    check(await tid(page,'party-size-input').get_attribute('role')=='spinbutton','number field spinbutton semantics')
    check(await tid(page,'party-size-input').get_attribute('inputmode')=='numeric','mobile numeric keyboard mode')
    await search(page);await open_booking(page)
    await tid(page,'booking-party-size').fill('1')
    await tid(page,'booking-party-size').press('ArrowDown')
    check(await tid(page,'booking-party-size').input_value()=='1','minimum one guest')
    committed=[]
    async def corrupt(route):
        response=await route.fetch();check(response.status==201,'real commit before malformed response')
        value=await response.json();committed.append(value)
        text=await response.text()
        # An invalid unquoted numeric key must not become valid during exact parsing.
        await route.fulfill(response=response,body='{9007199254740993:0,'+text[1:])
    await page.route('**/reservations',corrupt)
    await tid(page,'booking-submit').click();await expect(tid(page,'booking-uncertain')).to_be_visible()
    check(await tid(page,'booking-error').count()==0 and await tid(page,'confirmation').count()==0,'malformed receipt is uncertain only')
    await page.unroute_all()
    await tid(page,'booking-submit').click();check(await confirmed(page)==committed[0]['reference'],'malformed receipt retry recovers real original')

async def local_end_display(context,page,zone,local,expected):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    fixture=copy.deepcopy(FIXTURE)
    restaurant=fixture['restaurants'][0];fixture['restaurants']=[restaurant]
    restaurant.update(timezone=zone,reservation_duration_minutes=90,
        opening_hours=[{'weekday':day,'opens':'00:00','closes':'23:59'} for day in ['mon','tue','wed','thu','fri','sat','sun']])
    fixture['reservations']=[{'id':'local_end','reference':'LOCAL01','user_id':'u_ada','restaurant_id':restaurant['id'],
        'table_id':'t_window','starts_at_local':local,'party_size':2}]
    status,_=await request(context,BASE,'/_test/reset','POST',fixture)
    check(status==204,'local-end fixture accepted')
    await login(page)
    await page.goto(BASE+'/lookup');await tid(page,'lookup-reference-input').fill('LOCAL01');await tid(page,'lookup-submit').click()
    await expect(tid(page,'reservation-detail')).to_be_visible()
    api=await context.request.get(BASE+'/reservations/LOCAL01',headers={'Authorization':'Bearer '+await page.evaluate("JSON.parse(sessionStorage.getItem('tablekeeper.session')).token")})
    record=await api.json();check(api.status==200,'actual private local-end record')
    oracle=datetime.fromisoformat(record['ends_at']).astimezone(ZoneInfo(zone)).strftime('%H:%M')
    check(oracle==expected,'independent IANA instant-to-local end oracle')
    end=tid(page,'reservation-detail').get_by_text('Ends at',exact=True).locator('..').locator('dd')
    observed=await end.inner_text()
    REPORT['trace'].append({'scenario':'local-end-display','zone':zone,'browser_timezone':'Pacific/Honolulu',
        'starts_at_local':record['starts_at_local'],'ends_at':record['ends_at'],'expected_local_end':oracle,'displayed_local_end':observed})
    check(await end.locator('time').get_attribute('datetime')==record['ends_at'],'immutable wire datetime remains unchanged')
    check(local[11:16] in await tid(page,'reservation-detail').locator('h2').inner_text(),'start retains original wall field')
    await screenshots(page,'local-end-'+zone.replace('/','-')+'-'+local[:10])
    check(observed.endswith(' · '+expected),'restaurant-local end display '+zone+' '+local)

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        cases=[("transport-public",transport),("authentication-keyboard",auth_keyboard),("single-book-lookup-cancel",ordinary),('lookup-status-exact',lookup_status_exact),
            ("out-of-order-search",out_of_order),("single-conflict",conflict),
            ("combined-conflict",lambda c,p:conflict(c,p,True)),("lost-single",lost_response),
            ("lost-combined",lambda c,p:lost_response(c,p,True)),("genuine-stage1-upgrade",lambda c,p:lost_response(c,p,upgrade=True)),
            ("combined-occupancy",combinations),("changed-retry-form",changed_form),("empty-unavailable-lookup",empty_and_unavailable),
            ("lookup-race-privacy-cutoff",lookup_race_and_refusal),("auth-inputs-loading",loading_auth_stability),("concurrent-pair-transport",concurrent_pair_transport),
            ("party-safe-boundary",lambda c,p:large_party_exactness(c,p,9007199254740991)),
            ("party-above-safe-integer",lambda c,p:large_party_exactness(c,p,9007199254740993)),
            ("party-31-digits",lambda c,p:large_party_exactness(c,p,10**30+1)),
            ("party-401-digits",lambda c,p:large_party_exactness(c,p,10**400+1)),
            ("exact-numeric-keyboard-corrupt-response",corrupt_response_and_numeric_keyboard)]
        end_cases=[('berlin-historic','Europe/Berlin','0001-01-01T18:00','19:30'),
            ('brussels-historic','Europe/Brussels','0001-01-01T18:00','19:30'),
            ('new-york-historic','America/New_York','0001-01-01T18:00','19:30'),
            ('berlin-fall-back','Europe/Berlin','2026-10-25T02:30','03:00'),
            ('new-york-fall-back','America/New_York','2026-11-01T01:30','02:00'),
            ('berlin-spring','Europe/Berlin','2026-03-29T01:30','04:00'),
            ('new-york-spring','America/New_York','2026-03-08T01:30','04:00'),
            ('last-calendar-date','UTC','9999-12-31T18:00','19:30')]
        for name,zone,local,expected in end_cases:
            cases.append(('local-end-'+name,lambda c,p,z=zone,l=local,e=expected:local_end_display(c,p,z,l,e)))
        for name,callback in cases: await scenario(name,callback,browser)
        REPORT["browser_version"]=browser.version
        await browser.close()
    REPORT["seconds"]=round(time.perf_counter()-start,3)
    REPORT["passed"]=sum(s["verdict"]=="PASS" for s in REPORT["scenarios"])
    REPORT["total"]=len(REPORT["scenarios"])
    (OUT/"browser-report.json").write_text(json.dumps(REPORT,indent=2)+"\n")
    print(json.dumps({k:REPORT[k] for k in ["candidate","passed","total","assertions","seconds"]}))
    for s in REPORT["scenarios"]:
        print(s["verdict"],s["name"])
        if s["verdict"]=="FAIL": print(s["error"])
    raise SystemExit(0 if REPORT["passed"]==REPORT["total"] else 1)

asyncio.run(main())
