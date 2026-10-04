"""Fresh raw-wire reconstruction supplements; explicit named release gates execution.

Preparation imports construct only own fixtures/cases. The client parses shallow
public JSON with the independent exact-number oracle. Private exports stay raw.
"""
import argparse
import copy
import hashlib
import http.client
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'stage-1'))
from semantic_oracle import Number,parse,encode,same
from decoder_oracle import wrap,LEAF,LEAF_ALIAS,LEAF_DIFFERENT,LEAF_TYPED
from reconstruction_requirements import ACCEPTED,ORIGINS,SHAPES,DEPTHS

DAY='2035-06-04'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return encode(value).encode('utf-8')

def fixture(ids=('r','a','b','c'),capacity=8):
    rid,a,b,c=ids
    return dict(users=[dict(id='u',email='reconstruct@probe.invalid',password='independent-pass',display_name='Independent Diner')],
        restaurants=[dict(id=rid,name='Juniper Kitchen',timezone='UTC',slot_minutes=30,reservation_duration_minutes=90,cancellation_cutoff_minutes=0,
            opening_hours=[dict(weekday=day,opens='18:00',closes='23:00') for day in ('mon','tue','wed','thu','fri','sat','sun')],
            tables=[dict(id=a,label='Window Alcove',capacity=capacity),dict(id=b,label='Garden Bench',capacity=capacity),dict(id=c,label='Cedar Booth',capacity=capacity)],
            combinable=[[b,a]])],reservations=[])

def body(stage=2,table_ids=None,local=DAY+'T18:00',extra=None):
    ids=table_ids or ['a']
    value=dict(restaurant_id='r',starts_at_local=local,party_size=2)
    value.update(table_id=ids[0]) if stage==1 else value.update(table_ids=ids)
    if extra: value.update(extra)
    return encoded(value)

def deep_create(shape,depth,leaf=LEAF):
    # The whole envelope is shallow before injection; deep bytes are never decoded.
    shallow=body(table_ids=['b','a'])
    return shallow[:-1]+b',"ignored":'+wrap(shape,depth,leaf)+b'}'

def deep_moves(shape,depth,refs,leaf=LEAF):
    shallow=encoded({'moves':[dict(reference=refs[0],table_ids=['c']),dict(reference=refs[1],table_ids=['b','a'])]})
    return shallow[:-1]+b',"ignored":'+wrap(shape,depth,leaf)+b'}'

def validate_release(value):
    if not re.fullmatch('[0-9a-f]{40}',value.get('candidate','')): raise ValueError('full named candidate missing')
    if value.get('accepted_stage1')!=ACCEPTED: raise ValueError('accepted Stage 1 identity differs')
    if value.get('complete_package') is not True or value.get('end_received') is not True or value.get('execution_authorized') is not True:
        raise ValueError('complete later candidate package and execution release required')
    for field in ('systems_revision','interface_revision'):
        if not re.fullmatch('[0-9a-f]{40}',value.get(field,'')): raise ValueError('both substantive named builders required')
    if value.get('frozen_stage1_verified') is not True or value.get('offline_2cpu_2g_no_mounts_verified') is not True:
        raise ValueError('current independent source/resource proof required')
    for name in ('target','peer','third')+tuple(ORIGINS):
        url=value.get('urls',{}).get(name,'');parsed=urllib.parse.urlsplit(url)
        if parsed.scheme!='http' or not (parsed.hostname or '').startswith('independent-verifier-'):
            raise ValueError('only own constrained internal services permitted: '+name)
    for origin,(revision,_,_) in ORIGINS.items():
        if value.get('source_revisions',{}).get(origin)!=revision: raise ValueError('genuine source identity missing: '+origin)
    return value

