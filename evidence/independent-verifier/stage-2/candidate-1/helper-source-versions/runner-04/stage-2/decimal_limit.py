"""Valid small JSON/decimal payloads beyond a language's unstated digit ceiling."""
import argparse,hashlib,http.client,json,time
from pathlib import Path
from urllib.parse import urlsplit
def main():
    p=argparse.ArgumentParser()
    for k in ['base','legacy','candidate','out']:p.add_argument('--'+k,required=True)
    a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    digit='1'+'0'*4299+'1'; operations=[];assertions=[];started=time.monotonic()
    fixture={'users':[],'restaurants':[{'id':'r','name':'Decimal Boundary Kitchen','timezone':'UTC','slot_minutes':30,'reservation_duration_minutes':90,'cancellation_cutoff_minutes':0,'opening_hours':[{'weekday':'mon','opens':'18:10','closes':'23:10'}],'tables':[{'id':'t','label':'Window','capacity':2}]}],'reservations':[]}
    def call(base,method,path,body=None):
        url=urlsplit(base);c=http.client.HTTPConnection(url.hostname,url.port,timeout=10 if path.startswith('/_test/') else 5)
        t=time.monotonic();c.request(method,path,body=body,headers={'Content-Type':'application/json; charset=utf-8'});r=c.getresponse();raw=r.read();c.close()
        value=json.loads(raw) if raw else None
        operations.append(dict(base=base,method=method,path=path,body=body,status=r.status,response=value,seconds=time.monotonic()-t))
        return r.status,value
    for stage,base in [('stage2',a.base),('frozen-stage1',a.legacy)]:
        for field in ['slot_minutes','reservation_duration_minutes','cancellation_cutoff_minutes','capacity']:
            body=json.dumps(fixture,separators=(',',':')).replace('"'+field+'":'+str(2 if field=='capacity' else 90 if field=='reservation_duration_minutes' else 30 if field=='slot_minutes' else 0),'"'+field+'":'+digit)
            # Exact fixture shape, valid decimal JSON number; no float/int conversion in the client.
            control=json.loads(body,parse_int=str)
            status,value=call(base,'POST','/_test/reset',body)
            assertions.append(dict(requirement_id='TK1-decimal-limit-'+stage+'-'+field,passed=status==204,expected={'status':204,'positive_decimal_digits':len(digit)},observed={'status':status,'body':value}))
        call(base,'POST','/_test/reset',json.dumps(fixture))
        path='/availability?restaurant_id=r&date=2035-06-04&party_size='+digit
        status,value=call(base,'GET',path)
        assertions.append(dict(requirement_id='TK1-decimal-limit-'+stage+'-query',passed=status==200 and all(s['available_table_ids']==[] for s in value.get('slots',[])),expected={'status':200,'available_table_ids':[]},observed={'status':status,'body':value}))
    for name,value in [('assertions',assertions),('operations',operations)]: (out/(name+'.json')).write_text(json.dumps(value,indent=2))
    summary=dict(candidate=a.candidate,frozen_stage1='2a4b0408a3453bc87d86bca3d0ec571f479e03ca',decimal_digits=len(digit),requests=len(operations),assertions=len(assertions),failures=sum(not x['passed']for x in assertions),duration_seconds=time.monotonic()-started)
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary));raise SystemExit(bool(summary['failures']))
if __name__=='__main__':main()
