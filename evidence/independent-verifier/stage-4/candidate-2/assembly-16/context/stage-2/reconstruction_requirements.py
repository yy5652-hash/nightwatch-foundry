"""Prospective cumulative ledger. Historical evidence is never a current pass."""
import csv
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACCEPTED = '75005d57fe0904753eac4eab5bf4e4c9a78b6d1b'
PENDING = 'PENDING_COMPLETE_NAMED_STAGE2_CANDIDATE'
ORIGINS = {
    'legacy-s1': ('49287b4a5a1481f995c470ccae31776f03d4b863', 1, 'python-json-v1'),
    'legacy-s2': ('4b92041057beb669d2e6c528e8268f4d0d1e6421', 2, 'python-json-v1'),
    'exact-s1': (ACCEPTED, 1, 'exact-v1'),
}
ID_CASES = ('reserved', 'unicode', 'spaces', 'plus', 'percent', 'slash', 'max64', 'numeric-looking')
DEPTHS = (1100, 5000, 10000, 20000)
SHAPES = ('array', 'object', 'alternating')

def command(case, browser=False):
    name = 'reconstruction_browser_protocol.py' if browser else 'reconstruction_probe.py'
    return f'../../.venv/bin/python -B evidence/independent-verifier/stage-2/{name} --release COMPLETE_NAMED_RELEASE.json --case {case} --out NEW_UNIQUE_OUTPUT --execute'

def prior_rows(path, stage=None):
    rows = list(csv.DictReader(path.open()))
    if stage is not None:
        rows = [r for r in rows if r['introduced_stage'] == str(stage)]
    result = []
    for original in rows:
        r = copy.deepcopy(original)
        r.update(historical_candidate=original['candidate_full_revision'], historical_verdict=original['verdict'],
                 historical_evidence_path=original['evidence_path'], historical_command=original['executable_command_or_interaction'],
                 historical_matrix=str(path.relative_to(ROOT.parent.parent.parent)), candidate_full_revision=PENDING,
                 applicable_stages='2,3,4', verdict='unverified', evidence_path='PENDING_FRESH_STAGE2_EVIDENCE',
                 inherited='yes' if r['introduced_stage'] == '1' else 'no', normative=r.get('normative') or 'True')
        # Retain the actual independently executed command as a prospective
        # template, replacing only the candidate identifier. Runtime-specific
        # names/paths must be rebound from the fresh release and recorded argv.
        r['executable_command_or_interaction'] = original['executable_command_or_interaction'].replace(original['candidate_full_revision'], 'FULL_NAMED_STAGE2_REVISION')
        r['future_command_binding'] = 'Historical argv template only. Fresh constrained Stage 2 runtime URLs/image, full revision and new unique output must be substituted and exact executed argv saved; never execute against the historical image as current coverage.'
        r['interpretation_note'] = r.get('interpretation_note', '') + ' Preparation only. Historical observations stay unchanged; all applicable paths require fresh named Stage 2 execution and row-level evidence binding.'
        if r['requirement_id'] == 'TK2-party-input':
            r['requirement_text'] = 'Search party size is an exact labelled editable numeric control under the adopted semantic-number interpretation.'
        result.append(r)
    return result

ROWS = prior_rows(ROOT.parent / 'stage-1/candidate-7/coverage.csv') + prior_rows(ROOT / 'candidate-1/coverage.csv', 2)

