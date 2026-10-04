"""Inspect retained JSON traces without exposing credentials in output."""
import hashlib
import json
import sys
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent
TARGET=HERE/"candidate-5"
secret={"token","tokens","sessions","password","password_hash","password_salt","salt","hash"}
fingerprints={"private_value_sha256","private_state_sha256","export_sha256","token_sha256","sha256","private_export_sha256"}
bad=[]
count=0
def walk(v,trail):
    if isinstance(v,dict):
        for k,x in v.items():
            if k in secret and x is not None and not isinstance(x,bool) and x != "[private client value]" and not (isinstance(x,dict) and set(x)<=fingerprints):
                bad.append(trail+"/"+k)
            walk(x,trail+"/"+k)
    elif isinstance(v,list):
        for i,x in enumerate(v): walk(x,trail+"/"+str(i))
for path in TARGET.rglob("*"):
    if path.suffix==".json":
        walk(json.loads(path.read_text()),str(path.relative_to(TARGET)))
        count+=1
    elif path.suffix==".jsonl":
        for i,line in enumerate(path.read_text().splitlines()):
            walk(json.loads(line),str(path.relative_to(TARGET))+":"+str(i+1))
        count+=1
print(json.dumps(dict(json_files_checked=count,private_payload_paths=bad)))
assert not bad,bad
(TARGET/"private-artifact-audit.json").write_text(json.dumps(dict(json_files_checked=count,private_payload_paths=[],credential_and_export_values="Only fingerprints retained; synthetic fixture passwords in source examples are not live exported credentials.",scope="Retained structured JSON and JSONL; original official logs and source documents were separately reviewed."),indent=2))
