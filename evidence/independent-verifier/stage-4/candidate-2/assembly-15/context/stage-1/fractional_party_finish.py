"""Audit and seal an existing supplemental run without repeating HTTP probes."""
import ast
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path
from fractional_party_requirements import SOURCE_LINES

sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent
TARGET=HERE/"candidate-5-supplemental-fraction"
old=TARGET/"coverage-before-source-line-correction.csv"
assert not old.exists()
shutil.copyfile(TARGET/"coverage.csv",old)
with (TARGET/"coverage.csv").open(newline="") as stream:
    reader=csv.DictReader(stream)
    fields=reader.fieldnames
    rows=list(reader)
for row in rows:
    row["source_line"]=SOURCE_LINES[row["requirement_id"].removeprefix("TK1-finite-party-")]
with (TARGET/"coverage.csv").open("w",newline="") as stream:
    writer=csv.DictWriter(stream,fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
(TARGET/"source-line-correction.json").write_text(json.dumps(dict(
    scope="Primary source-line links only; source sections, observations, verdicts and counts unchanged.",
    original="coverage-before-source-line-correction.csv",
    source="Unchanged kickoff/tablekeeper/spec/stage-1.md at official revision 803560d2a678ace1414465c098eb0ab5380ffade",
    mapping=SOURCE_LINES),indent=2))

secret={"token","tokens","sessions","password","password_hash","password_salt","salt","hash","state"}
fingerprints={"private_value_sha256","private_state_sha256","export_sha256","token_sha256","sha256","private_export_sha256"}
bad=[]
count=0
def walk(value,trail):
    if isinstance(value,dict):
        for key,child in value.items():
            if key in secret and child is not None and not isinstance(child,bool) and not (isinstance(child,dict) and set(child)<=fingerprints):
                bad.append(trail+"/"+key)
            walk(child,trail+"/"+key)
    elif isinstance(value,list):
        for index,child in enumerate(value): walk(child,trail+"/"+str(index))
for path in TARGET.rglob("*.json"):
    walk(json.loads(path.read_text()),str(path.relative_to(TARGET)))
    count+=1
assert not bad,bad
(TARGET/"private-artifact-audit.json").write_text(json.dumps(dict(
    json_files_checked=count,private_payload_paths=[],
    scope="All supplemental structured JSON; exported state and credentials are fingerprints. Synthetic fixture values in probe source are not exported credentials."),indent=2))

snapshots=TARGET/"final-helper-source"
snapshots.mkdir()
sources={}
for filename in ["fractional_party_probe.py","fractional_party_run.py","fractional_party_requirements.py","fractional_party_report.py","fractional_party_finish.py"]:
    source=(HERE/filename).read_bytes()
    ast.parse(source,filename=filename)
    (snapshots/filename).write_bytes(source)
    sources[filename]=hashlib.sha256(source).hexdigest()
(TARGET/"final-helper-hashes.json").write_text(json.dumps(sources,indent=2))
manifest=[dict(path=str(path.relative_to(TARGET)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
          for path in sorted(TARGET.rglob("*")) if path.is_file() and path.name!="artifact-manifest.json"]
(TARGET/"artifact-manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(json_files_checked=count,private_payload_paths=[],source_files_checked=len(sources),artifact_files=len(manifest))))
