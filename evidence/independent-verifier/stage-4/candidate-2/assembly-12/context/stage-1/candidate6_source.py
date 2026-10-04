"""Named production/provenance audit; reads no builder probe implementation."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2];WORKSPACE=REPO.parents[1]
CANDIDATE="ab0cf79767b6768153a73894bf5768bf3328491a";PRODUCTION="debff0bbf2625936d30e1e11066b966a46320137"
TARGET=HERE/"candidate-6";SOURCE=TARGET/"source-inputs";SOURCE.mkdir(exist_ok=True)
commands=[]
def git(*args,cwd=REPO):
    argv=["git",*args];result=subprocess.check_output(argv,cwd=cwd)
    commands.append(dict(argv=argv,cwd=str(cwd),returncode=0,output_sha256=hashlib.sha256(result).hexdigest()))
    return result
items=[]
def snapshot(label,path,revision=CANDIDATE):
    data=git("show",revision+":"+path);(SOURCE/label).write_bytes(data)
    items.append(dict(path=path,revision=revision,sha256=hashlib.sha256(data).hexdigest(),snapshot=str((SOURCE/label).relative_to(REPO))))
    return data
for seat in ["systems-engineer","interface-engineer"]:
    snapshot(seat+"-initial-handoff.txt","evidence/coordinator/handoffs/TK-20261004-S1-"+seat+"-A.txt")
    snapshot(seat+"-source-provenance.md","evidence/"+seat+"/stage-1-source-provenance.md")
spec=(SOURCE/"stage-1.md").read_text().strip()
assert all(spec in (SOURCE/(s+"-initial-handoff.txt")).read_text() for s in ["systems-engineer","interface-engineer"])
intake="2f691e8c7c43b3489717eb3ede1dadf0b0651b74"
(SOURCE/"initial-tree.txt").write_bytes(git("ls-tree","-r",intake))
assert len(git("rev-list","--parents","-1",intake).split())==1
assert b"stage-1/" not in (SOURCE/"initial-tree.txt").read_bytes()
tree=git("ls-tree","-r",CANDIDATE);history=git("log","--format=%H %an <%ae> %s",CANDIDATE)
(TARGET/"committed-tree.txt").write_bytes(tree);(TARGET/"committed-history.txt").write_bytes(history)
assert not any(line.startswith((b"120000",b"160000")) for line in tree.splitlines())
assert git("rev-parse",CANDIDATE+":stage-1").decode().strip()=="d2905df39546a619afbad3547b10205bb6c01610"
assert git("rev-parse",CANDIDATE+":stage-1")==git("rev-parse",PRODUCTION+":stage-1")
files={};imports={}
for name in ["core.py","server.py","json_codec.py","Dockerfile","RUN.md",".dockerignore"]:
    data=snapshot(name,"stage-1/"+name);files[name]=hashlib.sha256(data).hexdigest()
    if name.endswith(".py"):
        parsed=ast.parse(data.decode())
        imports[name]=sorted({m for n in ast.walk(parsed) for m in ([x.name for x in n.names] if isinstance(n,ast.Import) else [n.module] if isinstance(n,ast.ImportFrom) else [])})
wiring="3dae12788ff59dce8c4ce8a6faa71394f140e3d2"
assert all(git("show",CANDIDATE+":stage-1/"+f)==git("show",wiring+":stage-1/"+f) for f in ["server.py","Dockerfile",".dockerignore","RUN.md"])
authors={}
for revision in ["e9e15076a762ab437d349cb3e6768b4786e1432f","9d53de905fdd498ee34dfa7c4d814b13dda7a921","00940d4777c316c1369e744109885d58c85373ec",wiring,PRODUCTION]:
    authors[revision]=git("show","--format=%H %an <%ae>","--name-only",revision).decode()
kickoff_head=git("rev-parse","HEAD",cwd=WORKSPACE/"kickoff").decode().strip()
assert kickoff_head=="803560d2a678ace1414465c098eb0ab5380ffade"
assert not git("status","--porcelain=v1",cwd=WORKSPACE/"kickoff")
review=dict(
    transport="Full server review: strict UTF8/object JSON framing; agreed loads/dumps bytes; serialized payload complete before headers; byte lengths; zero-byte204; default8080 and PORT/all-interface listener; lost response does not redispatch.",
    transactions="Full core review: one RLock includes reads and recursive-value retry checks; proposed records/body/receipt snapshots prepared before committing; detached copy_json result captured inside lock; replacement candidate validated before state assignment.",
    numbers="Full codec/core review: exact coefficient/exponent values and integral predicates; compact comparisons before bounded calendar materialization; booleans separate; per-receipt exact/legacy profiles; input integer provenance preserved; unchanged archived responses.",
    decoder_risk="loads uses standard json.loads and catches RecursionError as syntax refusal. Iterative later copying/comparison/encoding does not establish unrestricted decoding; independent bounded high-depth HTTP failures are separate current evidence.",
    clock_boundary="Source supplemental only: current-start cutoff compares exact remaining absolute microseconds <= configured cutoff; cancelled-before-cutoff and input-order batch validation are visible. No clock-control API or exact instantaneous threshold HTTP claim.",
    provenance="Complete task/spec/brief/decisions, full named source, initial handoffs, declarations, original empty root, imports and authored path history reviewed. Builder handoff outcomes are received evidence, not independent test results; no builder probe implementation read.")
record=dict(candidate=CANDIDATE,production_revision=PRODUCTION,stage_tree="d2905df39546a619afbad3547b10205bb6c01610",files=files,imports=imports,inputs=items,
    complete_initial_handoffs=True,empty_root_intake=True,unchanged_interface_runtime=True,stage_tree_matches_production_revision=True,
    symlink_or_submodule_entries=[],history_preserved=True,two_builders=all(r.encode() in history for r in authors),authors=authors,review=review,
    kickoff_head=kickoff_head,kickoff_clean=True,
    shared_index_deviation="182582c committed verifier-authored preparation under Interface Git identity; no attribution rewrite. Verifier seal/provenance b9174e and Interface audit0a643d retained; production module belonged to intervening Systems parentc2fcedc.",
    initial_intake_correction="Initial single basename provenance capture retained as Interface copy; both separately named exact source declarations are now preserved. END marker belongs to received message wrapper; initial unsupported file-END assertion is retained separately.",
    limitations="Declarations do not prove machine-wide exclusion. Source supplements are labelled and not HTTP counts; unseen judging and genuine full room export remain unavailable/operator-controlled.")
(TARGET/"source-audit.json").write_text(json.dumps(record,indent=2));(TARGET/"source-audit-commands.json").write_text(json.dumps(commands,indent=2))
print(json.dumps(dict(candidate=CANDIDATE,source_review="complete",two_builders=record["two_builders"],files=files)))