def add(case, source, key, text, *, owner='systems-engineer', browser=False, normative=True):
    ROWS.append(dict(requirement_id='TK2R-'+key, source_section=source, source_line='direct complete package / complete source snapshot',
        introduced_stage='2', applicable_stages='2,3,4', owner=owner, implementation_owner=owner,
        verification_owner='independent-verifier', candidate_full_revision=PENDING, requirement_text=text,
        verification_method='real browser / raw HTTP / independent oracle' if browser else 'independent raw HTTP / exact-value / member-interval oracle',
        executable_command_or_interaction=command(case, browser), evidence_path='PENDING_FRESH_STAGE2_EVIDENCE',
        verdict='unverified', case=case, inherited='no', normative=str(normative),
        interpretation_note='Specification-derived prospective case; not a presumed implementation failure. No service execution during preparation.',
        future_command_binding='Named release and actual source/resource proofs required before executing this prepared protocol.'))
    if case=='audit':
        ROWS[-1]['executable_command_or_interaction'] = (
            'git show --format=fuller FULL_NAMED_STAGE2_REVISION -- stage-2; git log --format=fuller --all -- stage-2 evidence/independent-verifier; inspect immutable provenance disclosure' if key=='index-provenance' else
            '../../.venv/bin/python -B evidence/independent-verifier/stage-2/api.py --base CURRENT_STAGE2_URL --peer INDEPENDENT_PEER_URL --candidate FULL_NAMED_STAGE2_REVISION --case transactions,concurrency --out NEW_UNIQUE_OUTPUT')

for origin, (revision, source_stage, profile) in ORIGINS.items():
    obligations = {
        'source': 'Genuine unmodified source issues a session and successful create/move receipts before export.',
        'import': 'Actual unchanged source export replaces a separately running current Stage 2 destination.',
        'token': 'The original source token remains authenticated after replacement.',
        'password': 'The genuine source account still logs in using its original password.',
        'reference': 'The original server-issued references remain usable by their owner.',
        'create-shape': 'Original create receipt retains the public representation actually issued by its source.',
        'moves-shape': 'Original move receipt retains the public representation actually issued by its source.',
        'numeric-profile': 'Original body comparison follows the saved receipt numeric profile independently of public representation origin.',
        'rounded-alias': 'Rounded decimal aliases replay only for genuine legacy receipts; exact-origin receipts distinguish the values.',
        'integer-distinct': 'A distinct integer-token request does not silently acquire legacy decimal rounding.',
        'bool-distinct': 'Boolean values remain different from numeric values during retry comparison.',
        'ignored-original': 'A formerly ignored source-stage field remains part of original complete body identity after import.',
        'new-rule': 'A new request/key obeys current Stage 2 seating-field validation.',
        'key-priority': 'A different used-key body conflicts before current field/resource validation.',
        'amend-create': 'Original create replay remains identical after a genuine current amendment.',
        'cancel-create': 'Original create replay remains identical after a genuine current cancellation.',
        'cancel-moves': 'Original batch replay remains identical after a genuine current cancellation.',
        'current-single': 'Current singleton lookup/list representation adds table_ids and retains table_id regardless of original receipt profile.',
        'mixed-new-exact': 'A newly issued exact Stage 2 receipt coexists with the imported historical receipt without rewriting it.',
        'mixed-forward': 'Actual mixed-origin export transfers unchanged into another independent current destination.',
        'mixed-replay': 'Both imported historical and new exact receipts keep their respective retry meaning in the next process.',
        'repeat-replacement': 'Repeating actual replacement restores identities/receipts without duplicates.',
        'failed-key': 'An unsuccessful current request leaves its key reusable after mixed-state transfer.',
        'destination-removed': 'Replacement removes the destination prior account, token and booking.',
        'reset-clears': 'Reset removes imported accounts/sessions/records/receipts.',
    }
    for suffix, text in obligations.items():
        add('origins', 'Stage1 §§3.4,5,7,10; Stage2 Existing clients / Response shapes; adopted numeric/receipt decisions',
            origin+'-'+suffix, f'{origin}, source {revision}, stage {source_stage}, numeric profile {profile}: {text}')
    if source_stage == 2:
        for suffix, text in {
            'pair-original': 'An original genuine pair receipt has table_ids and no table_id while retaining legacy comparison semantics.',
            'pair-current': 'Imported pair records occupy both members and current lookup retains declaration order.',
            'pair-cancel': 'Cancellation releases both genuine imported pair members.',
        }.items(): add('origins', 'Stage2 Combined tables; Stage1 §§7,10', origin+'-'+suffix, text)