class Wire:
    def __init__(self,out): self.trace=[];self.assertions=[];self.out=Path(out);self.request_count=0
    def call(self,url,method,path,raw=None,token=None,key=None,public=True):
        target=urllib.parse.urlsplit(url);headers={'Content-Type':'application/json; charset=utf-8'}
        if token: headers['Authorization']='Bearer '+token
        if key: headers['Idempotency-Key']=key
        began=time.monotonic();connection=http.client.HTTPConnection(target.hostname,target.port,timeout=10 if path.startswith('/_test/') else 5)
        try:
            connection.request(method,path,body=raw,headers=headers);response=connection.getresponse();payload=response.read()
            status=response.status;elapsed=time.monotonic()-began
        finally:connection.close()
        self.request_count+=1
        self.trace.append(dict(index=self.request_count,url=url,method=method,path=path,status=status,seconds=elapsed,
            request_bytes=len(raw or b''),request_sha256=sha(raw or b''),response_bytes=len(payload),response_sha256=sha(payload),
            authorization_present=bool(token),key_sha256=sha(key.encode()) if key else None,private_export_decoded=False if not public else None))
        value=parse(payload) if public and payload else None
        return status,value,payload
    def check(self,key,condition):
        self.assertions.append(dict(requirement_id='TK2R-'+key,passed=bool(condition)))
        if not condition: raise AssertionError(key)
    def setup(self,url,f=None):
        status,_,_=self.call(url,'POST','/_test/reset',encoded(f or fixture()))
        if status!=204:raise RuntimeError('legal fixture reset failed')
        status,value,_=self.call(url,'POST','/auth/login',encoded(dict(email='reconstruct@probe.invalid',password='independent-pass')))
        if status!=200:raise RuntimeError('genuine source login failed')
        return value['token']
    def export(self,url):
        status,_,raw=self.call(url,'GET','/_test/export',public=False)
        if status!=200:raise RuntimeError('export failed')
        return raw
    def transfer(self,source,dest,raw=None):
        raw=self.export(source) if raw is None else raw
        status,_,_=self.call(dest,'POST','/_test/import',raw,public=False)
        self.trace.append(dict(event='unchanged-raw-transfer',source=source,destination=dest,bytes=len(raw),sha256=sha(raw),decoded=False,status=status))
        return status
    def replay(self,url,path,raw,token,key,receipt):
        status,value,_=self.call(url,'POST',path,raw,token,key)
        return status==200 and same(value,receipt)

