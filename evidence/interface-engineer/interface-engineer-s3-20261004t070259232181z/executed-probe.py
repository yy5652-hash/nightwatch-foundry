"""Stage 3 original cumulative black-box browser/integration diagnostics.

Run inside the unchanged official runner image. Credentials remain in memory.
The race trace uses controlled events, not probabilistic sleeps.
"""
import asyncio
import copy
import json
import hashlib
import os
import sys
import time
import traceback
from pathlib import Path
from playwright.async_api import async_playwright, expect

# The client oracle must encode/decode the same unbounded valid decimal integers.
# This is confined to the probe process inside the dependency-runner container.
sys.set_int_max_str_digits(0)

BASE = os.environ["S2_BASE"]
LEGACY = os.environ["S1_BASE"]
OUT = Path(os.environ.get("PROBE_OUT", "/out"))
DATE = "2032-06-17"
REPORT = {"seed": 20261004, "candidate": os.environ["CANDIDATE"], "scenarios": [], "trace": [], "assertions": 0,"direct_http_operations":0,"browser_originated_requests":0,"forwarded_fetch_operations":0,"http_trace":[]}
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

async def direct_fetch(context,url,method='GET',**kwargs):
    from urllib.parse import urlsplit
    begin=time.perf_counter()
    response=await context.request.fetch(url,method=method,**kwargs)
    REPORT['direct_http_operations']+=1
    REPORT['http_trace'].append({'kind':'direct-api-client','method':method,'path':urlsplit(url).path,'status':response.status,'seconds':time.perf_counter()-begin})
    return response

async def forwarded_fetch(route,**kwargs):
    begin=time.perf_counter();response=await route.fetch(**kwargs)
    REPORT['forwarded_fetch_operations']+=1
    REPORT['http_trace'].append({'kind':'real-route-forwarding','method':route.request.method,'path':__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(route.request.url).path,'status':response.status,'seconds':time.perf_counter()-begin})
    return response

async def request(context, base, path, method="GET", data=None, token=None, key=None, raw=None):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token: headers["Authorization"] = "Bearer " + token
    if key: headers["Idempotency-Key"] = key
    response = await direct_fetch(context,base + path, method=method, headers=headers, data=raw if raw is not None else data, timeout=10000 if path.startswith('/_test/') else 5000)
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
    def count_browser_request(req):REPORT['browser_originated_requests']+=1
    page.on('request',count_browser_request)
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
        response=await direct_fetch(context,BASE+path)
        check(response.status==200, "direct screen: "+path)
        check(response.headers["content-type"]=="text/html; charset=utf-8", "HTML content type")
        check('src="/assets/app.js"' in await response.text(), "local script")
    for path, content_type in [("/assets/app.js", "text/javascript; charset=utf-8"),("/assets/app.css", "text/css; charset=utf-8")]:
        response=await direct_fetch(context,BASE+path)
        check(response.status==200 and response.headers["content-type"]==content_type, "offline asset: "+path)
    response=await direct_fetch(context,BASE+"/reservations",method="POST",data='{"party_size":NaN}',headers={"Content-Type":"application/json"})
    check(response.status==400 and (await response.json())["error"]["code"]=="malformed_request", "strict JSON precedes auth")
    response=await direct_fetch(context,BASE+"/auth/signup",method="POST",data='[]',headers={"Content-Type":"application/json"})
    check(response.status==400, "nonobject refusal")
    response=await direct_fetch(context,BASE+"/_test/reset",method="POST",data=FIXTURE)
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
            response=await forwarded_fetch(route,);started.set();await release.wait();await route.fulfill(response=response);completed.set()
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

