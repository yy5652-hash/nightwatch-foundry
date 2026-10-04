"""Six writes × six reads with saved client intervals and valid serial states.

The writer holds its final body byte until the reader is released. This records
client overlap, not unobservable internal lock or serializer timing. Raw exports
stay in memory and are forwarded unchanged before independently reading the peer.
"""
import argparse,json,http.client,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from stage3_probe import Client,raw,parse,same,sha,fixture,policy,create_body,validate_release,integer,DAY

def main():
 p=argparse.ArgumentParser();p.add_argument('--release',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 release=validate_release(json.loads(Path(a.release).read_text()));c=Client(release['urls']['target'],a.out,release['candidate']);error=None
 try:
  for op in ('create','patch','cancel','moves','policy','series'):
   for read in ('lookup','list','history','decision','availability','raw-export'):
    c.setup();anchor=c.create(seats=('b','a'),party=5);other=c.create(seats=('c',),key='other');ref=anchor['reference']
    paths=dict(lookup='/reservations/'+ref,list='/reservations',history='/reservations/'+ref+'/history',decision='/reservations/'+ref+'/decision',
     availability='/availability?restaurant_id=r&date='+DAY+'&party_size=5&explain=true',**{'raw-export':'/_test/export'})
    path=paths[read];token=None if read in ('availability','raw-export') else c.tokens['u'];private=read=='raw-export'
    before=c.call('GET',path,token=token,decode=not private)
    public_before=c.public_state()
    method='POST';write_path='/reservations';key='race';write_token=c.tokens['u']
    if op=='create':body=create_body(('c',),DAY+'T20:00',2)
    elif op=='patch':method='PATCH';write_path='/reservations/'+ref;body=dict(party_size=6);key=None
    elif op=='cancel':write_path='/reservations/'+ref+'/cancel';body={};key=None
    elif op=='moves':write_path='/reservation-moves';body=dict(moves=[dict(reference=ref,table_ids=['c']),dict(reference=other['reference'],table_ids=['b','a'])])
    elif op=='policy':write_path='/restaurants/r/policies';body=policy(reservation_duration_minutes=30);write_token=c.tokens['m']
    else:write_path='/series';body=dict(anchor_reference=ref,count=3,interval_weeks=1)
    data=raw(body);ready=threading.Event();go=threading.Event();record={};reader=Client(c.base,c.out,c.candidate)
    def writer():
     target=urlsplit(c.base);connection=http.client.HTTPConnection(target.hostname,target.port,timeout=5);began=time.monotonic()
     try:
      connection.putrequest(method,write_path);connection.putheader('Content-Type','application/json; charset=utf-8');connection.putheader('Content-Length',str(len(data)))
      connection.putheader('Authorization','Bearer '+write_token)
      if key is not None:connection.putheader('Idempotency-Key',key)
      connection.endheaders();connection.send(data[:-1]);record['prefix_sent_at']=time.monotonic();ready.set()
      if not go.wait(5):raise RuntimeError('reader gate not released')
      record['final_byte_sent_at']=time.monotonic();connection.send(data[-1:]);response=connection.getresponse();payload=response.read()
      record.update(method=method,path=write_path,status=response.status,began_at=began,ended_at=time.monotonic(),request_bytes=len(data),request_sha256=sha(data),response_sha256=sha(payload))
      return response.status,parse(payload)
     finally:connection.close()
    def capture():
     if not ready.wait(5):raise RuntimeError('writer prefix gate not reached')
     began=time.monotonic();go.set();result=reader.call('GET',path,token=token,decode=not private)
     record['reader_began_at']=began;record['reader_ended_at']=time.monotonic();return result
    with ThreadPoolExecutor(max_workers=2) as pool:
     wf=pool.submit(writer);rf=pool.submit(capture);captured=rf.result();written=wf.result()
    c.count+=1+reader.count;c.trace.extend(reader.trace);c.trace.append(dict(event='held-final-byte-race',operation=op,read=read,**record))
    c.check('moves-concurrency-'+op+'-'+read+'-write',written[0]==(200 if op in ('patch','cancel') else 201))
    after=c.call('GET',path,token=token,decode=not private);public_after=c.public_state()
    if private:
     c.check('moves-concurrency-'+op+'-'+read,same(parse(captured[2]),parse(before[2])) or same(parse(captured[2]),parse(after[2])))
     c.response('upgrade-raw-transfer',c.transfer(c.base,release['urls']['peer'],captured[2]),204)
     original_base=c.base;c.base=release['urls']['peer'];peer_public=c.public_state();c.base=original_base
     c.check('moves-concurrency-'+op+'-'+read+'-peer',same(peer_public,public_before) or same(peer_public,public_after))
    else:c.check('moves-concurrency-'+op+'-'+read,captured[0]==200 and (same(captured[1],before[1]) or same(captured[1],after[1])))
  c.setup();barrier=threading.Barrier(50)
  def publish(i):
   client=Client(c.base,c.out,c.candidate);barrier.wait();result=client.call('POST','/restaurants/r/policies',policy(),token=c.tokens['m'],key='distinct-'+str(i));return result,client.trace
  with ThreadPoolExecutor(max_workers=50) as pool:results=list(pool.map(publish,range(50)))
  c.check('policies-contiguous-version',all(result[0][0]==201 for result in results) and sorted(integer(result[0][1]['policy_version']) for result in results)==list(range(1,51)))
  c.count+=50;c.trace.extend(dict(event='distinct-policy-worker',trace=t) for _,t in results)
 except BaseException as exc:error=dict(kind='failed-expectation' if isinstance(exc,AssertionError) else 'runner-exception',type=type(exc).__name__,message=str(exc));raise
 finally:c.save(error)
if __name__=='__main__':main()
