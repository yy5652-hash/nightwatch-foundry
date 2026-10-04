"""Own isolated browser dependency smoke; no app or candidate interaction."""
import json
import argparse
import subprocess
import time
from pathlib import Path

PROGRAM="""
import asyncio,json
from playwright.async_api import async_playwright
import api,browser
async def main():
    async with async_playwright() as runtime:
        browser=await runtime.chromium.launch(headless=True)
        context=await browser.new_context(viewport={'width':375,'height':812})
        page=await context.new_page()
        width=await page.evaluate('innerWidth')
        assert width==375
        print(json.dumps({'chromium_version':browser.version,'viewport_width':width,'imports':['api','browser'],'candidate_calls':0}))
        await browser.close()
asyncio.run(main())
"""


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--attempt",required=True)
    parser.add_argument("--image",required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent
    log=root/("helper-smoke-"+args.attempt+".log")
    facts_path=root/("helper-smoke-"+args.attempt+".json")
    if log.exists() or facts_path.exists():
        parser.error("Choose a new attempt; preserve earlier outputs.")
    argv=["docker","run","--rm","--name","independent-verifier-s2-helper-smoke-"+args.attempt,"--network","none","--cpus","2","--memory","2g",
          "--entrypoint","python",args.image,"-c",PROGRAM]
    start=time.monotonic()
    result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    log.write_text(result.stdout)
    facts=dict(argv=argv,returncode=result.returncode,duration_seconds=time.monotonic()-start,candidate_calls=0,note="Verifier helper only; no service startup or requirement pass implied")
    facts_path.write_text(json.dumps(facts,indent=2))
    print(json.dumps(facts))
    raise SystemExit(result.returncode)


if __name__=="__main__":
    main()
