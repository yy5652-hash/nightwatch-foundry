# Closure endpoint type errors

Candidate `261e4d9456a04a8b57ed46db71a09ac267ff15a9`, tree `501d27abab7226546da42edb1131ef8aa037deaf`.

The independent reading retains the inherited Stage1 section5 distinction: a JSON field of the wrong type is 400 `malformed_request`; missing required fields and correct-type invalid values/formats are 422 `validation_failed`. Stage4's interval rule specifies explicit offsets and strict ordering, and assigns 422 to an invalid interval. It does not explicitly assign a different error to nonstring JSON timestamp fields. Those fields therefore retain the general wrong-type rule. The four earlier adopted decisions do not change this distinction. This is the verifier's reconciliation of the cumulative published source, not a new coordinator decision.

The candidate's `explicit_instant` at core.py line219 sends every nonstring value through default `fail()`, producing 422. The current source-bound HTTP protocol separately executes null, true, false, number, array and object on both `from` and `to`. All twelve return 422 `validation_failed`, contrary to expected400 `malformed_request`. There are no client exceptions. Every corresponding export comparison remains byte-identical and each failed key succeeds when reused with the corrected body. Correct missing fields/bad string formats/nonpositive intervals return422. Wrong table_id type and malformed whole bodies correctly return400. Used-key differences correctly return409 before type validation. These successful neighboring observations are preserved separately and do not excuse the twelve type failures.

Smallest reproduction after resetting the protocol fixture and logging in as its real declared manager:

```http
POST /restaurants/r/replans
Authorization: Bearer <actual manager token>
Idempotency-Key: error-0
Content-Type: application/json; charset=utf-8

{"table_id":"a","from":null,"to":"2035-06-04T19:00:00+00:00"}
```

Expected400 `malformed_request`; observed422 `validation_failed`. The exact fixture, all request bytes/hash/status/timing and independently authored executable protocol are retained outside graded folders. No private token or raw export is saved. The executable command is in `current-http-01/commands.json`; its first client invokes `/verifier/stage-4/stage4_closure_errors.py` in the constrained source-bound client image.

Evidence: `current-http-01/closure-errors/requests.json`, `assertions.json`, `summary.json`, `executed-source.py`; source: `source-audit-02/source/core.py`. This finding rejects this candidate's promotion. A repaired candidate requires a new complete source-bound execution package and fresh evidence. No current failed output, published source or prior acceptance is rewritten.