async def lost_response(context,page,combined=False,upgrade=False,source_base=None,source_revision=None,source_stage=1):
    source=(source_base or LEGACY) if upgrade else BASE
    if upgrade:
        await reset(context,source,source_stage==1)
        async def old_api(route):
            target=source+route.request.url[len(BASE):]
            response=await forwarded_fetch(route,url=target)
            await route.fulfill(response=response)
        await page.route("**/*",lambda route:old_api(route) if "/assets/" not in route.request.url and route.request.url[len(BASE):].split("?")[0] not in ["/","/login","/signup","/lookup"] else route.continue_())
    else: await reset(context)
    await login(page);await search(page,party="6" if combined else "2");await open_booking(page,"t_garden+t_window" if combined else "t_window")
    # A retained original reference is created by the source process before import.
    status,auth=await request(context,source,"/auth/login","POST",{"email":"ada@example.test","password":"correct horse"})
    retained={"restaurant_id":"r_harbor","table_id":"t_booth","starts_at_local":DATE+"T19:00","party_size":2}
    if upgrade and source_stage==1: retained['table_ids']={'ignored-by-stage1':True}
    retained_status,retained_receipt=await request(context,source,"/reservations","POST",retained,auth["token"],"retained-reference")
    check(retained_status==201,'real source retained booking issued')
    move_body={'moves':[{'reference':retained_receipt['reference'],'starts_at_local':DATE+'T19:30'}]}
    if upgrade and source_stage==1: move_body['moves'][0]['table_ids']={'ignored-by-stage1':True}
    if upgrade:
        move_status,move_receipt=await request(context,source,'/reservation-moves','POST',move_body,auth['token'],'retained-move')
        check(move_status==201,'real source original move receipt issued')
    await page.evaluate('window.upgradeDocumentMarker="same-document"')
    writes=[];lost=[]
    async def drop(route):
        writes.append({"key":route.request.headers.get("idempotency-key"),"body":route.request.post_data})
        response=await forwarded_fetch(route,url=source+"/reservations")
        check(response.status==201,"committed response before connection loss")
        lost.append(await response.json())
        await route.abort("failed")
    await page.route("**/reservations",drop)
    await tid(page,"booking-submit").click()
    await expect(tid(page,"booking-uncertain")).to_be_visible()
    check(bool(await tid(page,"booking-uncertain").inner_text()),"nonempty uncertainty")
    check(await tid(page,"booking-error").count()==0 and await tid(page,"confirmation").count()==0,"lost response cannot claim refusal or confirmation")
    await screenshots(page,("upgrade-"+str(source_stage)+"-"+(source_revision or os.environ.get("S1_REVISION","accepted"))[:8]+("-pair" if combined else "-single")) if upgrade else "combined-uncertain" if combined else "single-uncertain")
    # Migration completes between requests: no reload, new login or form edit.
    if upgrade:
        exported=await direct_fetch(context,source+'/_test/export',timeout=10000)
        snapshot=await exported.body()
        check(exported.status==200,'genuine source raw export')
        status,_=await request(context,source,'/reservations/'+retained_receipt['reference']+'/cancel','POST',token=auth['token'])
        check(status==200,'source changes after snapshot captured')
        status,_=await request(context,BASE,"/_test/import","POST",raw=snapshot)
        check(status==204,"genuine unchanged snapshot import")
        if source_stage==1:check("table_ids" not in lost[0],"real Stage1 original receipt shape")
        else:check('table_ids' in lost[0],'real old Stage2 combined receipt shape')
        replay_status,replayed=await request(context,BASE,'/reservation-moves','POST',move_body,auth['token'],'retained-move')
        check(replay_status==200 and replayed==move_receipt,'original source move receipt replays unchanged after replacement')
        create_status,created=await request(context,BASE,'/reservations','POST',retained,auth['token'],'retained-reference')
        check(create_status==200 and created==retained_receipt,'original source create receipt replays after move')
        REPORT['trace'].append({'scenario':'raw-upgrade-transfer','source_revision':source_revision or os.environ.get('S1_REVISION'),'source_stage':source_stage,'export_bytes':len(snapshot),'import_bytes':len(snapshot),'export_sha256':hashlib.sha256(snapshot).hexdigest(),'import_sha256':hashlib.sha256(snapshot).hexdigest(),'decoded':False})
        new_body=json.dumps({'restaurant_id':'r_garden','table_id':'t_corner','starts_at_local':DATE+'T20:00','party_size':2},separators=(',',':'))[:-1]+',"ignored":9007199254740993.0}'
        new_status,new_receipt=await request(context,BASE,'/reservations','POST',token=auth['token'],key='current-exact-after-upgrade',raw=new_body)
        check(new_status==201,'current exact receipt joins genuine historical state')
        mixed_export=await direct_fetch(context,BASE+'/_test/export',timeout=10000);mixed=await mixed_export.body()
        peer=os.environ['S2_DEST_BASE']
        mixed_status,_=await request(context,peer,'/_test/import','POST',raw=mixed)
        check(mixed_status==204,'mixed origins raw replacement in independent peer')
        for path,body,key,receipt in [('/reservations',retained,'retained-reference',retained_receipt),('/reservation-moves',move_body,'retained-move',move_receipt)]:
            replay_status,replayed=await request(context,peer,path,'POST',body,auth['token'],key)
            check(replay_status==200 and replayed==receipt,'mixed peer retains original source receipt '+path)
        exact_status,exact_receipt=await request(context,peer,'/reservations','POST',token=auth['token'],key='current-exact-after-upgrade',raw=new_body.replace('9007199254740993.0','9007199254740993e0'))
        check(exact_status==200 and exact_receipt==new_receipt,'mixed peer retains exact numeric alias semantics')
        return_export=await direct_fetch(context,peer+'/_test/export',timeout=10000);returned=await return_export.body()
        returned_status,_=await request(context,BASE,'/_test/import','POST',raw=returned)
        check(returned_status==204,'genuine peer raw replacement back before browser retry')
        REPORT['trace'].append({'scenario':'raw-mixed-roundtrip','source_revision':source_revision or os.environ.get('S1_REVISION'),'source_stage':source_stage,'forward_bytes':len(mixed),'forward_sha256':hashlib.sha256(mixed).hexdigest(),'return_bytes':len(returned),'return_sha256':hashlib.sha256(returned).hexdigest(),'decoded':False})
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
        check(await page.evaluate('window.upgradeDocumentMarker')=='same-document','upgrade recovery used same browser document')
        await page.get_by_role("link",name="Your reservation",exact=True).click()
        await tid(page,"lookup-reference-input").fill(retained_receipt["reference"])
        await tid(page,"lookup-submit").click()
        await expect(tid(page,"reservation-status")).to_have_text("confirmed")
        await expect(tid(page,"current-user")).to_have_text("Ada")
        check("Harbor booth" in await tid(page,"reservation-tables").inner_text(),"retained old reference works without reload")
    REPORT["trace"].append({"scenario":"upgrade" if upgrade else "lost-combined" if combined else "lost-single","source_revision":source_revision,'source_stage':source_stage,"writes":writes,"committed_reference":reference,"retained_reference":retained_receipt["reference"]})
    return retained_receipt,auth,lost[0]

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
        response=await forwarded_fetch(route,);started.set();await release.wait();await route.fulfill(response=response);completed.set()
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
        response=await forwarded_fetch(route,);started.set();await release.wait();await route.fulfill(response=response);completed.set()
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
        response=await forwarded_fetch(route,);check(response.status==201,'real commit before malformed response')
        value=await response.json();committed.append(value)
        text=await response.text()
        # An invalid unquoted numeric key must not become valid during exact parsing.
        await route.fulfill(response=response,body='{9007199254740993:0,'+text[1:])
    await page.route('**/reservations',corrupt)
    await tid(page,'booking-submit').click();await expect(tid(page,'booking-uncertain')).to_be_visible()
    check(await tid(page,'booking-error').count()==0 and await tid(page,'confirmation').count()==0,'malformed receipt is uncertain only')
    await page.unroute_all()
    await tid(page,'booking-submit').click();check(await confirmed(page)==committed[0]['reference'],'malformed receipt retry recovers real original')

