"""Owned file hashes and strictly scoped JSON/embedded-JSON privacy review."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.set_int_max_str_digits(0)
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];H=HERE/'candidate-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);assert not out.exists();manifest=[];objects=embedded=fingerprints=0;findings=[];classified=[];errors=[]
 for file in sorted(H.rglob('*')):
  if not file.is_file() or file==out:continue
  data=file.read_bytes();relative=str(file.relative_to(H));manifest.append(dict(path=relative,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
  if file.suffix!='.json' or any(part in ['context','own-client-context','source-inputs','executed-source'] for part in file.parts):continue
  try:value=json.loads(data)
  except Exception as exc:errors.append(dict(path=relative,type=type(exc).__name__));continue
  stack=[('',value)]
  while stack:
   loc,v=stack.pop()
   if isinstance(v,dict):
    objects+=1
    for key,item in v.items():
     at=loc+'/'+key
     if key.lower() in ['password','password_hash','token','tokens','state','authorization']:
      safe=isinstance(item,dict) and any('sha256' in k or 'fingerprint' in k for k in item)
      if safe:fingerprints+=1
      elif key=='tokens' and item is None and file.name in ['intake.json','release.json','browser-release.json','preflight.json'] and at in ['/tokens','/intake/tokens']:
       classified.append(dict(path=relative,pointer=at,classification='Explicit unknown model-usage metadata, not a session'))
      elif key=='tokens' and item is None and relative=='summary.json' and at=='/model/tokens':
       classified.append(dict(path=relative,pointer=at,classification='Explicit unknown model token-usage metadata'))
      elif key.lower()=='state' and isinstance(item,str) and item in ['completed','running','pending','pass','fail','failed','blocked'] and relative.startswith('official/'):
       classified.append(dict(path=relative,pointer=at,classification='Official harness execution state'))
      elif key=='State' and isinstance(item,dict) and {'Running','OOMKilled','Pid','StartedAt'}<=set(item) and relative=='cleanup-01/commands.json' and '/embedded-json/' in at:
       classified.append(dict(path=relative,pointer=at,classification='Actual own Docker inspection metadata'))
      elif item=='[private client value]':fingerprints+=1
      else:findings.append(dict(path=relative,pointer=at,value_type=type(item).__name__,sha256=hashlib.sha256(json.dumps(item,sort_keys=True).encode()).hexdigest()))
     stack.append((at,item))
   elif isinstance(v,list):stack.extend((loc+'/'+str(i),x) for i,x in enumerate(v))
   elif isinstance(v,str) and v[:1] in ['{','[']:
    try:nested=json.loads(v)
    except (ValueError,RecursionError):continue
    embedded+=1;stack.append((loc+'/embedded-json',nested))
 result=dict(candidate='91e2c471acded1b861b3fec725f202297b1c6740',file_count=len(manifest),json_object_records=objects,embedded_json_strings=embedded,private_or_credential_fingerprints=fingerprints,unclassified_private_payload_findings=findings,json_read_errors=errors,classified_nonprivate_fields=classified,manifest=manifest,scope='Owned saved JSON and valid embedded JSON strings; source/client context snapshots, source/log text, peer artifacts and genuine room export excluded. No universal secret-free claim. Self audit and later seal files excluded from this byte manifest.')
 out.write_text(json.dumps(result,indent=2)+'\n');assert not findings and not errors
 print(json.dumps({k:result[k] for k in ['file_count','json_object_records','embedded_json_strings','private_or_credential_fingerprints','unclassified_private_payload_findings','json_read_errors']}))
if __name__=='__main__':main()
