"""Lossless packaging of bulky derived observation indexes; original live bytes retained."""
import argparse,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;H=HERE/'candidate-2'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--restore',action='store_true');a=p.parse_args();manifest=H/'aggregate-archives.json'
    if a.restore:
        for row in json.loads(manifest.read_text()):
            blob=(H/row['archive']).read_bytes();assert sha(blob)==row['archive_sha256'];data=gzip.decompress(blob);assert sha(data)==row['original_sha256'];target=H/row['original']
            if target.exists():assert target.read_bytes()==data
            else:target.write_bytes(data)
        print('Seven exact derived indexes restored; no original overwritten');return
    assert not manifest.exists();rows=[]
    for n in range(4,11):
        original=H/('binding-'+str(n).zfill(2))/'all-observations.json';data=original.read_bytes();archive=original.with_suffix('.json.gz');assert not archive.exists();blob=gzip.compress(data,compresslevel=9,mtime=0);assert gzip.decompress(blob)==data;archive.write_bytes(blob)
        rows.append(dict(original=str(original.relative_to(H)),archive=str(archive.relative_to(H)),original_bytes=len(data),original_sha256=sha(data),archive_bytes=len(blob),archive_sha256=sha(blob),exact_roundtrip=True,original_live_file_preserved=True))
    manifest.write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(dict(archives=len(rows),original_bytes=sum(x['original_bytes'] for x in rows),packaged_bytes=sum(x['archive_bytes'] for x in rows),exact=True)))
if __name__=='__main__':main()