deep_obligations = {
    'reset': 'Valid ignored deep JSON in reset is accepted without changing fixture meaning.',
    'signup': 'Valid ignored deep JSON in signup is accepted and issues a real token.',
    'create': 'A valid combined-table create with ignored deep JSON succeeds.',
    'create-alias': 'An equal exact numeric deep body replays the original successful create.',
    'create-different': 'A distinct exact deep fraction returns 409 before endpoint validation.',
    'create-type': 'A boolean/number deep body difference returns 409.',
    'moves': 'A genuine atomic pair/single swap with ignored deep JSON succeeds.',
    'moves-alias': 'An equal exact numeric deep batch replays its original input-order response.',
    'moves-noop': 'No-op/reversed-pair amendments preserve every current value.',
    'mutation': 'Original create and move receipts survive actual amendment/cancellation.',
    'export': 'Actual successful deep receipts are captured in raw HTTP export bytes, without client deep decoding.',
    'import': 'Those unchanged bytes replace an independent process and preserve tokens/references/current records.',
    'peer-replay': 'The imported original deep create and move bodies/keys replay unchanged.',
    'next-transfer': 'A genuine peer export transfers unchanged into a third independent destination.',
    'bad-import': 'Malformed deep import is 400 and leaves the complete destination snapshot unchanged.',
    'grammar-refusal': 'A malformed deep request is 400, leaves records unchanged and service healthy.',
    'failed-key': 'A correctly typed fractional invalid create fails 422 and its key can later succeed.',
    'capacity': 'Pair capacity remains exact while full deep request identity survives state transfer.',
}
for shape in SHAPES:
    for depth in DEPTHS:
        for suffix, text in deep_obligations.items():
            add('deep', 'Stage1 §§3.4,5,7,10,11; Stage2 combined members', f'deep-{shape}-{depth}-{suffix}', f'{shape}, {depth} balanced wrappers: {text}')

for label in ID_CASES:
    for suffix, text in {
        'admission': 'A legal opaque restaurant/table ID fixture is admitted.',
        'detail': 'Percent-encoded restaurant route resolves the original opaque ID.',
        'query': 'Availability query identity remains exact after URL encoding.',
        'single-body': 'Singleton body retains original opaque table ID.',
        'pair-body': 'Pair body retains both original opaque IDs in declaration order.',
        'grid': 'Required single/pair test IDs use the literal fixture IDs without aliasing.',
        'labels': 'Selection/confirmation/lookup show the real human labels.',
        'retry': 'Unchanged real browser request retains exact opaque IDs and retry key.',
        'lookup': 'Owner lookup and cancellation work with the original server reference.',
        'replacement': 'Actual export/import preserves opaque IDs and original receipts.',
    }.items():
        add('opaque', 'Stage1 §§3.4,7,8,10; Stage2 grid / combined UI', 'opaque-'+label+'-'+suffix, text,
            owner='interface-engineer' if suffix in ('grid','labels','retry','lookup') else 'systems-engineer',
            browser=suffix in ('grid','labels','retry','lookup'))

for spelling in ('integer', 'decimal-integral', 'exponent-integral'):
    for seating in ('single', 'pair'):
        for suffix, text in {
            'fixture': 'An exactly integral numeric base fixture obeys whole-value semantics.',
            'options': 'Actual response capacities preserve exact integer value and summed pair capacity.',
            'create': 'Actual reservation response party_size is a JSON number with the exact accepted integral value.',
            'visible-capacity': 'The browser displays actual integral decimal/exponent response capacity exactly.',
            'visible-party': 'The browser displays actual integral decimal/exponent response guest count exactly.',
            'query': 'The actual editable numeric control emits plain-digit query spelling.',
            'body': 'The actual form emits the exact integer JSON token, without string/rounding substitution.',
            'retry': 'Unchanged submit keeps body/key and original server-issued reference.',
            'malformed': 'Malformed JSON is rejected before any internal lossless number conversion; no false success is shown.',
        }.items():
            browser = suffix in ('visible-capacity','visible-party','query','body','retry','malformed')
            add('numeric', 'Stage1 §§3.4,5,7,8; Stage2 Product / numeric controls; adopted value interpretation',
                f'numeric-{spelling}-{seating}-{suffix}', text,
                owner='interface-engineer' if browser else 'systems-engineer', browser=browser)

