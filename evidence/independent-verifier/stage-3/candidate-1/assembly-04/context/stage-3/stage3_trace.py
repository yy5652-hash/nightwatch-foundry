"""Deterministic finite reference operations and a future black-box comparator."""
from copy import deepcopy
from dataclasses import asdict
import random
from stage3_oracle import Model,Refusal
from stage3_requirements import SEED

def observation(model):
    return dict(policies=deepcopy(model.policies),restaurant_revision=model.restaurant_revision,
        bookings={ref:dict(seating=list(b.seating),starts_at_local=b.starts_at_local,party_size=b.party_size,
            status=b.status,revision=b.revision,accepted_terms=deepcopy(b.accepted_terms),
            history=deepcopy(b.history),exception=b.exception,series_id=b.series_id) for ref,b in model.bookings.items()},
        series={sid:asdict(s) for sid,s in model.series.items()})

def reference_trace(count=160,seed=SEED):
    rng=random.Random(seed);model=Model();operations=[]
    choices=[('a',),('b',),('c',),('a','b'),('c','b'),('a','c')]
    for index in range(count):
        kind=rng.choice(['create','create','move','cancel','publish','adopt']) if model.bookings else 'create'
        command=dict(index=index,operation=kind)
        before=observation(model)
        try:
            if kind=='create':
                ref='B'+str(index);seats=rng.choice(choices);local='2035-06-'+rng.choice(['04','05','06'])+'T'+rng.choice(['17:00','18:00','19:00','20:30'])
                party=rng.randrange(1,12);command.update(reference=ref,seating=list(seats),local=local,party_size=party)
                model.create(ref,seats,local,party);result='created'
            elif kind=='move':
                ref=rng.choice(list(model.bookings));moves=[dict(reference=ref,table_ids=list(rng.choice(choices)),party_size=rng.randrange(1,12))]
                if rng.randrange(4)==0:moves[0]['expected_revision']=model.bookings[ref].revision+1
                if len(model.bookings)>1 and rng.randrange(3)==0:
                    other=rng.choice([k for k in model.bookings if k!=ref]);moves.append(dict(reference=other,party_size=rng.randrange(1,12)))
                command['moves']=moves;result=dict(changed=model.batch(moves))
            elif kind=='cancel':
                ref=rng.choice(list(model.bookings));command['reference']=ref;result=dict(cancelled=model.cancel(ref))
            elif kind=='publish':
                day=rng.choice(['2035-06-01','2035-06-05','2035-06-20']);duration=rng.choice([30,60,90]);caps={k:rng.randrange(1,10) for k in model.tables}
                command.update(effective_from=day,duration=duration,capacities=caps)
                result=model.publish(day,reservation_duration_minutes=duration,capacities=caps)
            else:
                ref=rng.choice(list(model.bookings));count_value=rng.randrange(2,5);interval=rng.randrange(1,3)
                command.update(reference=ref,count=count_value,interval_weeks=interval);result=dict(series_id=model.adopt(ref,count_value,interval))
        except Refusal as refusal:
            result=dict(error=refusal.code)
            if before!=observation(model):raise AssertionError('reference refusal must be atomic')
        command['reference_result']=result;command['reference_after']=observation(model);operations.append(command)
    return dict(seed=seed,operations=operations,trace_kind='finite reference construction only; not candidate execution',
        limitations=['Abstract model owns only specified adoption/batch restaurant counter increments; other counter rules need source reconciliation.',
            'No endpoint type/permission/idempotency validation is inferred from these model transitions.'])

def compare_public(c,expected,references,series_ids):
    """Actual candidate values, never expected references fabricated on the server."""
    from stage3_probe import integer,raw,parse,same
    for label,record in expected['bookings'].items():
        actual=c.lookup(references[label]);history=c.history(references[label])['entries']
        checks=dict(seating=actual['table_ids']==record['seating'],local=actual['starts_at_local']==record['starts_at_local'],
            party=integer(actual['party_size'])==record['party_size'],status=actual['status']==record['status'],
            revision=integer(actual['revision'])==record['revision'],terms=same(actual['accepted_terms'],parse(raw(record['accepted_terms']))))
        for name,condition in checks.items():c.check('trace-'+label+'-'+name,condition)
        normalized=[{k:event[k] for k in ('seq','event','changes','revision','accepted_terms')} for event in history]
        c.check('trace-'+label+'-history',same(normalized,parse(raw(record['history']))))
    for label,s in expected['series'].items():
        actual=c.response('series-get-current',c.call('GET','/series/'+series_ids[label],token=c.tokens['u']),200)
        c.check('trace-'+label+'-revision',integer(actual['revision'])==s['revision'])
        c.check('trace-'+label+'-references',[x['reference'] for x in actual['occurrences']]==[references[x] for x in s['references']])
        c.check('trace-'+label+'-exceptions',[x['exception'] for x in actual['occurrences']]==[expected['bookings'][x]['exception'] for x in s['references']])

def execute_trace(c,trace):
    """Call only from a complete later release driver, never during construction."""
    from stage3_probe import create_body,policy
    c.setup();references={};series_ids={}
    for operation in trace['operations']:
        kind=operation['operation'];expected=operation['reference_result'];key='trace-'+str(operation['index'])
        if kind=='create':
            result=c.call('POST','/reservations',create_body(operation['seating'],operation['local'],operation['party_size']),token=c.tokens['u'],key=key)
            if result[0]==201:references[operation['reference']]=result[1]['reference']
        elif kind=='move':
            moves=[{**move,'reference':references[move['reference']]} for move in operation['moves']]
            result=c.call('POST','/reservation-moves',dict(moves=moves),token=c.tokens['u'],key=key)
        elif kind=='cancel':result=c.call('POST','/reservations/'+references[operation['reference']]+'/cancel',{},token=c.tokens['u'])
        elif kind=='publish':result=c.call('POST','/restaurants/r/policies',policy(operation['effective_from'],reservation_duration_minutes=operation['duration'],capacities=operation['capacities']),token=c.tokens['m'],key=key)
        else:
            result=c.call('POST','/series',dict(anchor_reference=references[operation['reference']],count=operation['count'],interval_weeks=operation['interval_weeks']),token=c.tokens['u'],key=key)
            if result[0]==201:
                sid=expected['series_id'];series_ids[sid]=result[1]['series_id']
                for i,occurrence in enumerate(result[1]['occurrences']):
                    label=operation['reference'] if i==0 else operation['reference']+'-'+str(i);references[label]=occurrence['reference']
        status,value,_=result
        if isinstance(expected,dict) and 'error' in expected:
            c.check('trace-refusal-'+str(operation['index']),status in (404,409,422) and value['error']['code']==expected['error'])
        else:c.check('trace-success-'+str(operation['index']),status==(200 if kind=='cancel' else 201))
        compare_public(c,operation['reference_after'],references,series_ids)
