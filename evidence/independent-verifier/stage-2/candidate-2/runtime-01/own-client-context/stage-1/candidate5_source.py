"""Exact-revision source/provenance review; no builders' tests read."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parents[1]
CANDIDATE = "f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
OLD = "2a4b0408a3453bc87d86bca3d0ec571f479e03ca"
TARGET = HERE / "candidate-5"
SOURCE = TARGET / "source-inputs"
SOURCE.mkdir(exist_ok=True)
def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)
def snapshot(label, path, revision=CANDIDATE):
    data = git("show", revision+":"+path)
    (SOURCE / label).write_bytes(data)
    return dict(path=path, full_revision=revision, sha256=hashlib.sha256(data).hexdigest(), snapshot=str((SOURCE/label).relative_to(REPO)))

items = [snapshot("systems.md", "evidence/systems-engineer/stage-1-source-provenance.md"),
         snapshot("interface.md", "evidence/interface-engineer/stage-1-source-provenance.md"),
         snapshot("decimal-repair.md", "evidence/systems-engineer/stage-1-decimal-repair-05.md"),
         snapshot("timestamp-decision.md", "evidence/coordinator/timestamp-representation-decision.md"),
         snapshot("systems-handoff.txt", "evidence/coordinator/handoffs/TK-20261004-S1-systems-engineer-A.txt"),
         snapshot("interface-handoff.txt", "evidence/coordinator/handoffs/TK-20261004-S1-interface-engineer-A.txt")]
for label,path in [("participant-guide.md","docs/participant-guide.md"),("stage-1.md","tablekeeper/spec/stage-1.md")]:
    data = subprocess.check_output(["git","show","803560d2a678ace1414465c098eb0ab5380ffade:"+path],cwd=WORKSPACE/"kickoff")
    (SOURCE/label).write_bytes(data)
    items.append(dict(path="kickoff/"+path, full_revision="803560d2a678ace1414465c098eb0ab5380ffade", sha256=hashlib.sha256(data).hexdigest()))
brief = (WORKSPACE/"factory/PRODUCT_ACCEPTANCE.md").read_bytes()
(SOURCE/"PRODUCT_ACCEPTANCE.md").write_bytes(brief)
items.append(dict(path="factory/PRODUCT_ACCEPTANCE.md",sha256=hashlib.sha256(brief).hexdigest(),role="supplement only"))
spec = (SOURCE/"stage-1.md").read_text().strip()
assert all(spec in (SOURCE/name).read_text() for name in ["systems-handoff.txt","interface-handoff.txt"])
intake="2f691e8c7c43b3489717eb3ede1dadf0b0651b74"
(SOURCE/"intake-tree.txt").write_bytes(git("ls-tree","-r",intake))
(SOURCE/"intake-record.jsonl").write_bytes(git("show",intake+":evidence/coordinator/run-ledger.jsonl"))
assert len(git("rev-list","--parents","-1",intake).split()) == 1
assert b"stage-1/" not in (SOURCE/"intake-tree.txt").read_bytes()
files = ["core.py","server.py","Dockerfile","RUN.md",".dockerignore"]
hashes={f:hashlib.sha256(git("show",CANDIDATE+":stage-1/"+f)).hexdigest() for f in files}
assert all(git("show",CANDIDATE+":stage-1/"+f) == git("show",OLD+":stage-1/"+f) for f in files if f != "core.py")
diff=git("diff",OLD,CANDIDATE,"--","stage-1")
(SOURCE/"repair.diff").write_bytes(diff)
assert git("rev-parse",CANDIDATE+":stage-1") == git("rev-parse","78732dde56ba6116d0722136beba74b674811105:stage-1")
imports={}
for f in ["core.py","server.py"]:
    data=git("show",CANDIDATE+":stage-1/"+f).decode()
    parsed=ast.parse(data)
    imports[f]=sorted({module for n in ast.walk(parsed) for module in ([x.name for x in n.names] if isinstance(n,ast.Import) else [n.module] if isinstance(n,ast.ImportFrom) else [])})
    (SOURCE/f).write_text(data)
history=git("log","--format=%H %an <%ae> %s",CANDIDATE)
tree=git("ls-tree","-r",CANDIDATE)
(TARGET/"committed-history.txt").write_bytes(history)
(TARGET/"committed-tree.txt").write_bytes(tree)
assert not any(line.startswith((b"120000",b"160000")) for line in tree.splitlines())
engine=next(n for n in ast.parse((SOURCE/"core.py").read_text()).body if isinstance(n,ast.ClassDef) and n.name=="Engine")
init=next(n for n in engine.body if isinstance(n,ast.FunctionDef) and n.name=="__init__")
assert isinstance(init.body[0],ast.Expr) and ast.unparse(init.body[0]) == "sys.set_int_max_str_digits(0)"
record=dict(candidate=CANDIDATE,original_revoked_source=OLD,files=hashes,imports=imports,inputs=items,
    exact_core_repair_only=True,unchanged_interface_runtime=True,complete_initial_handoffs=True,empty_root_intake=True,
    stage_tree_matches_production_revision=True,symlink_or_submodule_entries=[],history_preserved=True,
    two_builders=all(r.encode() in history for r in ["e9e15076a762ab437d349cb3e6768b4786e1432f","9d53de905fdd498ee34dfa7c4d814b13dda7a921"]),
    construction_review="server.main constructs Engine before Server binds/accepts requests; core initialization is the sole new behavior. All other source bytes match the separately reviewed revoked Stage 1 source.",
    source_provenance_method="Full direct candidate package, complete source declarations/repair authoring-input report, initial handoffs, original empty intake, authored-path history, imports, current source/repair diff and dependency packaging reviewed. No builder probe/oracle implementation opened.",
    limitations="Seat exclusions are declarations, not machine-wide forensic proof. Runtime observations are still pending. Full room export remains operator-controlled.")
(TARGET/"source-audit.json").write_text(json.dumps(record,indent=2))
print(json.dumps(dict(candidate=CANDIDATE,source_review="complete",files=hashes,two_builders=record["two_builders"])))