def origin_cases(w,release):
    urls=release['urls']
    for origin,(_,stage,profile) in ORIGINS.items():
        prefix=origin+'-';source=urls[origin];target=urls['target'];peer=urls['peer']
        token=w.setup(source)
        ids=['b','a'] if stage==2 else ['a']
        extra={'numeric_probe':Number('9007199254740993.0')}
        if stage==1:extra['table_ids']={'originally_ignored':True}
        raw=body(stage,ids,extra=extra);key='origin-create-'+origin
        status,receipt,_=w.call(source,'POST','/reservations',raw,token,key)
        w.check(prefix+'source',status==201)
        original_shape=('table_ids' in receipt)==(stage==2)
        ref=receipt['reference']
        status,second,_=w.call(source,'POST','/reservations',body(stage,['c']),token,'second-'+origin)
        if status!=201:raise RuntimeError('genuine companion booking failed')
        move={'reference':ref,'party_size':3}
        if stage==1:move['table_ids']='formerly ignored in batch'
        moves=encoded(dict(moves=[move,dict(reference=second['reference'])],numeric_probe=Number('9007199254740993.0')))
        move_key='origin-moves-'+origin
        status,move_receipt,_=w.call(source,'POST','/reservation-moves',moves,token,move_key)
        if status!=201:raise RuntimeError('genuine source move receipt failed')
        old_snapshot=w.export(source)
        obsolete_token=w.setup(target)
        w.check(prefix+'import',w.transfer(source,target,old_snapshot)==204)
        status,_,_=w.call(target,'GET','/reservations',token=token);w.check(prefix+'token',status==200)
        status,_,_=w.call(target,'GET','/reservations',token=obsolete_token)
        # The source and target reset created distinct actual sessions, not synthetic state.
        w.check(prefix+'destination-removed',status==401)
        status,_,_=w.call(target,'POST','/auth/login',encoded(dict(email='reconstruct@probe.invalid',password='independent-pass')));w.check(prefix+'password',status==200)
        status,current,_=w.call(target,'GET','/reservations/'+ref,token=token)
        w.check(prefix+'reference',status==200 and current['reference']==ref)
        status,single_current,_=w.call(target,'GET','/reservations/'+second['reference'],token=token)
        w.check(prefix+'current-single',status==200 and single_current.get('table_ids')==['c'] and single_current.get('table_id')=='c')
        w.check(prefix+'create-shape',original_shape and w.replay(target,'/reservations',raw,token,key,receipt))
        w.check(prefix+'moves-shape',w.replay(target,'/reservation-moves',moves,token,move_key,move_receipt))
        alias=raw.replace(b'9007199254740993.0',b'9007199254740992.0')
        status,value,_=w.call(target,'POST','/reservations',alias,token,key)
        expected=200 if profile=='python-json-v1' else 409
        w.check(prefix+'rounded-alias',status==expected and (status!=200 or same(value,receipt)))
        w.check(prefix+'numeric-profile',status==expected)
        integer_distinct=raw.replace(b'9007199254740993.0',b'9007199254740993')
        status,_,_=w.call(target,'POST','/reservations',integer_distinct,token,key)
        w.check(prefix+'integer-distinct',status==(409 if profile=='python-json-v1' else 200))
        status,_,_=w.call(target,'POST','/reservations',raw.replace(b'9007199254740993.0',b'true'),token,key)
        w.check(prefix+'bool-distinct',status==409)
        w.check(prefix+'ignored-original',w.replay(target,'/reservations',raw,token,key,receipt))
        new_invalid=encoded(dict(restaurant_id='r',table_id='a',table_ids=['a'],party_size=2,starts_at_local=DAY+'T18:00'))
        status,_,_=w.call(target,'POST','/reservations',new_invalid,token,'invalid-'+origin);w.check(prefix+'new-rule',status==422)
        status,_,_=w.call(target,'POST','/reservations',new_invalid,token,key);w.check(prefix+'key-priority',status==409)
        status,_,_=w.call(target,'PATCH','/reservations/'+ref,encoded(dict(party_size=4)),token)
        w.check(prefix+'amend-create',status==200 and w.replay(target,'/reservations',raw,token,key,receipt))
        status,_,_=w.call(target,'POST','/reservations/'+ref+'/cancel',encoded({}),token)
        w.check(prefix+'cancel-create',status==200 and w.replay(target,'/reservations',raw,token,key,receipt))
        w.check(prefix+'cancel-moves',w.replay(target,'/reservation-moves',moves,token,move_key,move_receipt))
        if stage==2:
            w.check(prefix+'pair-original',receipt.get('table_ids')==['b','a'] and 'table_id' not in receipt)
            w.check(prefix+'pair-current',current.get('table_ids')==['b','a'] and 'table_id' not in current)
            status,availability,_=w.call(target,'GET','/availability?restaurant_id=r&date='+DAY+'&party_size=2')
            w.check(prefix+'pair-cancel',status==200 and 'a' in availability['slots'][0]['available_table_ids'] and 'b' in availability['slots'][0]['available_table_ids'])
        newraw=body(table_ids=['b','a'],extra={'numeric_probe':Number('9007199254740993.0')})
        newkey='new-exact-'+origin
        status,newreceipt,_=w.call(target,'POST','/reservations',newraw,token,newkey);w.check(prefix+'mixed-new-exact',status==201)
        status,_,_=w.call(target,'POST','/reservations',newraw.replace(b'9007199254740993.0',b'9007199254740992.0'),token,newkey)
        w.check(prefix+'mixed-new-exact',status==409)
        mixed=w.export(target);w.check(prefix+'mixed-forward',w.transfer(target,peer,mixed)==204)
        w.check(prefix+'mixed-replay',w.replay(peer,'/reservations',raw,token,key,receipt) and w.replay(peer,'/reservations',newraw,token,newkey,newreceipt))
        alias_status,_,_=w.call(peer,'POST','/reservations',alias,token,key)
        exact_status,_,_=w.call(peer,'POST','/reservations',newraw.replace(b'9007199254740993.0',b'9007199254740992.0'),token,newkey)
        w.check(prefix+'mixed-replay',alias_status==expected and exact_status==409)
        w.check(prefix+'repeat-replacement',w.transfer(target,peer,mixed)==204 and w.replay(peer,'/reservation-moves',moves,token,move_key,move_receipt))
        bad=body(table_ids=['a'],local=DAY+'T20:00',extra={'party_size':Number('1.5')})
        status,_,_=w.call(peer,'POST','/reservations',bad,token,'failed-'+origin)
        status2,_,_=w.call(peer,'POST','/reservations',body(table_ids=['a'],local=DAY+'T20:00'),token,'failed-'+origin)
        w.check(prefix+'failed-key',status==422 and status2==201)
        w.setup(peer);status,_,_=w.call(peer,'GET','/reservations',token=token);w.check(prefix+'reset-clears',status==401)

