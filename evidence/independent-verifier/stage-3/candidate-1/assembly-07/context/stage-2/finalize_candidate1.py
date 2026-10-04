"""Publish append-only factual verdicts; prior observations and acceptance stay intact."""
import csv,datetime as dt,hashlib,json,sys
from pathlib import Path
from requirements import stage1
here=Path(__file__).resolve().parent;repo=here.parents[2];workspace=repo.parents[1]
target=here/'candidate-1';candidate='4b92041057beb669d2e6c528e8268f4d0d1e6421';frozen='2a4b0408a3453bc87d86bca3d0ec571f479e03ca'
summary=json.loads((target/'summary.json').read_text());assert summary['rows']==1265 and summary['verified']==1226 and summary['failed']==17 and summary['unverified']==22
summary['highest_independently_accepted_stage']=0
summary['official_wall_seconds']=json.loads((target/'official-evidence/independent-verifier-s2-4b92041-official-01.execution.json').read_text())['seconds']
summary['official_stage3_overshoot']=dict(json.loads((target/'official-evidence/stage-3.counts.json').read_text()),not_executed=6)
summary['observed_runs']={str(p.relative_to(target).parent):json.loads(p.read_text()) for p in target.rglob('summary.json') if p!=target/'summary.json'}
summary['large_minutes']={k:v for k,v in json.loads((target/'api-01/large-minutes.log').read_text()).items() if k not in ['operations','results']}
(target/'summary.json').write_text(json.dumps(summary,indent=2))
issues=[
 dict(classification='verifier DNS-label error; no service startup failure inferred',evidence=['boundaries-02/commands.json','legacy-01/commands.json'],observed='Verifier-generated container hostnames exceeded the DNS label length; health client could not resolve them.',repair='Shorten own names, then repeat from fresh matching-image processes in boundaries-03, historical-02 and legacy-02 onward.'),
 dict(classification='verifier current-view assumption; original raw failures retained',evidence=['api-01/inherited/assertions.json','legacy-02/probes/assertions.json'],observed='One amendment and three legacy lookup checks compared a newly derived Stage 2 table_ids view as though it must remain the old singleton value/shape.',repair='Separate source-correct amendment observations in amend-02 and genuine old-service current-view probes in legacy-03/04; historical successful POST receipts still compare exact original JSON.'),
 dict(classification='incomplete/scheduled verifier migration protocol; no promotion evidence from these runs',evidence=['upgrade-browser-01','upgrade-browser-02'],observed='First protocol imported login state before search; next corrected protocol overlapped own legacy transfer driver.',repair='Route all compatible pre-upgrade API traffic transparently to the real Stage 1 process and repeat sequentially in upgrade-browser-03; final legacy-04 also runs sequentially.'),
 dict(classification='pending status text interpretation, not an asserted production defect',evidence=['browser-01/browser/assertions.json','upgrade-browser-03/upgrade-browser/assertions.json','boundaries-03/probes/assertions.json'],observed='Five general-browser checks and one upgrade check used innerText and saw Confirmed/Cancelled. DOM textContent is exactly confirmed/cancelled; CSS text-transform is capitalize.',repair='Keep four corresponding normative rows unverified pending the coordinator interpretation. No failure is converted in place.'),
 dict(classification='verifier report printer error after evidence/cleanup completed',evidence=['cleanup.json','assessment-printer-error.md'],observed="TypeError: dict() got multiple values for keyword argument 'failed'",repair='Rename the printed list field to failed_ids; rerun only evidence aggregation. All four primary cleanup return codes were already zero; no service check was repeated or altered.')]
