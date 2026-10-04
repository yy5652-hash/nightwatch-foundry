"""Owned snapshot hashes and scoped saved-JSON privacy audit; no peer/source/log secret claim."""
import hashlib,json,sys
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent;H=HERE/'candidate-2';R=HERE.parents[2]
def main():
    output=H/'artifact-audit.json';manifest=[];objects=0;embedded=0;findings=[];fingerprints=0;classified=[]
    for file in sorted(H.rglob('*')):
        if not file.is_file() or file==output:continue
        raw=file.read_bytes();manifest.append(dict(path=str(file.relative_to(H)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
        if file.suffix!='.json' or any(part in ['context','own-client-context','source-inputs'] for part in file.parts):continue
        try:value=json.loads(raw)
        except Exception:continue
        stack=[('',value)]
        while stack:
            loc,v=stack.pop()
            if isinstance(v,dict):
                objects+=1
                for key,item in v.items():
                    if key.lower() in ['password','password_hash','token','tokens','state','authorization']:
                        safe=isinstance(item,dict) and any('sha256' in k or 'fingerprint' in k for k in item)
                        if safe:fingerprints+=1
                        elif key=='state' and (isinstance(item,str) and item in ['completed','running','pass','fail','pending'] or isinstance(item,dict) and ('Running' in item or 'Status' in item)):
                            classified.append(dict(path=str(file.relative_to(H)),pointer=loc+'/'+key,classification='Docker/harness runtime metadata'))
                        else:findings.append(dict(path=str(file.relative_to(H)),pointer=loc+'/'+key,value_type=type(item).__name__))
                    stack.append((loc+'/'+key,item))
            elif isinstance(v,list):stack.extend((loc+'/'+str(i),x) for i,x in enumerate(v))
            elif isinstance(v,str) and v[:1] in ['{','[']:
                try:nested=json.loads(v)
                except Exception:continue
                embedded+=1;stack.append((loc+'/embedded-json',nested))
    result=dict(candidate='4dba10246b07b2dda19de260d529f9d94ba0a1ed',file_count=len(manifest),json_object_records=objects,embedded_json_strings=embedded,private_or_credential_fingerprints=fingerprints,unclassified_private_payload_findings=findings,classified_runtime_state=classified,manifest=manifest,
        scope='Owned saved JSON and valid embedded JSON strings, excluding source-input snapshots and client/source context files. Source/log text, peer artifacts and genuine room export are not reviewed by this claim. Manifest excludes this self-referential audit file and later seals.',
        private_capture_correction='One inactive own test-session token was fingerprinted before commit in two uncommitted artifacts; invalidation/hash/count proof saved separately. No historical commit rewritten.')
    output.write_text(json.dumps(result,indent=2)+'\n');assert not findings
    print(json.dumps({k:result[k] for k in ['file_count','json_object_records','embedded_json_strings','private_or_credential_fingerprints','unclassified_private_payload_findings']}))
if __name__=='__main__':main()
