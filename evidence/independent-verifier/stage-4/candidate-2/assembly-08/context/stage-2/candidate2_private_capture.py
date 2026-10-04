"""Invalidate-check and fingerprint own uncommitted test-session capture, without printing values."""
import argparse,hashlib,http.client,json,sys
from pathlib import Path
from urllib.parse import urlsplit
sys.set_int_max_str_digits(0)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');a=p.parse_args()
    root=Path('/evidence') if a.verify else Path(__file__).resolve().parent/'candidate-2'
    file=root/'http-01/numeric.json';data=json.loads(file.read_text());tokens=set()
    def walk(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k=='token' and isinstance(x,str):tokens.add(x)
                walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(data)
    if a.verify:
        release=json.loads(Path('/release.json').read_text());observations=[]
        for token in tokens:
            for name in ['target','peer','third']:
                parsed=urlsplit(release['urls'][name]);c=http.client.HTTPConnection(parsed.hostname,parsed.port,timeout=5)
                try:
                    c.request('GET','/reservations',headers={'Authorization':'Bearer '+token});r=c.getresponse();r.read();status=r.status
                finally:c.close()
                observations.append(dict(credential_sha256=sha(token.encode()),destination=name,status=status))
                assert status==401
        print(json.dumps(dict(unique_test_sessions=len(tokens),observations=observations,all_inactive=True)));return
    proof=json.loads((root/'private-capture-invalidation.json').read_text());assert proof['all_inactive']
    files=[]
    def redact(v):
        if isinstance(v,dict):return {k:({'private_value_sha256':sha(x.encode())} if k=='token' and isinstance(x,str) else redact(x)) for k,x in v.items()}
        if isinstance(v,list):return [redact(x) for x in v]
        return v
    for name in ['numeric.json','numeric.log']:
        file=root/'http-01'/name;original=file.read_bytes();value=json.loads(original);clean=redact(value);encoded=(json.dumps(clean,indent=2)+'\n').encode()
        assert value['assertions']==clean['assertions'] and value['failed_assertions']==clean['failed_assertions']==0 and value['http_operations']==clean['http_operations']
        file.write_bytes(encoded);files.append(dict(path=str(file.relative_to(root)),original_sha256=sha(original),fingerprinted_sha256=sha(encoded),observed_operations=value['http_operations'],assertions=value['assertions'],failed_assertions=0))
    (root/'PRIVATE_CAPTURE_CORRECTION.json').write_text(json.dumps(dict(candidate=data['candidate_full_revision'],scope='Own uncommitted numeric client JSON/stdout only; execution source, checks/status/timing/numeric values unchanged.',unique_inactive_test_sessions=len(tokens),files=files,history='These raw artifacts had not been committed. All sessions verified401 against three independent current destinations before fingerprinting. No real host/account credential inspected.',future_reproduction='Original sealed own protocol is preserved exactly; fingerprint its private response token fields before retaining/publishing reproduction output.'),indent=2)+'\n')
    print(json.dumps(dict(fingerprinted_files=len(files),inactive_sessions=len(tokens))))
if __name__=='__main__':main()