(target/'runner-issues.json').write_text(json.dumps(issues,indent=2))
(target/'assessment-printer-error.md').write_text("# Preserved verifier aggregation error\n\nThe first `assess.py --cleanup` invocation completed source capture, the four zero-code cleanup operations and coverage/summary writes, then its final stdout printer raised `TypeError: dict() got multiple values for keyword argument 'failed'`. This exact error was observed in the tool result. The print field was renamed `failed_ids`; a new aggregation invocation completed. This note records a verifier error, not a retained service-failure log or a service defect.\n")
report=f'''# Stage 2 candidate 1: reject

Tested full candidate: `{candidate}`. **Reject**. Highest independently accepted consecutive stage is **0** after the new inherited Stage 1 decimal-limit supplemental rejection below. No Stage 2 freeze or Stage 3 extension follows. The verifier modified no production files; later builder revisions have not been accepted through this report.

The full package `TK-20261004-S2-independent-verifier-CANDIDATE-1`, all eight parts and END marker, was acknowledged in room message `946398a8-3d58-47ea-b7d1-cb2984566774` before execution. The final independent matrix has **1,265 atomic rows: 1,226 verified, 17 failed, 22 unverified** (806 inherited, 459 Stage 2). Counts denote this specification decomposition, not shipped tests or an unseen judging score. Every row names source section/stage/owner/full candidate, method, observed executable command or browser interaction, artifact and verdict. The 18 downstream 401-digit browser paths could not execute after the input was cleared; four status/lookup rows remain unverified pending text-versus-CSS-case interpretation. A rejection is required independently of those pending rows.

| Smallest source-derived interaction | Expected | Observed on this exact candidate |
|---|---|---|
| Stage 1 §§4/5: valid UTC fixture, change only one of grid/duration/cutoff/capacity to a positive 4,301-digit JSON integer (`10^4300+1`), body about 5 KB | 204; no published language digit ceiling | 400 `malformed_request`, `Body must be a JSON object`, for all four fields |
| Stage 1 §§5/8: normal capacity-2 fixture, availability `party_size=10^4300+1` as plain digits | 200; eight fitting starts with empty single-table availability | 422 `validation_failed` |
| Stage 2 product/party rules: fitting singleton and declared pair, party/capacity `9007199254740993` | Faithful capacity and stored guest count where displayed | UI shows `9007199254740992` for capacity and lookup Guests, although emitted query/body and server record remain exact |
| Same, `1000000000000000000001` | Faithful numeric value | Capacity and lookup Guests show `1e+21`, losing the final unit; exponent display alone is not the defect |
| Same, fitting singleton/pair with `10^400+1`, 401 plain digits | Preserve valid numeric input and allow the requested search/prefill/booking path | Native number control clears its value before application code; downstream paths remain unverified |
| Recorded historical timestamp decision plus truthful restaurant-local UI: Berlin/Brussels `0001-01-01T18:00`, 90 minutes, lookup | Local end 19:30 in the displayed restaurant zone | Ends at 19:29: the UI reads the adjusted minute-offset wire clock instead of restaurant-local end. The API instant is correct |

All three numeric/display families were repeated in new matching-image service processes. `boundaries-03/probes` preserves 34 assertions, 10 failures, 24 direct HTTP operations and 94 browser requests; original `boundaries-01` remains unchanged. `decimal-02/probes` preserves 14 requests, 12 assertions, 10 failures across fresh current and frozen-Stage-1 processes, with normal controls passing; the first run remains in `decimal-01`. `historical-02/probes` preserves 6 assertions, 2 failures, 12 HTTP operations and 33 browser requests, repeating `historical-01`. Exact fixtures, raw valid decimal JSON/query strings, request/response observations, expected/observed values, source hashes, real screenshots, timings and argv are inspectable. This is actual behavior, not inference from production source.

The decimal-count source applicability follows the same Stage 1 §§4/5 interpretation as the prior `10^18` repair: these base fields have no stated upper bound; §5 distinguishes type/format errors and values beyond a stated maximum. Later policy bounds are separate. A valid modest JSON integer or plain-decimal query cannot be treated as malformed solely because Python's conversion limit is 4,300 digits. For browser values, positive integer party size and fitting capacity likewise have no stated 2^53 or IEEE-float upper bound. A native HTML control limit is an observed cause, not a published application range. The source words “Number”/“Number input” do not resolve the proposed replacement control here; its implementation and accessible semantics require a later named review.

The frozen Stage 1 service bytes are identical to `{frozen}` and also exhibit all five decimal-limit failures. The separate append-only report `../../stage-1/candidate-4-supplemental-decimal/VERDICT.md` revokes the earlier acceptance at `fcc0974e8cc44f7f3d57891d6b1759b499ede176`. Original acceptance, all prior rejection/repair files, freeze manifest and history remain unchanged. Earlier 801 passing rows against that exact source are historical valid observations; the five new failed rows prevent promotion. No fresh fixture or hand-edited export was substituted for genuine legacy state.

Official command, from `{workspace}/kickoff`:

```sh
{workspace}/.venv/bin/python -m harness run --track tablekeeper \\
  --repo {workspace}/band-work/independent-verifier-s2-4b92041057be-20261004t020622 \\
  --stage 2 --mode isolated \\
  --out {workspace}/band-work/final-checks/independent-verifier-s2-4b92041-official-01
```

Unchanged isolated observed counts: Stage 1 **120 collected/120 passed**; Stage 2 **25 collected/25 passed** (8 API, 17 UI); zero failures/errors/skipped/deselected/xfailed in both. The unchanged harness runs both earlier and current suites against the Stage 2 container; the separate Stage 1 build is only its upgrade source. This establishes current-implementation regression evidence, not a repeated test of only the frozen folder. Measured total command time **33.579287041 s**. Stage 3 overshoot **7 collected, 0 passed, 1 failed, 6 not executed**, zero errors/skipped/deselected/xfailed; `-x` stopped the unchanged probe, report overshoot is null and claimed stage is 2. No shipped tests, runtime or selection were edited. Official green checks cannot override the independent source failures.

| Independent run, retained separately | HTTP operations | Assertions | Raw failures | Probe seconds |
|---|---:|---:|---:|---:|
| Complete inherited suite and offset/occupancy oracle | 1,485 | 1,497 | 1 verifier current-view assumption | 8.110426087 |
| Pair/single API, member/interval oracle, atomic moves and staged concurrency | 949 | 2,459 | 0 | 7.002601462 |
| Original minimal rejection regression | 4 | 9 | 0 | 0.013867875 |
| Calendar endpoint minimal regression | 8 | 12 | 0 | 0.105251666 |
| Staged 50 identical singleton requests | 55 | 11 | 0 | 0.120898709 |
| `10^18` minute grid/fit/cutoff/import/retry | 39 | 26 | 0 | 0.177557334 |
| Genuine frozen Stage 1 accounts/create/batch transfer | 31 | 39 | 0 | 0.158449167 |
| Source-correct retained-field amendment | 5 | 2 | 0 | 0.116967709 |
| Genuine pre-serializer source/current-view/mixed-state transfer, final sequential run | 26 | 24 | 0 | 0.210533625 |
| General browser flows and request identity | 94 direct HTTP, 361 browser requests | 329 | 5 CSS-case assumption checks; unresolved | 22.747328343 |
| Genuine old-API browser upgrade, final sequential protocol | see request trace | 8 | 1 CSS-case assumption check; unresolved | 1.190313167 |
| Real visual/keyboard/contrast states at 375/1280 px | 14 direct HTTP, 102 browser requests | 48 | 0 | 7.121809295 |
| Genuine old ignored-field create/batch receipts | 18 | 14 | 0 | 0.125045959 |

Raw assertion failures are disclosed separately from normative failures. The first amendment comparison included the newly derived seating array; three initial legacy lookup comparisons expected the old shape without current `table_ids`. Separate source-correct observations preserve all original identity/time/owner/receipt values and validate the new current view. Old traces were not edited. Five general-browser and one upgrade checks used rendered `innerText`; actual lowercase DOM `textContent` is retained with CSS capitalization. These are not asserted implementation failures. Four corresponding rows remain unverified until interpretation is resolved. DNS-name mistakes and an aggregation stdout printer error are classified in `runner-issues.json`; they are verifier errors, not service startup defects.

The independent Stage 1 occupancy oracle uses seed `20261004`; the separate Stage 2 member/interval oracle uses `20261005`, each with 160 saved operations. No production helper is used as an oracle. Staged Content-Length workloads hold each final body byte until all 50 are ready, then release together. Singleton identical and pair identical each give one 201 and 49 original 200 receipts; 50 mixed pair/single competitors sharing a member give one 201 and 49 `table_unavailable` refusals. Saved client intervals overlap at 50; no artificial service delay was introduced. The pair amendment/create/cancel/read and batch/read workloads record an independently valid serial ordering, including every observed export snapshot. Ordinary inherited calls took at most 0.057351 s; saved timeouts remain 5 s (10 s test controls).

Actual browser flows exercise direct routes/signup/login/logout, public browse, signed-out refusal, private lookup, cutoff refusal, singleton/combination labels, success and repeated submissions. Search A is held until B's results/form finish, then released; labels/form remain B. Rival commits after form opening cause real 409, availability refresh, preserved inputs and no false success. Both precommit and real commit-then-drop faults show only uncertainty; unchanged key/body retry recovers the original receipt/reference, and a real edit changes identity. The server remains authoritative. Genuine old-service migration forwards the unmodified packaged Stage 2 assets' compatible API traffic to independently built Stage 1, which really issues the login token and lost-response booking. Its unchanged in-memory export replaces Stage 2 between requests; routing switches without reload/login/form edit/key regeneration. The unchanged retry recovers the real table_id-only original receipt. The current lookup response legitimately gains `table_ids`; its pending row concerns CSS-case judgment only.

Real pre-serializer service source is this run's earlier `49287b4a5a1481f995c470ccae31776f03d4b863`, clean-cloned and separately built. Its offset-second strings and original create/batch receipts survive current import and mixed-state transfer to another process without rewriting. Frozen Stage 1 genuine receipts with formerly ignored `table_ids` values also import/replay exactly; new keys obey Stage 2 rules and altered used bodies conflict first. Exports/tokens/password hashes stayed in memory; saved credential fields contain fingerprints.

Independent screenshots and measured page widths show clear ordinary flows at 375 and 1280 CSS px without horizontal page scroll. Warm cream surfaces, green actions, clay/amber feedback, human table labels and consistent navigation form a coherent product. Focus has a visible 3px brown outline; an actual mobile Enter/Tab booking, lost response and unchanged Enter retry completed. Captured text contrast was independently computed with transparent ancestor backgrounds: normal >=4.5:1, large >=3:1, disabled text excluded. This is a scoped product review, not complete WCAG certification. General visual approval cannot conceal the exact value/time failures listed above.

Fresh clean detached clones followed RUN.md. Current default/override health took **0.292209417/0.272538083 s** from separate internal-network clients; frozen source health took **0.407309042 s**. Every service had 2 CPU, 2 GiB, no mounts and an internal offline network; actual committed/image Python and packaged HTML/CSS/JS hashes match. Source audit preserves authored history, complete source-input declarations and complete accepted-copy evidence. No escaping symlink, submodule, nested service repository or uncommitted runtime dependency was found. Build cache was available; no uncached-build claim. All verifier-owned service containers and network were removed with zero cleanup codes; own images and clean clones remain inspectable. No other seat's process was touched.

**Inherited interpretation risk remains explicit.** New historical wire timestamps use the nearest representable minute-aligned fixed offset plus adjusted clock, exact IANA instant and unchanged original wall field; lower-offset ties are deterministic. Literal historical subminute wire-offset compliance cannot be claimed simultaneously with RFC3339 minute-offset grammar. Genuine old successful strings/receipts, including offset seconds and old response schemas, remain immutable. The browser's wrong restaurant-local end display is separate from that correct instant serialization. Original-response precedence is supplied in the complete direct handoff; its later durable coordinator file is not falsely attributed to this named candidate.

Owning-builder repair and a complete new named handoff/full independent rerun are required before acceptance. Preserve every failure, correct both inherited/current decimal input limits, preserve exact displayed integer values and valid numeric input, and make any shown local end truthful. No builder summary or later source change has been relabelled as this candidate's evidence. Harness Codex; configured model gpt-6.1-sol; actual runtime override, effort, usage, estimated cost and billed spend **unknown**. Per-run timings are measured; whole factory elapsed remains coordinator-owned. Room export, public release and competition submission remain operator-controlled.
'''
(target/'VERDICT.md').write_text(report)
supp=here.parent/'stage-1/candidate-4-supplemental-decimal';supp.mkdir(exist_ok=True)
prior=list(csv.DictReader((here.parent/'stage-1/candidate-4/coverage.csv').open()))
assert len(prior)==801 and all(r['verdict']=='verified' for r in prior)
new=[dict(r) for r in stage1.ROWS if r['requirement_id'].startswith('TK1-decimal-limit-')]
for row in new:
    row.update(candidate_full_revision=frozen,verdict='failed',verification_method='black-box HTTP valid raw decimal JSON/plain query on genuine frozen source and fresh matching-image repeat',
      evidence_path=str(target/'decimal-01/decimal-limit/assertions.json')+' ; '+str(target/'decimal-02/probes/assertions.json')+' ; '+str(target/'decimal-02/source-proof.json'),
      executable_command_or_interaction='Exact Docker probe argv in '+str(target/'decimal-02/commands.json')+'; raw 4,301-digit fixture/query operations in '+str(target/'decimal-02/probes/operations.json'))
