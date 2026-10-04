"""Preserve prospective original; Stage1 configuration has no declared pairs."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent; source=H.parent/'reconstruction_probe.py'
before=source.read_bytes();(H/'reconstruction-origin-01-executed-source.py').write_bytes(before)
old="newraw=body(table_ids=['b','a'],extra={'numeric_probe':Number('9007199254740993.0')})"
new="newraw=body(table_ids=['a'] if stage==1 else ['b','a'],extra={'numeric_probe':Number('9007199254740993.0')})"
assert before.decode().count(old)==1
source.write_text(before.decode().replace(old,new))
(H/'ORIGIN_CLIENT_CORRECTION.md').write_text('The first origins run records a failed expectation after 28 requests and 20 assertions. It expected a new combined booking on an imported Stage 1 fixture. Stage 1 legitimately ignored the unknown combinable field, so its genuine exported restaurant has no declared pair; Stage 2 correctly refused the undeclared combination. The new mixed exact receipt uses a singleton for either Stage 1 origin, retaining original configuration, and uses the declared pair for the old Stage 2 origin. No export is manufactured or modified. The first source/result stays preserved; subsequent execution uses a new output.\n')
print(json.dumps({'original_sha256':hashlib.sha256(before).hexdigest(),'corrected_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}))