for origin in ('legacy-s1', 'exact-s1'):
    for suffix, text in {
        'auth': 'The real source API issues the browser login token.',
        'retained': 'The real source issues a reference before the lost-response booking.',
        'commit': 'The real source commits the unchanged actual browser body/key before its response is dropped.',
        'uncertain': 'Only nonempty uncertainty is shown after the real committed response is lost.',
        'export': 'The actual raw source export replaces current Stage 2 between browser requests.',
        'no-reload': 'Routing switches without reloading, logging in again or editing the form.',
        'body': 'Unchanged retry uses identical raw request body.',
        'key': 'Unchanged retry uses identical original key.',
        'original': 'Retry displays the actual original receipt reference with replay status 200.',
        'shape': 'The original Stage 1 table_id-only receipt is handled without enriching it.',
        'lookup': 'The retained source reference works through real current lookup with the original token.',
        'one-record': 'Retry/resubmit creates no additional reservation.',
    }.items(): add('upgrade', 'Stage2 Existing clients / uncertain outcomes; adopted receipt decision', 'browser-'+origin+'-'+suffix,
        text, owner='interface-engineer', browser=True)

for suffix, text in {
    'native-value': 'Actual visible numeric fields retain complete decimal values through 4,301 digits.',
    'label': 'Actual search/booking fields have visible associated labels.',
    'role': 'Actual editable fields expose spinbutton semantics and numeric input mode.',
    'buttons': 'Visible increment/decrement controls step exact values with minimum one.',
    'keyboard': 'Arrow and Tab/Enter interaction uses the actual editable field and exact decimal stepping.',
    'mobile': '375px exact-value search/form/lookup remain usable without horizontal page scroll.',
    'focus': 'Keyboard focus remains apparent on editable field and stepping buttons.',
    'status': 'Exact DOM text and actual rendered status spellings are recorded separately; no earlier CSS-case assumption is relabelled.',
    'historic-current': 'Current historical end display follows exact restaurant IANA instant independently of browser timezone.',
    'historic-legacy': 'Genuine old offset-second strings display the correct restaurant-local end without rewriting original receipts.',
    'cutoff-order': 'Batch cutoff/nonoccupancy error order includes pairs, unchanged members and mixed valid/invalid items.',
    'snapshot-prefix': 'Concurrent reads and actual raw exports correspond to complete transaction prefixes with intact receipts.',
    'no-op-values': 'Reverse pair order alone and empty supported PATCH changes preserve every existing record value.',
    'serial-witness': 'Saved concurrent intervals/results/reads admit independently enumerated real-time-respecting serial histories.',
    'index-provenance': 'Immutable index incident and later source attribution corrections retain genuine authorship versus Git-identity distinction.',
}.items():
    browser = suffix not in ('cutoff-order','snapshot-prefix','no-op-values','serial-witness','index-provenance')
    add('controls' if browser else 'audit', 'Complete cumulative source / supplementary product brief / adopted decisions', suffix, text,
        owner='interface-engineer' if browser else ('systems-engineer / interface-engineer' if suffix=='index-provenance' else 'systems-engineer'), browser=browser)

def write_matrix(path):
    fields = list(dict.fromkeys(k for row in ROWS for k in row))
    with Path(path).open('w', newline='') as stream:
        writer=csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(ROWS)