async def local_end_display(context,page,zone,local,expected,legacy=False):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    fixture=copy.deepcopy(FIXTURE)
    restaurant=fixture['restaurants'][0];fixture['restaurants']=[restaurant]
    restaurant.update(timezone=zone,reservation_duration_minutes=90,
        opening_hours=[{'weekday':day,'opens':'00:00','closes':'23:59'} for day in ['mon','tue','wed','thu','fri','sat','sun']])
    fixture['reservations']=[{'id':'local_end','reference':'LOCAL01','user_id':'u_ada','restaurant_id':restaurant['id'],
        'table_id':'t_window','starts_at_local':local,'party_size':2}]
    reference='LOCAL01'
    if legacy:
        fixture['reservations']=[];restaurant.pop('combinable')
        source=os.environ['S1_HIST_BASE']
        status,_=await request(context,source,'/_test/reset','POST',fixture)
        check(status==204,'genuine pre-serializer Stage1 reset')
        status,auth=await request(context,source,'/auth/login','POST',{'email':'ada@example.test','password':'correct horse'})
        check(status==200,'genuine historical source token')
        body={'restaurant_id':restaurant['id'],'table_id':'t_window','starts_at_local':local,'party_size':2}
        status,original=await request(context,source,'/reservations','POST',body,auth['token'],'historic-original-receipt')
        check(status==201,'genuine historical source booking')
        reference=original['reference']
        import re
        check(bool(re.search(r'[+-]\d\d:\d\d:\d\d$',original['ends_at'])),'genuine immutable offset-seconds timestamp')
        export_response=await direct_fetch(context,source+'/_test/export',timeout=10000)
        snapshot=await export_response.body()
        check(export_response.status==200,'genuine historical source export')
        status,_=await request(context,BASE,'/_test/import','POST',raw=snapshot)
        check(status==204,'unchanged genuine historical export import')
        status,replay=await request(context,BASE,'/reservations','POST',body,auth['token'],'historic-original-receipt')
        check(status==200 and replay==original,'immutable genuine old receipt and token retained')
    else:
        status,_=await request(context,BASE,'/_test/reset','POST',fixture)
        check(status==204,'local-end fixture accepted')
    await login(page)
    await page.goto(BASE+'/lookup');await tid(page,'lookup-reference-input').fill(reference);await tid(page,'lookup-submit').click()
    await expect(tid(page,'reservation-detail')).to_be_visible()
    api=await direct_fetch(context,BASE+'/reservations/'+reference,headers={'Authorization':'Bearer '+await page.evaluate("JSON.parse(sessionStorage.getItem('tablekeeper.session')).token")})
    record=await api.json();check(api.status==200,'actual private local-end record')
    if legacy:check(record['ends_at']==original['ends_at'] and record['starts_at_local']==original['starts_at_local'],'import retains original timestamp and wall fields')
    oracle=datetime.fromisoformat(record['ends_at']).astimezone(ZoneInfo(zone)).strftime('%H:%M')
    check(oracle==expected,'independent IANA instant-to-local end oracle')
    end=tid(page,'reservation-detail').get_by_text('Ends at',exact=True).locator('..').locator('dd')
    observed=await end.inner_text()
    REPORT['trace'].append({'scenario':'local-end-display','zone':zone,'browser_timezone':'Pacific/Honolulu',
        'starts_at_local':record['starts_at_local'],'ends_at':record['ends_at'],'expected_local_end':oracle,'displayed_local_end':observed,
        'genuine_legacy_source_revision':os.environ['S1_HIST_REVISION'] if legacy else None})
    check(await end.locator('time').get_attribute('datetime')==record['ends_at'],'immutable wire datetime remains unchanged')
    check(local[11:16] in await tid(page,'reservation-detail').locator('h2').inner_text(),'start retains original wall field')
    await screenshots(page,('legacy-' if legacy else '')+'local-end-'+zone.replace('/','-')+'-'+local[:10])
    check(observed.endswith(' · '+expected),'restaurant-local end display '+zone+' '+local)

async def huge_decimal_transport(context,page):
    import urllib.parse
    huge=10**4300+1
    fixture=copy.deepcopy(FIXTURE);restaurant=fixture['restaurants'][0]
    restaurant['tables'][0]['capacity']=huge;restaurant['slot_minutes']=huge
    status,_=await request(context,BASE,'/_test/reset','POST',raw=json.dumps(fixture))
    check(status==204,'4301-digit raw numeric JSON reset')
    status,detail=await request(context,BASE,'/restaurants/r_garden')
    check(status==200 and type(detail['tables'][0]['capacity']) is int and detail['tables'][0]['capacity']==huge,'4301-digit exact integer response')
    query=urllib.parse.urlencode({'restaurant_id':'r_garden','date':DATE,'party_size':str(huge)})
    status,availability=await request(context,BASE,'/availability?'+query)
    check(status==200 and len(availability['slots'])==1 and availability['slots'][0]['available_table_ids']==['t_window'],'4301-digit plain decimal query and grid count')
    status,auth=await request(context,BASE,'/auth/login','POST',{'email':'ada@example.test','password':'correct horse'})
    check(status==200,'huge transport real token')
    body={'restaurant_id':'r_garden','table_id':'t_window','starts_at_local':DATE+'T18:00','party_size':huge,'ignored_number':huge}
    status,original=await request(context,BASE,'/reservations','POST',raw=json.dumps(body),token=auth['token'],key='huge-raw-original')
    check(status==201 and type(original['party_size']) is int and original['party_size']==huge,'huge raw create preserves integer and ignores unknown numeric field')
    exported=await direct_fetch(context,BASE+'/_test/export');snapshot=await exported.body()
    check(exported.status==200,'huge exact export encoded without digit ceiling')
    destination=os.environ['S2_DEST_BASE']
    status,_=await request(context,destination,'/_test/import','POST',raw=snapshot)
    check(status==204,'unchanged huge export imported into independent process')
    status,current=await request(context,destination,'/reservations/'+original['reference'],token=auth['token'])
    check(status==200 and current==original,'huge record and token survive independent import')
    status,replay=await request(context,destination,'/reservations','POST',raw=json.dumps(body),token=auth['token'],key='huge-raw-original')
    check(status==200 and replay==original,'huge original receipt and parsed body replay after import')
    wrong=dict(body,party_size=str(huge))
    status,error=await request(context,destination,'/reservations','POST',wrong,auth['token'],'huge-wrong-type')
    check(status==422 and error['error']['code']=='validation_failed','large string party remains invalid')
    status,error=await request(context,destination,'/reservations','POST',wrong,auth['token'],'huge-raw-original')
    check(status==409 and error['error']['code']=='idempotency_key_reuse','large changed body conflicts before type validation')
    for invalid in ['1e4300','4.0','+4','-'+str(huge)]:
        query=urllib.parse.urlencode({'restaurant_id':'r_garden','date':DATE,'party_size':invalid})
        status,error=await request(context,BASE,'/availability?'+query)
        check(status==422 and error['error']['code']=='validation_failed','strict decimal query refusal '+invalid[:12])
    restaurant['slot_minutes']=30;restaurant['reservation_duration_minutes']=huge
    status,_=await request(context,BASE,'/_test/reset','POST',raw=json.dumps(fixture))
    check(status==204,'4301-digit duration fixture accepted')
    status,value=await request(context,BASE,'/availability?restaurant_id=r_garden&date='+DATE+'&party_size=2')
    check(status==200 and value['slots']==[],'huge absolute duration has no fitting slots')
    restaurant['reservation_duration_minutes']=60;restaurant['cancellation_cutoff_minutes']=huge
    status,_=await request(context,BASE,'/_test/reset','POST',raw=json.dumps(fixture))
    check(status==204,'4301-digit cutoff fixture accepted')
    _,auth=await request(context,BASE,'/auth/login','POST',{'email':'ada@example.test','password':'correct horse'})
    status,record=await request(context,BASE,'/reservations','POST',dict(body,party_size=2),auth['token'],'huge-cutoff-create')
    check(status==201,'huge cutoff still permits real booking')
    status,error=await request(context,BASE,'/reservations/'+record['reference']+'/cancel','POST',token=auth['token'])
    check(status==409 and error['error']['code']=='cutoff_passed','huge cutoff gives ordinary stable refusal')
    status,current=await request(context,BASE,'/reservations/'+record['reference'],token=auth['token'])
    check(status==200 and current==record,'cutoff refusal leaves record unchanged')
    REPORT['trace'].append({'scenario':'huge-decimal-transport','digits':4301,'independent_destination':True,'original_receipt_preserved':True,'json_type':'integer','base_counts':['capacity','slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes']})

