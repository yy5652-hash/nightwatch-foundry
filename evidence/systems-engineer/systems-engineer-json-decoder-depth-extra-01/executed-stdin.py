import importlib.util,json,pathlib,time,sys,hashlib
path=pathlib.Path('stage-1/json_codec.py'); spec=importlib.util.spec_from_file_location('own_codec_boundary',path); codec=importlib.util.module_from_spec(spec); sys.modules[spec.name]=codec;spec.loader.exec_module(codec)
out=pathlib.Path('evidence/systems-engineer/systems-engineer-json-decoder-depth-extra-01');out.mkdir();rows=[]
for depth in (2500,3000,4000,5000):
 wire=b'['*depth+b'1e4300'+b']'*depth;start=time.monotonic()
 try: codec.loads(wire);result='decoded'
 except Exception as e:result=type(e).__name__+':'+str(e)
 rows.append({'depth':depth,'bytes':len(wire),'sha256':hashlib.sha256(wire).hexdigest(),'valid_by_balanced_array_composition':True,'result':result,'seconds':time.monotonic()-start})
(out/'observations.json').write_text(json.dumps({'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'recursion_limit':sys.getrecursionlimit(),'scope':'codec only; no HTTP','rows':rows},indent=2)+'\n');print(rows)
