# Stage 1 transport state map

Scope: HTTP API only, package TK-20261004-S1-interface-engineer-A. This describes
observable states and ownership, not an acceptance verdict.

| Outcome | Observable contract | Owner / recovery |
|---|---|---|
| Starting / loading | Health is available only after shared Engine construction; clients wait for a response | Transport serves the ready Engine; no cosmetic healthy result |
| Normal | Engine status and JSON value are returned unchanged | Core owns transactions and endpoint rules |
| Empty | Empty list remains valid JSON; reset/import 204 has zero body bytes | Core determines lists; transport frames empty 204 |
| Malformed | Invalid UTF-8/JSON or explicit nonobject JSON returns 400 malformed_request before Engine | Correct the raw request; no state mutation |
| Validation | Parsed object passes untouched; wrong field types/value rules are evaluated by Engine | Core distinguishes 400 versus 422 and endpoint exceptions |
| Unauthenticated / unavailable | Engine's 401/403/404 or domain refusal is returned as JSON | Authenticate or correct visible resources |
| Conflict | Engine's occupancy or idempotency refusal remains 409 | Refresh availability or submit a legitimately new request |
| Retry / recovered | Lost connection never invokes Engine again; same caller/key/body retries recover the original receipt | Core returns original JSON with 200; no duplicate operation |
| Atomic replacement | Reset/import response becomes visible only after Engine's transaction returns | All following requests use the replacement state |
| Unexpected failure | Exception gives a JSON error and no success claim | Record and repair the backend fault; never relabel it accepted |

The transport does not introduce validation, idempotency caching, authentication,
occupancy decisions, browser controls or later-stage surfaces.