async def integral_wire_presentation(context,page,spelling,party=9007199254740993):
    fixture=copy.deepcopy(FIXTURE)
    fixture['restaurants'][0]['tables'][0]['capacity']=party
    fixture['restaurants'][0]['tables'][0]['label']='Window 9007199254740993 "quoted"'
    raw=json.dumps(fixture,separators=(',',':')).replace('"capacity":'+str(party),'"capacity":'+spelling,1)
    status,_=await request(context,BASE,'/_test/reset','POST',raw=raw)
    check(status==204,'valid integral decimal/exponent fixture accepted')
    detail=await direct_fetch(context,BASE+'/restaurants/r_garden')
    wire=await detail.text()
    from decimal import Decimal
    parsed=json.loads(wire,parse_int=Decimal,parse_float=Decimal)
    check(parsed['tables'][0]['capacity']==Decimal(party),'real response capacity retains exact numeric value')
    await login(page);await search(page,party=str(party))
    single=await tid(page,'slot-t_window-18:00').inner_text()
    pair=await tid(page,'slot-t_garden+t_window-18:00').inner_text()
    check(str(party)+' seats' in single,'decimal/exponent response exact single capacity display')
    check(str(party+4)+' seats' in pair,'decimal/exponent response exact combined capacity display')
    await open_booking(page);check(await tid(page,'booking-party-size').input_value()==str(party),'decimal/exponent exact form prefill')
    await tid(page,'booking-submit').click();reference=await confirmed(page)
    await tid(page,'booking-submit').click();check(await confirmed(page)==reference,'decimal/exponent unchanged retry')
    await page.get_by_role('link',name='View or cancel reservation').click();await tid(page,'lookup-submit').click()
    await expect(tid(page,'reservation-status')).to_have_text('confirmed')
    capacity_tokens=__import__('re').findall(r'"capacity":(-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)',wire)
    REPORT['trace'].append({'scenario':'integral-wire-presentation','fixture_token':spelling,'real_response_capacity_tokens':capacity_tokens,'expected_integer':str(party),'single':single,'pair':pair,'original_reference':reference})
    await screenshots(page,'integral-wire-'+spelling.replace('.','d').replace('+','p').replace('-','m'))

async def opaque_identifiers(context,page):
    from urllib.parse import parse_qs,urlsplit,quote
    fixture=copy.deepcopy(FIXTURE)
    r=fixture['restaurants'][0];rid='r_🌿/ ?#%+&"\\';ids=['t_窓/ ?#%+&"\\','t_園+雪','t_角%2F']
    r['id']=rid;r['name']='The Garden · 花園'
    labels=['Window · 窓 "view"','Garden · 園','Corner · 角']
    for t,i,label in zip(r['tables'],ids,labels):t['id']=i;t['label']=label
    r['combinable']=[[ids[1],ids[0]],[ids[0],ids[2]]]
    status,_=await request(context,BASE,'/_test/reset','POST',fixture);check(status==204,'opaque Unicode URI fixture admitted')
    await login(page);queries=[];writes=[]
    def observe(req):
        if '/availability?' in req.url:queries.append(parse_qs(urlsplit(req.url).query).get('restaurant_id'))
        if req.method=='POST' and req.url==BASE+'/reservations':writes.append({'key':req.headers.get('idempotency-key'),'body':req.post_data})
    page.on('request',observe)
    await search(page,restaurant=rid,party='6')
    cell=tid(page,'slot-'+ids[1]+'+'+ids[0]+'-18:00')
    check(await cell.get_attribute('data-available')=='true','declared opaque pair advertised')
    await cell.press('Enter');await expect(tid(page,'booking-form')).to_be_visible()
    summary=await tid(page,'booking-summary').inner_text()
    check(all(label in summary for label in labels[:2]),'opaque pair summary names human labels')
    await tid(page,'booking-submit').click();reference=await confirmed(page)
    await tid(page,'booking-submit').click();check(await confirmed(page)==reference,'opaque pair stable retry')
    check(writes[0]==writes[1] and json.loads(writes[0]['body'])['restaurant_id']==rid,'opaque request identity exact')
    check(json.loads(writes[0]['body'])['table_ids']==[ids[1],ids[0]],'opaque pair canonical declaration order')
    await page.get_by_role('link',name='View or cancel reservation').click();await tid(page,'lookup-submit').click()
    await expect(tid(page,'reservation-status')).to_have_text('confirmed')
    lookup_labels=await tid(page,'reservation-tables').inner_text()
    check(all(label in lookup_labels for label in labels[:2]),'opaque lookup labels')
    await screenshots(page,'opaque-unicode-pair')
    await tid(page,'reservation-cancel-button').click();await expect(tid(page,'reservation-status')).to_have_text('cancelled')
    check(all(q==[rid] for q in queries),'opaque restaurant query survives percent encoding')
    REPORT['trace'].append({'scenario':'opaque-identifiers','restaurant_id':rid,'table_ids':ids,'queries':queries,'writes':writes,'reference':reference})

async def stage3_fixture(context):
    fixture=copy.deepcopy(FIXTURE)
    fixture['restaurants'][0]['manager_user_ids']=['u_ben']
    check((await request(context,BASE,'/_test/reset','POST',fixture))[0]==204,'Stage3 manager fixture reset')
    status,owner=await request(context,BASE,'/auth/login','POST',{'email':'ada@example.test','password':'correct horse'})
    check(status==200,'actual diner token')
    status,manager=await request(context,BASE,'/auth/login','POST',{'email':'ben@example.test','password':'correct horse'})
    check(status==200,'actual fixture manager token')
    return fixture,owner,manager