def deep_cases(w,release):
    source,peer,third=(release['urls'][x] for x in ('target','peer','third'))
    for shape in SHAPES:
        for depth in DEPTHS:
            prefix=f'deep-{shape}-{depth}-';rawdeep=wrap(shape,depth)
            status,_,_=w.call(source,'POST','/_test/reset',encoded(fixture())[:-1]+b',"ignored":'+rawdeep+b'}')
            w.check(prefix+'reset',status==204)
            signup=encoded(dict(email='deep@probe.invalid',password='deep-independent',display_name='Deep Diner'))
            status,auth,_=w.call(source,'POST','/auth/signup',signup[:-1]+b',"ignored":'+rawdeep+b'}')
            w.check(prefix+'signup',status==201);token=auth['token']
            raw=deep_create(shape,depth);key=f'create-{shape}-{depth}'
            status,receipt,_=w.call(source,'POST','/reservations',raw,token,key);w.check(prefix+'create',status==201)
            w.check(prefix+'create-alias',w.replay(source,'/reservations',deep_create(shape,depth,LEAF_ALIAS),token,key,receipt))
            for label,leaf in [('create-different',LEAF_DIFFERENT),('create-type',LEAF_TYPED)]:
                status,_,_=w.call(source,'POST','/reservations',deep_create(shape,depth,leaf),token,key);w.check(prefix+label,status==409)
            status,second,_=w.call(source,'POST','/reservations',body(table_ids=['c']),token,'second')
            if status!=201:raise RuntimeError('deep companion failed')
            refs=[receipt['reference'],second['reference']];move=deep_moves(shape,depth,refs);move_key='moves'
            status,moved,_=w.call(source,'POST','/reservation-moves',move,token,move_key);w.check(prefix+'moves',status==201)
            w.check(prefix+'moves-alias',w.replay(source,'/reservation-moves',deep_moves(shape,depth,refs,LEAF_ALIAS),token,move_key,moved))
            status,before,_=w.call(source,'GET','/reservations/'+refs[1],token=token)
            status,after,_=w.call(source,'PATCH','/reservations/'+refs[1],encoded(dict(table_ids=['a','b'])),token)
            w.check(prefix+'moves-noop',status==200 and same(before,after))
            export=w.export(source);w.check(prefix+'export',len(export)>len(rawdeep))
            status,_,_=w.call(source,'POST','/reservations/'+refs[0]+'/cancel',encoded({}),token)
            w.check(prefix+'mutation',status==200 and w.replay(source,'/reservations',raw,token,key,receipt) and w.replay(source,'/reservation-moves',move,token,move_key,moved))
            w.check(prefix+'import',w.transfer(source,peer,export)==204)
            w.check(prefix+'peer-replay',w.replay(peer,'/reservations',raw,token,key,receipt) and w.replay(peer,'/reservation-moves',move,token,move_key,moved))
            w.check(prefix+'next-transfer',w.transfer(peer,third)==204 and w.replay(third,'/reservations',raw,token,key,receipt))
            before=w.export(third);status,_,_=w.call(third,'POST','/_test/import',export+b']',public=False)
            w.check(prefix+'bad-import',status==400 and before==w.export(third))
            status,_,_=w.call(third,'POST','/reservations',raw[:-1],token,'bad-grammar')
            status2,_,_=w.call(third,'GET','/health');w.check(prefix+'grammar-refusal',status==400 and status2==200 and before==w.export(third))
            fractional=body(table_ids=['a'],local=DAY+'T20:00',extra={'party_size':Number('1.5')})
            fractional=fractional[:-1]+b',"ignored":'+rawdeep+b'}'
            status,_,_=w.call(third,'POST','/reservations',fractional,token,'failed')
            good=body(table_ids=['a'],local=DAY+'T20:00');good=good[:-1]+b',"ignored":'+rawdeep+b'}'
            status2,_,_=w.call(third,'POST','/reservations',good,token,'failed')
            w.check(prefix+'failed-key',status==422 and status2==201)
            status,availability,_=w.call(third,'GET','/availability?restaurant_id=r&date='+DAY+'&party_size=16')
            w.check(prefix+'capacity',status==200 and any(same(o.get('capacity'),16) for slot in availability['slots'] for o in slot['available_options']))

