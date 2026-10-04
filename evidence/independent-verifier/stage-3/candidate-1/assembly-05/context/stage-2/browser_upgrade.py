"""Real old-API login/create, unchanged UI pending request, genuine state upgrade."""
import argparse
import asyncio
import json
import time
from urllib.parse import urlsplit
from playwright.async_api import async_playwright, expect
from browser import BrowserProbe
from api import pair_fixture


class UpgradeProbe(BrowserProbe):
    async def upgrade(self):
        f=pair_fixture()
        for restaurant in f["restaurants"]:
            restaurant.pop("combinable")
        status,_=await self.api("POST","/_test/reset",f,base=self.args.legacy)
        if status!=204:
            raise RuntimeError("Frozen source reset failed")
        context,page=await self.page()
        original={}
        routing={'upgraded':False}
        try:
            async def source_api(route):
                request=route.request
                parsed=urlsplit(request.url)
                if routing['upgraded'] or not parsed.path.startswith(('/auth/','/restaurants','/availability','/reservations','/reservation-moves')):
                    await route.continue_(); return
                target=parsed.path+('?' + parsed.query if parsed.query else '')
                headers={k:v for k,v in request.headers.items() if k in {'authorization','idempotency-key','content-type','accept'}}
                response=await self.http.fetch(self.args.legacy+target,method=request.method,headers=headers,data=request.post_data,timeout=5000)
                payload=await response.body()
                self.actions.append(dict(event='genuine-source-api-proxy',method=request.method,path=target,status=response.status))
                # Forward the actual old-service bytes; no state/response construction.
                await route.fulfill(status=response.status,headers={'content-type':response.headers.get('content-type','application/json; charset=utf-8')},body=payload)
            await page.route('**/*',source_api)
            await self.login(page)
            await self.open_form(page,"single")
            before_url=page.url
            form_value=await page.get_by_test_id("booking-party-size").input_value()
            summary=await self.text(page,"booking-summary")
            async def old_commit(route):
                request=route.request
                body=request.post_data_json
                original["body"]=body
                original["key"]=request.headers.get("idempotency-key")
                if "table_id" not in body or "table_ids" in body:
                    original["protocol_unavailable"]="Frozen Stage 1 requires a legacy singleton body; the actual UI request cannot be committed unchanged on that source. No body was adapted or successful receipt fabricated."
                    await route.abort("connectionfailed")
                    return
                token=request.headers.get("authorization","").removeprefix("Bearer ")
                status,receipt=await self.api("POST","/reservations",body,token=token,key=original["key"],base=self.args.legacy)
                original["receipt"]=receipt
                original["status"]=status
                await route.abort("connectionfailed")
            await page.route("**/reservations",old_commit,times=1)
            await page.get_by_test_id("booking-submit").click()
            await expect(page.get_by_test_id("booking-uncertain")).to_be_visible()
            await self.shot(page,"upgrade-before-import-uncertain")
            if original.get("protocol_unavailable"):
                self.actions.append(dict(event="upgrade-protocol-unavailable",reason=original["protocol_unavailable"],actual_body=original["body"],key=original["key"]))
                self.pending_protocol=True
                return
            if original.get("status")!=201:
                raise RuntimeError("Real frozen-source booking was refused")
            _,snapshot=await self.api("GET","/_test/export",base=self.args.legacy)
            self.check("stage1-genuine-export",snapshot.get("track")=="tablekeeper" and snapshot.get("format_version")==1)
            status,_=await self.api("POST","/_test/import",snapshot)
            self.check("stage1-import",status==204)
            routing['upgraded']=True
            self.check("upgrade-browser-identity","Diner A" in await self.text(page,"current-user"))
            self.check("upgrade-browser-form",page.url==before_url and await page.get_by_test_id("booking-party-size").input_value()==form_value and await self.text(page,"booking-summary")==summary)
            status,receipt=await self.submit(page)
            await expect(page.get_by_test_id("confirmation")).to_be_visible()
            current=self.requests[-1]
            self.check("upgrade-browser-key",current["key"]==original["key"])
            self.check("upgrade-browser-body",current["body"]==original["body"])
            self.check("upgrade-browser-original",status==200 and receipt==original["receipt"] and await self.text(page,"confirmation-reference")==original["receipt"]["reference"])
            await self.shot(page,"upgrade-recovered-original")
            await page.goto(self.args.base+"/lookup")
            await page.get_by_test_id("lookup-reference-input").fill(original["receipt"]["reference"])
            await page.get_by_test_id("lookup-submit").click()
            await expect(page.get_by_test_id("reservation-detail")).to_be_visible()
            self.check("upgrade-browser-lookup",await self.visible(page,"reservation-detail") and await self.text(page,"reservation-status")=="confirmed" and "Diner A" in await self.text(page,"current-user"))
        finally:
            await context.close()

    async def run(self):
        self.pending_protocol=False
        async with async_playwright() as runtime:
            self.http=await runtime.request.new_context()
            self.browser=await runtime.chromium.launch(headless=True)
            try:
                await self.upgrade()
            except Exception as error:
                self.results.append(dict(requirement_id="BROWSER-CASE-upgrade",passed=False,expected="real upgrade case completes",observed=str(error)))
            await self.browser.close()
            await self.http.dispose()
        for name,value in [("assertions",self.results),("browser-actions",self.actions),("http-operations",self.operations),("browser-network",self.network)]:
            (self.out/(name+".json")).write_text(json.dumps(value,indent=2))
        summary=dict(stage=2,candidate=self.args.candidate,source_revision=self.args.legacy_revision,assertions=len(self.results),failures=sum(not x["passed"] for x in self.results),
                     pending_protocol=self.pending_protocol,duration_seconds=time.monotonic()-self.started)
        (self.out/"summary.json").write_text(json.dumps(summary,indent=2))
        print(json.dumps(summary))
        return 2 if self.pending_protocol else bool(summary["failures"])


def main():
    parser=argparse.ArgumentParser()
    for field in ["base","legacy","legacy-revision","candidate","out"]:
        parser.add_argument("--"+field,required=True)
    args=parser.parse_args()
    if args.legacy_revision!="2a4b0408a3453bc87d86bca3d0ec571f479e03ca":
        parser.error("Use the frozen accepted Stage 1 source.")
    if len(args.candidate)!=40 or any(c not in "0123456789abcdef" for c in args.candidate):
        parser.error("A full named committed candidate is required.")
    raise SystemExit(asyncio.run(UpgradeProbe(args).run()))


if __name__=="__main__":
    main()