async def create3(context,owner,start='18:00',table='t_window',party=2,key='s3-anchor'):
    body={'restaurant_id':'r_garden','table_id':table,'starts_at_local':DATE+'T'+start,'party_size':party}
    status,receipt=await request(context,BASE,'/reservations','POST',body,owner['token'],key)
    check(status==201,'real anchor created')
    return body,receipt

async def lookup3(page,reference):
    if not page.url.endswith('/lookup'):await page.get_by_role('link',name='Your reservation',exact=True).click()
    await tid(page,'lookup-reference-input').fill(reference)
    await tid(page,'lookup-submit').click()
    await expect(tid(page,'reservation-history')).to_be_visible()
    await expect(tid(page,'reservation-revision')).to_be_visible()
    REPORT['assertions']+=2

def policy3(capacity=8,duration=120,cutoff=45,effective=DATE):
    return {'effective_from':effective,'slot_minutes':30,'reservation_duration_minutes':duration,
            'cancellation_cutoff_minutes':cutoff,'opening_hours':[{'weekday':day,'opens':'18:00','closes':'23:00'} for day in ['mon','tue','wed','thu','fri','sat','sun']],
            'capacities':{'t_window':capacity,'t_garden':9,'t_corner':10}}

async def policy_history_product(context,page):
    fixture,owner,manager=await stage3_fixture(context)
    denied,_=await request(context,BASE,'/restaurants/r_garden/policies','POST',policy3(),owner['token'],'denied-policy')
    check(denied==403,'ordinary diner cannot publish fixture manager policy')
    for body,key in [(policy3(effective='2032-06-24'),'later'),(policy3(),'earlier'),(policy3(capacity=7,duration=90,cutoff=30),'tie')]:
        status,published=await request(context,BASE,'/restaurants/r_garden/policies','POST',body,manager['token'],key)
        check(status==201,'actual complete dated policy published')
    await login(page);await search(page,party='6')
    check('7 seats' in await tid(page,'slot-t_window-18:00').inner_text(),'grid capacity uses selected policy, not original capacity2')
    await open_booking(page);await tid(page,'booking-submit').click();reference=await confirmed(page)
    terms=tid(page,'confirmation-terms')
    await terms.locator('summary').click()
    check('90 minutes' in await terms.inner_text() and '30 minutes before' in await terms.inner_text(),'original confirmation accepted duration/cutoff')
    status,original=await request(context,BASE,'/reservations/'+reference,token=owner['token'])
    check(status==200 and original['accepted_terms']['policy_version']==3,'same-date greatest version selected')
    await screenshots(page,'s3-original-confirmation-terms')
    await lookup3(page,reference)
    await tid(page,'reservation-current-terms').locator('summary').click()
    check('policy 3' in await tid(page,'reservation-current-terms').inner_text(),'current decision policy displayed')
    count=await tid(page,'reservation-history').locator('ol.history-list>li').count()
    status,no_op=await request(context,BASE,'/reservations/'+reference,'PATCH',{'party_size':6},owner['token'])
    check(status==200 and no_op['revision']==1,'no-op preserves revision')
    check((await request(context,BASE,'/reservations/'+reference+'/history',token=owner['token']))[1]['entries'][-1]['revision']==1,'no-op creates no event')
    status,new_policy=await request(context,BASE,'/restaurants/r_garden/policies','POST',policy3(capacity=8,duration=60,cutoff=15),manager['token'],'new-tie')
    check(status==201,'new policy after accepted booking')
    await tid(page,'lookup-submit').click();await expect(tid(page,'reservation-revision')).to_have_text('Current revision 1')
    check('policy 3' in await tid(page,'reservation-current-terms').inner_text(),'new publication leaves accepted terms unchanged')
    status,changed=await request(context,BASE,'/reservations/'+reference,'PATCH',{'party_size':7,'expected_revision':1},owner['token'])
    check(status==200 and changed['revision']==2 and changed['accepted_terms']['policy_version']==4,'real amendment adopts current date policy')
    status,stale=await request(context,BASE,'/reservations/'+reference,'PATCH',{'party_size':False,'expected_revision':1},owner['token'])
    check(status==409 and stale['error']['code']=='stale_revision','stale check precedes invalid party value')
    await tid(page,'lookup-submit').click();await expect(tid(page,'reservation-revision')).to_have_text('Current revision 2')
    history=tid(page,'reservation-history')
    check(await history.locator('ol.history-list>li').count()==count+1,'only one new changed event')
    check('Guests: 6 → 7' in await tid(page,'history-entry-2').inner_text(),'human exact changed field')
    check('policy 3' in await tid(page,'history-entry-1').inner_text() and 'policy 4' in await tid(page,'history-entry-2').inner_text(),'history terms never rewritten')
    await tid(page,'reservation-cancel-button').click();await expect(tid(page,'reservation-status')).to_have_text('cancelled')
    check(await history.locator('ol.history-list>li').count()==3,'cancel adds one current history entry')
    await screenshots(page,'s3-cancelled-ordered-history')
    check((await request(context,BASE,'/restaurants/r_garden'))[1]['tables'][0]['capacity']==2,'ordinary restaurant still original fixture')
    REPORT['trace'].append({'scenario':'stage3-policy-history','reference':reference,'selected_version':3,'changed_version':4,'history_count':3,'stale_status':status})

async def history_privacy_product(context,page):
    _,owner,manager=await stage3_fixture(context)
    _,anchor=await create3(context,owner)
    for token in [None,manager['token']]:
        for suffix in ['/history','/decision']:
            status,value=await request(context,BASE,'/reservations/'+anchor['reference']+suffix,token=token)
            check(status==404 and value['error']['code']=='not_found','history/decision privacy even manager/anonymous')
    await login(page,'ben')
    await page.get_by_role('link',name='Your reservation',exact=True).click()
    await tid(page,'lookup-reference-input').fill(anchor['reference']);await tid(page,'lookup-submit').click()
    await expect(tid(page,'reservation-error')).to_be_visible()
    check(await tid(page,'reservation-detail').count()==0 and await tid(page,'reservation-history').count()==0 and await tid(page,'series-form').count()==0,'manager UI receives no private diner surface')
    await screenshots(page,'s3-manager-private-refusal')