def opaque_cases(w,release):
    from reconstruction_browser_protocol import opaque_ids
    from reconstruction_requirements import ID_CASES
    target,peer=(release['urls'][x] for x in ('target','peer'))
    for label in ID_CASES:
        prefix='opaque-'+label+'-';rid,a,b,c=opaque_ids(label);token=w.setup(target,fixture((rid,a,b,c)))
        w.check(prefix+'admission',True)  # setup's observed reset status is required.
        status,detail,_=w.call(target,'GET','/restaurants/'+urllib.parse.quote(rid,safe=''))
        w.check(prefix+'detail',status==200 and detail.get('id')==rid)
        query=urllib.parse.urlencode(dict(restaurant_id=rid,date=DAY,party_size='2'))
        status,availability,_=w.call(target,'GET','/availability?'+query)
        w.check(prefix+'query',status==200 and availability.get('restaurant_id')==rid)
        single=encoded(dict(restaurant_id=rid,table_id=a,party_size=2,starts_at_local=DAY+'T18:00'))
        status,receipt,_=w.call(target,'POST','/reservations',single,token,'single')
        w.check(prefix+'single-body',status==201 and receipt.get('table_ids')==[a] and receipt.get('table_id')==a)
        pair=encoded(dict(restaurant_id=rid,table_ids=[b,a],party_size=2,starts_at_local=DAY+'T20:00'))
        status,pair_receipt,_=w.call(target,'POST','/reservations',pair,token,'pair')
        w.check(prefix+'pair-body',status==201 and pair_receipt.get('table_ids')==[b,a] and 'table_id' not in pair_receipt)
        w.check(prefix+'replacement',w.transfer(target,peer)==204 and w.replay(peer,'/reservations',single,token,'single',receipt) and w.replay(peer,'/reservations',pair,token,'pair',pair_receipt))

def numeric_cases(w,release):
    from reconstruction_browser_protocol import token_spelling
    target=release['urls']['target']
    digits='9007199254740993';n=int(digits)
    for spelling in ('integer','decimal-integral','exponent-integral'):
        for seating in ('single','pair'):
            prefix=f'numeric-{spelling}-{seating}-';f=fixture();caps=[n,n-1,1] if seating=='single' else [n//2,n-n//2,1]
            for table,cap in zip(f['restaurants'][0]['tables'],caps):table['capacity']=Number(token_spelling(str(cap),spelling))
            token=w.setup(target,f);w.check(prefix+'fixture',True)
            ids=['a'] if seating=='single' else ['b','a']
            status,availability,_=w.call(target,'GET','/availability?restaurant_id=r&date='+DAY+'&party_size='+digits)
            selected=[o for o in availability['slots'][0]['available_options'] if o['table_ids']==ids]
            w.check(prefix+'options',status==200 and len(selected)==1 and same(selected[0]['capacity'],n))
            raw=body(table_ids=ids,extra={'party_size':Number(token_spelling(digits,spelling))})
            status,receipt,_=w.call(target,'POST','/reservations',raw,token,'numeric')
            w.check(prefix+'create',status==201 and isinstance(receipt.get('party_size'),Number) and same(receipt['party_size'],n))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--release',required=True);p.add_argument('--out',required=True)
    p.add_argument('--case',choices=['origins','deep','opaque','numeric','all'],default='all');p.add_argument('--execute',action='store_true')
    a=p.parse_args();release=validate_release(json.loads(Path(a.release).read_text()))
    if not a.execute:p.error('execution requires explicit --execute after complete release; no service calls made')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);w=Wire(out);errors=[];stopped=[];began=time.monotonic()
    try:
        if a.case in ('origins','all'):origin_cases(w,release)
        if a.case in ('deep','all'):deep_cases(w,release)
        if a.case in ('opaque','all'):opaque_cases(w,release)
        if a.case in ('numeric','all'):numeric_cases(w,release)
    except AssertionError as e:
        stopped.append(dict(type='stopped-after-recorded-failed-expectation',requirement_id=str(e),dependent_unexecuted_paths='unverified'))
    except Exception as e:errors.append(dict(type=type(e).__name__,message=str(e)))
    finally:
        (out/'assertions.json').write_text(json.dumps(w.assertions,indent=2)+'\n')
        (out/'trace.json').write_text(json.dumps(w.trace,indent=2)+'\n')
        summary=dict(candidate=release['candidate'],case=a.case,requests=w.request_count,assertions=len(w.assertions),failures=sum(not x['passed'] for x in w.assertions),runner_errors=errors,stopped_after_expectation=stopped,seconds=time.monotonic()-began,private_exports_saved=False)
        (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
    return bool(errors or summary['failures'])

if __name__=='__main__':raise SystemExit(main())