with (supp/'coverage.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(prior[0]));writer.writeheader();writer.writerows(prior+new)
supp_summary=dict(candidate=frozen,verdict='reject',revokes_evidence='fcc0974e8cc44f7f3d57891d6b1759b499ede176',rows=806,verified=801,failed=5,unverified=0,
  note='The earlier 801 verified rows are unchanged historical observations against this same exact source, not a claimed new full run.',highest_independently_accepted_stage=0,
  original=json.loads((target/'decimal-01/decimal-limit/summary.json').read_text()),repeat=json.loads((target/'decimal-02/probes/summary.json').read_text()))
(supp/'summary.json').write_text(json.dumps(supp_summary,indent=2))
(supp/'VERDICT.md').write_text(f'''# Stage 1 candidate 4 supplemental verdict: reject

Stage 1 source revision `{frozen}`: **reject**. This new independent boundary review revokes acceptance at evidence revision `fcc0974e8cc44f7f3d57891d6b1759b499ede176`; its original report, all prior failed observations and the coordinator's freeze manifest remain unchanged. Highest independently accepted consecutive stage is now **0**, pending a repaired candidate and full review.

Stage 1 §§4/5 impose no numeric maximum on positive grid/duration/capacity or nonnegative cutoff. Section 5 forbids values beyond a **stated** maximum and requires plain decimal query integers; no Python 4,300-digit limit is stated. This is the same source applicability as the prior `10^18` base minute-count repair, applied to a valid modest request about 5 KB rather than a resource exhaustion workload. Later policy limits are separate. A 4,301-digit positive JSON integer (`10^4300+1`) is syntactically valid and of the correct JSON number type. The independently authored client checks JSON grammar using decimal strings; it does not pass a string in the wire body or use floating conversion.

| Smallest source-derived interaction in a normal UTC fixture | Expected | Observed |
|---|---|---|
| Change only `slot_minutes` to `10^4300+1` | reset 204 | 400 `malformed_request`, `Body must be a JSON object` |
| Change only `reservation_duration_minutes` to the same positive integer | reset 204 | same 400 |
| Change only `cancellation_cutoff_minutes` to the same positive integer | reset 204 | same 400 |
| Change only table `capacity` to the same positive integer | reset 204 | same 400 |
| Normal capacity-2 fixture, `GET /availability?restaurant_id=r&date=2035-06-04&party_size=<4301 plain digits>` | 200; eight fitting starts, each with empty `available_table_ids` | 422 `validation_failed` |

The five failures first occurred against the genuine frozen Stage 1 service during current-stage review, and repeated in a fresh independently running matching-image Stage 1 process. Stage 2 exhibits the same five inherited failures. The first combined run has 12 HTTP requests, 10 assertions and 10 failures in 0.006695750 s. The repeat has 14 requests, 12 assertions and 10 failures in 0.007320791 s; ordinary-value resets pass before both source families and the later controls also return 204. These totals cover both stages: **five distinct failed requirements per stage**, not ten distinct Stage 1 rows.

Exact independently authored client: `{here}/decimal_limit.py`. Raw fixtures/query strings, responses, assertions and timings: `{target}/decimal-01/decimal-limit/` and `{target}/decimal-02/probes/`. The fresh-repeat driver is `{here}/decimal_repeat.py`; exact executed argv and zero cleanup codes are in `{target}/decimal-02/commands.json`. Source/resource proof is `{target}/decimal-02/source-proof.json`. No exported credentials occur in these decimal fixtures; users are empty.

The Stage 1 folder built from a clean detached current-candidate clone is byte-identical in all five files to `{frozen}`, not a later repair. Its independently built image and both running source processes match frozen core/server hashes; the fresh repeat has 2 CPU/2 GiB, no mounts and an internal offline network. The clone's full HEAD is honestly current candidate `4b92041057beb669d2e6c528e8268f4d0d1e6421`, whose unchanged Stage 1 subtree is verified against the frozen full source; this is not a claim that the clone HEAD itself is the earlier commit. Original accepted-build/clone evidence remains in `../candidate-4/`. All own processes/network were removed; no other seat's process was touched. Build cache was available.

The supplemental matrix has **806 rows: 801 historical verified, 5 newly failed, 0 unverified**. The earlier independently observed official 120/120 against this unchanged source is preserved and was not repeated merely to rediscover an already rejecting source failure. The current Stage 2 official run also passes all 120 inherited tests, which do not cover these five boundaries. Neither official result establishes renewed acceptance.

Owning-builder repair must remove unpublished language conversion ceilings while preserving exact JSON numbers, decimal query grammar, correct error codes, bounded grid/fit/cutoff behavior and all original receipts/state. A new complete candidate/full independent rerun is required; no Stage 1 freeze or later extension follows this verdict. Historical minute-offset/immutable original-string interpretation remains as recorded and independent of these failures. No production file was modified by the verifier. Harness Codex; configured gpt-6.1-sol; actual model override/effort/usage/estimated/billed spend unknown. Per-run durations are observed; whole factory elapsed is coordinator-owned. Genuine room export/publication/submission remain operator-controlled.
''')
for folder in [target,supp]:
    manifest=[dict(path=str(p.relative_to(folder)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json']
    (folder/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2))
ledger=here.parent/'ledger.jsonl'
if '--no-ledger' not in sys.argv:
    with ledger.open('a') as stream:
        for phase,data in [('stage-1-candidate-4-supplemental-decimal-reject',supp_summary),('stage-2-candidate-1-final-reject',summary)]:
            stream.write(json.dumps(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase=phase,**data))+'\n')
print(json.dumps(dict(stage2=dict(rows=1265,verified=1226,failed=17,unverified=22),stage1=dict(rows=806,verified=801,failed=5,unverified=0),highest_accepted=0)))