async def explanation_product(context,page):
    _,owner,_=await stage3_fixture(context)
    await create3(context,owner)
    await page.goto(BASE+'/');await search(page,party='6')
    text=await tid(page,'slot-t_window-18:00').inner_text()
    check('Too few seats' in text and 'Already booked' in text,'both actual independent rules explained')
    plain=await request(context,BASE,'/availability?restaurant_id=r_garden&date='+DATE+'&party_size=6')
    check('explain' not in plain[1]['slots'][0],'omitted explain retains existing shape')
    status,value=await request(context,BASE,'/availability?restaurant_id=r_garden&date='+DATE+'&party_size=6&explain=false')
    check(status==422 and value['error']['code']=='validation_failed','only true explain accepted')
    await screenshots(page,'s3-two-rule-refusal')

async def series_product(context,page,drop=False,malformed=False):
    _,owner,manager=await stage3_fixture(context)
    body,anchor=await create3(context,owner)
    await request(context,BASE,'/restaurants/r_garden/policies','POST',policy3(capacity=4,duration=90,cutoff=15,effective='2032-06-24'),manager['token'],'future-series-policy')
    await login(page);await lookup3(page,anchor['reference'])
    await page.set_viewport_size({'width':375,'height':812})
    await tid(page,'series-count').fill('3');await tid(page,'series-interval-weeks').fill('1')
    writes=[];original=[]
    async def capture(route):
        writes.append({'key':route.request.headers.get('idempotency-key'),'body':route.request.post_data})
        response=await forwarded_fetch(route)
        original.append(await response.json())
        if len(writes)==1 and drop:await route.abort('failed')
        elif len(writes)==1 and malformed:await route.fulfill(status=response.status,body='{1:2}',headers={'content-type':'application/json; charset=utf-8'})
        else:await route.fulfill(response=response)
    await page.route('**/series',capture)
    await tid(page,'series-count').press('Tab');await tid(page,'series-interval-weeks').press('Tab')
    await tid(page,'series-submit').press('Enter')
    if drop or malformed:
        await expect(tid(page,'series-uncertain')).to_be_visible()
        check(await tid(page,'series-error').count()==0 and await tid(page,'series-confirmation').count()==0 and await tid(page,'series-occurrences').count()==0,'uncertain series cannot fabricate refusal or committed list')
        await screenshots(page,'s3-series-'+('malformed' if malformed else 'lost'))
        await tid(page,'series-submit').press('Enter')
        check(writes[0]==writes[1],'same original series body/key on unchanged keyboard retry')
    await expect(tid(page,'series-occurrences')).to_be_visible()
    sid=await tid(page,'series-id').inner_text()
    check(sid==original[0]['series_id'],'real original recurring reference recovered')
    check(await tid(page,'series-occurrences').locator('ol>li').count()==3,'legible complete occurrence list')
    check(all(original[0]['occurrences'][0]['reservation'].get(k)==v for k,v in anchor.items()),'anchor existing values exactly unchanged by adoption')
    check(original[0]['occurrences'][1]['reservation']['accepted_terms']['policy_version']==1,'future occurrence independently selects future policy')
    references=[item['reference'] for item in original[0]['occurrences']]
    status,changed=await request(context,BASE,'/reservations/'+references[1],'PATCH',{'party_size':3},owner['token'])
    check(status==200,'actual individual occurrence changed')
    status,cancelled=await request(context,BASE,'/reservations/'+references[2]+'/cancel','POST',token=owner['token'])
    check(status==200,'actual sibling cancelled')
    await tid(page,'series-refresh').click();await expect(tid(page,'series-revision')).to_have_text('Agreement revision 3')
    check('permanent exception' in await tid(page,'series-occurrence-1').inner_text(),'real changed occurrence permanent exception shown')
    check('cancelled' in await tid(page,'series-occurrence-2').inner_text() and 'Part of the recurring agreement' in await tid(page,'series-occurrence-2').inner_text(),'cancelled occurrence retained without invented exception')
    await screenshots(page,'s3-series-exception-cancelled')
    await tid(page,'series-submit').click();await expect(tid(page,'series-revision')).to_have_text('Agreement revision 3')
    check(writes[-1]==writes[0] and original[-1]==original[0],'original series replay remains immutable after changes')
    exported=await direct_fetch(context,BASE+'/_test/export',timeout=10000);raw=await exported.body()
    peer=os.environ['S2_DEST_BASE'];check((await request(context,peer,'/_test/import','POST',raw=raw))[0]==204,'populated actual current series raw peer import')
    status,current=await request(context,peer,'/series/'+sid,token=owner['token'])
    check(status==200 and current['revision']==3 and current['occurrences'][1]['exception'] and current['occurrences'][2]['reservation']['status']=='cancelled','current imported series and exceptions retained')
    status,replay=await request(context,peer,'/series','POST',raw=writes[0]['body'],token=owner['token'],key=writes[0]['key'])
    check(status==200 and replay==original[0],'import preserves original recurring receipt')
    for token in [None,manager['token']]:check((await request(context,peer,'/series/'+sid,token=token))[0]==404,'series owner-only even fixture manager')
    check((await request(context,BASE,'/reservations','POST',body,owner['token'],'s3-anchor'))[1]==anchor,'anchor original create receipt remains unchanged')
    REPORT['trace'].append({'scenario':'stage3-series','mode':'lost' if drop else 'malformed' if malformed else 'keyboard','series_id':sid,'references':references,'writes':writes,'export_bytes':len(raw),'import_bytes':len(raw),'export_sha256':hashlib.sha256(raw).hexdigest(),'import_sha256':hashlib.sha256(raw).hexdigest(),'decoded':False})
    await tid(page,'logout-button').click()
    check(await tid(page,'reservation-history').count()==0 and await tid(page,'series-occurrences').count()==0,'logout clears own private histories and occurrences')

