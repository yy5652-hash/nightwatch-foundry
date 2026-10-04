"""Run independent probes on the exact already-started candidate; keep every exit/log."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--runtime',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--group',choices=['api','browser','upgrade-browser','boundaries','amend'],required=True)
    p.add_argument('--runner')
    a=p.parse_args()
    runtime=Path(a.runtime).resolve()
    facts=json.loads((runtime/'preflight.json').read_text())
    out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=False)
    network,runner,candidate=facts['network'],facts['runner_image'],facts['candidate']
    runner=a.runner or runner
    base,peer,legacy=[c['url'] for c in facts['containers']]
    commands=[]
    prefix=facts['prefix']+'-'+a.group
    def run(argv,label,required=False):
        t=time.monotonic()
        log=out/(label+'.log')
        with log.open('w') as h:
            result=subprocess.run(argv,stdout=h,stderr=subprocess.STDOUT)
        row=dict(label=label,argv=argv,returncode=result.returncode,seconds=time.monotonic()-t,log=str(log))
        commands.append(row); (out/'commands.json').write_text(json.dumps(commands,indent=2))
        print(json.dumps(row),flush=True)
        if required and result.returncode: raise RuntimeError(label+' setup failed')
        return result.returncode
    def probe(stage,script,label,extra=(),legacy_arg=False,positional=False):
        argv=['docker','run','--rm','--name',prefix+'-'+label,'--network',network,'--cpus','2','--memory','2g',
              '-v',str(out)+':/out','--entrypoint','python',runner,'/verifier/'+stage+'/'+script]
        if positional:
            argv.extend([base,candidate,peer])
        else:
            argv.extend(['--base',base,'--candidate',candidate,'--out','/out/'+label])
            argv.extend(extra)
            if legacy_arg: argv.extend(['--legacy',legacy])
        run(argv,label)
    if a.group=='api':
        probe('stage-1','probe.py','inherited',['--peer',peer])
        probe('stage-2','api.py','pairs',['--peer',peer])
        probe('stage-1','reproduce.py','original-minimal')
        probe('stage-1','reproduce_calendar.py','calendar-minimal')
        probe('stage-1','race50.py','race50')
        probe('stage-1','large_minutes.py','large-minutes',positional=True)
        probe('stage-2','upgrade_api.py','upgrade-api',['--peer',peer],legacy_arg=True)
    elif a.group=='browser':
        probe('stage-2','browser.py','browser')
    elif a.group=='boundaries':
        probe('stage-2','browser_boundaries.py','boundaries')
    elif a.group=='amend':
        probe('stage-2','amend_retained.py','amend-retained',['--peer',peer])
    else:
        probe('stage-2','browser_upgrade.py','upgrade-browser',['--legacy-revision','2a4b0408a3453bc87d86bca3d0ec571f479e03ca'],legacy_arg=True)
    (out/'run-summary.json').write_text(json.dumps(dict(candidate=candidate,group=a.group,commands=len(commands),
        nonzero=sum(bool(c['returncode']) for c in commands),seconds=sum(c['seconds'] for c in commands),runtime=str(runtime)),indent=2))
    raise SystemExit(any(c['returncode'] for c in commands))

if __name__=='__main__': main()