async def series_refusal_product(context,page):
    _,owner,_=await stage3_fixture(context)
    _,anchor=await create3(context,owner)
    blocked_body={'restaurant_id':'r_garden','table_id':'t_window','starts_at_local':'2032-06-24T18:00','party_size':2}
    status,blocked=await request(context,BASE,'/reservations','POST',blocked_body,owner['token'],'future-blocker')
    check(status==201,'real competing future booking')
    await login(page);await lookup3(page,anchor['reference']);await tid(page,'series-count').fill('3')
    writes=[]
    page.on('request',lambda req:writes.append({'key':req.headers.get('idempotency-key'),'body':req.post_data}) if req.url.endswith('/series') and req.method=='POST' else None)
    await tid(page,'series-submit').click();await expect(tid(page,'series-error')).to_be_visible()
    check(await tid(page,'series-confirmation').count()==0 and await tid(page,'series-occurrences').count()==0,'refused adoption shows no success or partial occurrence list')
    status,records=await request(context,BASE,'/reservations',token=owner['token'])
    check(status==200 and len(records['reservations'])==2,'failed adoption leaves only real original records')
    await screenshots(page,'s3-series-real-refusal')
    await request(context,BASE,'/reservations/'+blocked['reference']+'/cancel','POST',token=owner['token'])
    await tid(page,'series-submit').click();await expect(tid(page,'series-occurrences')).to_be_visible()
    check(writes[0]==writes[1],'confirmed failed series key remains reusable unchanged')

async def series_changed_identity(context,page):
    _,owner,_=await stage3_fixture(context);_,anchor=await create3(context,owner)
    await login(page);await lookup3(page,anchor['reference'])
    writes=[]
    async def block(route):
        writes.append({'key':route.request.headers.get('idempotency-key'),'body':route.request.post_data});await route.abort('failed')
    await page.route('**/series',block)
    await tid(page,'series-submit').click();await expect(tid(page,'series-uncertain')).to_be_visible()
    await tid(page,'series-count').fill('3');await tid(page,'series-submit').click();await expect(tid(page,'series-uncertain')).to_be_visible()
    check(writes[0]['key']!=writes[1]['key'] and writes[0]['body']!=writes[1]['body'],'real series field change changes request identity')
    await page.unroute_all(behavior='wait');await tid(page,'series-submit').click();await expect(tid(page,'series-occurrences')).to_be_visible()
    await screenshots(page,'s3-series-edited-recovery')

async def upgraded_adoption(context,page,base,revision,pair=False,stage=2):
    retained,owner,lost=await lost_response(context,page,pair,True,base,revision,stage)
    anchor=lost if pair else retained
    if pair:await lookup3(page,anchor['reference'])
    await expect(tid(page,'reservation-history')).to_be_visible();REPORT['assertions']+=1
    check('policy 0' in await tid(page,'reservation-current-terms').inner_text(),'genuine prior booking gains current adopted terms separately from original receipt')
    await tid(page,'series-count').fill('2');await tid(page,'series-submit').click();await expect(tid(page,'series-occurrences')).to_be_visible()
    sid=await tid(page,'series-id').inner_text()
    status,current=await request(context,BASE,'/series/'+sid,token=owner['token'])
    check(status==200 and current['occurrences'][0]['reference']==anchor['reference'],'actual imported prior anchor adopted with same reference')
    await screenshots(page,'s3-upgraded-anchor-'+('pair' if pair else 'single'))

async def pair_history_product(context,page):
    _,owner,_=await stage3_fixture(context)
    body={'restaurant_id':'r_garden','table_ids':['t_window','t_garden'],'starts_at_local':DATE+'T18:00','party_size':6}
    status,anchor=await request(context,BASE,'/reservations','POST',body,owner['token'],'pair-anchor')
    check(status==201 and anchor['table_ids']==['t_garden','t_window'],'real declared-order pair booking')
    status,no_op=await request(context,BASE,'/reservations/'+anchor['reference'],'PATCH',{'table_ids':['t_window','t_garden']},owner['token'])
    check(status==200 and no_op['revision']==1,'pair reversal remains no-op')
    await login(page);await lookup3(page,anchor['reference'])
    check('Tables: Not previously booked → Garden + Window' in await tid(page,'history-entry-1').inner_text(),'pair creation human full labels in declared order')
    status,changed=await request(context,BASE,'/reservations/'+anchor['reference'],'PATCH',{'table_id':'t_corner','party_size':4},owner['token'])
    check(status==200 and changed['table_ids']==['t_corner'],'actual pair-to-single transition')
    await tid(page,'lookup-submit').click();await expect(tid(page,'history-entry-2')).to_be_visible()
    check('Tables: Garden + Window → Corner' in await tid(page,'history-entry-2').inner_text(),'pair transition history carries complete before/after seating')
    check('Guests: 6 → 4' in await tid(page,'history-entry-2').inner_text(),'pair transition exact party change')
    await screenshots(page,'s3-pair-transition-history')

async def series_read_race(context,page):
    _,owner,_=await stage3_fixture(context);_,a=await create3(context,owner)
    _,b=await create3(context,owner,start='19:00',table='t_garden',key='anchor-B')
    agreements=[]
    for i,anchor in enumerate([a,b]):
        status,current=await request(context,BASE,'/series','POST',{'anchor_reference':anchor['reference'],'count':2,'interval_weeks':1},owner['token'],'series-'+str(i))
        check(status==201,'actual second own agreement for read race');agreements.append(current)
    await login(page);await lookup3(page,a['reference'])
    held=asyncio.Event();release=asyncio.Event()
    async def delayed(route):
        response=await forwarded_fetch(route);held.set();await release.wait();await route.fulfill(response=response)
    await page.route('**/series/'+agreements[0]['series_id'],delayed)
    await tid(page,'series-lookup-id').fill(agreements[0]['series_id']);await tid(page,'series-refresh').click();await held.wait()
    await tid(page,'series-lookup-id').fill(agreements[1]['series_id']);await tid(page,'series-refresh').click()
    await expect(tid(page,'series-occurrences')).to_be_visible()
    check(b['reference'] in await tid(page,'series-occurrences').inner_text(),'newer agreement B list completed')
    release.set();await page.unroute_all(behavior='wait')
    check(b['reference'] in await tid(page,'series-occurrences').inner_text() and a['reference'] not in await tid(page,'series-occurrences').inner_text(),'late A cannot restore old occurrence list')
    await screenshots(page,'s3-series-read-race')

async def series_restaurant_labels(context,page):
    _,owner,_=await stage3_fixture(context);_,garden=await create3(context,owner)
    body={'restaurant_id':'r_harbor','table_id':'t_booth','starts_at_local':DATE+'T19:00','party_size':2}
    status,harbor=await request(context,BASE,'/reservations','POST',body,owner['token'],'harbor-anchor')
    check(status==201,'real owned anchor in another restaurant')
    status,agreement=await request(context,BASE,'/series','POST',{'anchor_reference':harbor['reference'],'count':2,'interval_weeks':1},owner['token'],'harbor-series')
    check(status==201,'real other-restaurant recurring agreement')
    await login(page);await lookup3(page,garden['reference'])
    await tid(page,'series-lookup-id').fill(agreement['series_id']);await tid(page,'series-refresh').click()
    await expect(tid(page,'series-occurrences')).to_be_visible()
    text=await tid(page,'series-occurrences').inner_text()
    check('Harbor House' in text and text.count('Harbor booth')==2 and 'Garden Room' not in text,'occurrence labels belong to actual agreement restaurant')
    await screenshots(page,'s3-series-own-restaurant-labels')

async def series_dst_refusal(context,page,zone,anchor_date):
    fixture=copy.deepcopy(FIXTURE);restaurant=fixture['restaurants'][0];restaurant['timezone']=zone
    restaurant['opening_hours']=[{'weekday':d,'opens':'00:00','closes':'06:00'} for d in ['mon','tue','wed','thu','fri','sat','sun']]
    check((await request(context,BASE,'/_test/reset','POST',fixture))[0]==204,'genuine DST recurrence fixture')
    _,owner=await request(context,BASE,'/auth/login','POST',{'email':'ada@example.test','password':'correct horse'})
    body={'restaurant_id':'r_garden','table_id':'t_window','starts_at_local':anchor_date+'T02:30','party_size':2}
    status,anchor=await request(context,BASE,'/reservations','POST',body,owner['token'],'dst-anchor')
    check(status==201,'future pre-transition real anchor')
    await login(page);await lookup3(page,anchor['reference']);await tid(page,'series-count').fill('2');await tid(page,'series-submit').click()
    await expect(tid(page,'series-error')).to_be_visible()
    check('clocks change' in await tid(page,'series-error').inner_text(),'future nonexistent local recurrence explains actual refusal')
    check(await tid(page,'series-confirmation').count()==0 and await tid(page,'series-occurrences').count()==0,'DST failure displays no partial series')
    check(len((await request(context,BASE,'/reservations',token=owner['token']))[1]['reservations'])==1,'DST adoption rolls back generated reservations')
    await screenshots(page,'s3-dst-series-refusal-'+zone.replace('/','-'))

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
            ('party-4301-digits',lambda c,p:large_party_exactness(c,p,10**4300+1)),
            ('huge-decimal-transport',huge_decimal_transport),
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
        for name,zone in [('berlin','Europe/Berlin'),('brussels','Europe/Brussels'),('new-york','America/New_York')]:
            cases.append(('local-end-legacy-'+name,lambda c,p,z=zone:local_end_display(c,p,z,'0001-01-01T18:00','19:30',True)))
        for spelling in ['9007199254740993.0','9007199254740993e0','90071992547409930e-1','9.007199254740993E+15','0.9007199254740993e16']:
            cases.append(('integral-wire-'+spelling,lambda c,p,t=spelling:integral_wire_presentation(c,p,t)))
        cases.append(('opaque-unicode-identifiers',opaque_identifiers))
        for label,base,revision,stage,pair in [('historic-stage1',os.environ['S1_HIST_BASE'],os.environ['S1_HIST_REVISION'],1,False),('old-stage2-single',os.environ['S2_OLD_BASE'],os.environ['S2_OLD_REVISION'],2,False),('old-stage2-pair',os.environ['S2_OLD_BASE'],os.environ['S2_OLD_REVISION'],2,True)]:
            cases.append(('upgrade-'+label,lambda c,p,b=base,r=revision,s=stage,combined=pair:lost_response(c,p,combined,True,b,r,s)))
        cases.extend([('stage3-policy-history-product',policy_history_product),('stage3-manager-privacy',history_privacy_product),('stage3-independent-explanations',explanation_product),
          ('stage3-series-keyboard',series_product),('stage3-series-committed-loss',lambda c,p:series_product(c,p,drop=True)),('stage3-series-malformed-response',lambda c,p:series_product(c,p,malformed=True)),
          ('stage3-series-real-refusal',series_refusal_product),('stage3-series-changed-identity',series_changed_identity),
          ('stage3-pair-transition-history',pair_history_product),('stage3-series-read-race',series_read_race),('stage3-series-restaurant-labels',series_restaurant_labels),
          ('stage3-series-dst-berlin',lambda c,p:series_dst_refusal(c,p,'Europe/Berlin','2032-03-21')),
          ('stage3-series-dst-new-york',lambda c,p:series_dst_refusal(c,p,'America/New_York','2032-03-07')),
          ('stage3-accepted-stage1-upgrade-adoption',lambda c,p:upgraded_adoption(c,p,os.environ['S1_BASE'],os.environ['S1_REVISION'],stage=1)),
          ('stage3-historic-stage1-upgrade-adoption',lambda c,p:upgraded_adoption(c,p,os.environ['S1_HIST_BASE'],os.environ['S1_HIST_REVISION'],stage=1)),
          ('stage3-accepted-stage2-upgrade-adoption',lambda c,p:upgraded_adoption(c,p,os.environ['S2_ACCEPTED_BASE'],os.environ['S2_ACCEPTED_REVISION'])),
          ('stage3-accepted-stage2-pair-upgrade-adoption',lambda c,p:upgraded_adoption(c,p,os.environ['S2_ACCEPTED_BASE'],os.environ['S2_ACCEPTED_REVISION'],True))])
        prefix=os.environ.get('S2_SCENARIO_PREFIX')
        if prefix:
            cases=[(name,callback) for name,callback in cases if name.startswith(prefix)]
            if not cases:raise RuntimeError('No own supplemental scenario matches '+prefix)
            REPORT['supplemental_scope_prefix']=prefix
        for name,callback in cases: await scenario(name,callback,browser)
        REPORT["browser_version"]=browser.version
        await browser.close()
    REPORT["seconds"]=round(time.perf_counter()-start,3)
    REPORT["passed"]=sum(s["verdict"]=="PASS" for s in REPORT["scenarios"])
    REPORT["total"]=len(REPORT["scenarios"])
    (OUT/"browser-report.json").write_text(json.dumps(REPORT,indent=2)+"\n")
    print(json.dumps({k:REPORT[k] for k in ["candidate","passed","total","assertions","seconds","direct_http_operations","browser_originated_requests","forwarded_fetch_operations"]}))
    for s in REPORT["scenarios"]:
        print(s["verdict"],s["name"])
        if s["verdict"]=="FAIL": print(s["error"])
    raise SystemExit(0 if REPORT["passed"]==REPORT["total"] else 1)

if __name__=='__main__':
    asyncio.run(main())
