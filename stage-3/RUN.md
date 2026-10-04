# Tablekeeper Stage 3

From this folder, build and start the complete HTTP service:

```sh
docker build -t interface-engineer-tablekeeper-stage-3 .
docker run --rm --name interface-engineer-tablekeeper-stage-3 \
  --cpus=2 --memory=2g -e PORT=8080 -p 18200:8080 \
  interface-engineer-tablekeeper-stage-3
```

In another terminal:

```sh
curl --fail http://localhost:18200/health
```

The ready response is `{"status":"ok"}`. The service listens on `0.0.0.0`
and uses `PORT`, defaulting to `8080`. To change it, change both the container
environment and mapping, for example `-e PORT=9090 -p 18200:9090`.

Python, the application and IANA timezone rules are packaged in this single
image. No host Python packages, mounted data, separate database or runtime
network access are required. Startup has no runtime downloads. Requests are
served concurrently against one shared Engine; its application transactions
coordinate occupancy, retries, reset and import. State is in memory and lasts
only for this container process.

Open `http://localhost:18200/`. The browser routes `/`, `/signup`, `/login` and
`/lookup` load directly. Diners can browse before signing in, choose a single
table or an approved pair, book, and look up or cancel their own reservations.
All assets are packaged locally. Typography uses the browser's system fonts.
The service begins with an empty catalogue; supply fixtures through reset.

Guest fields are exact-decimal numeric controls with visible labels, numeric
keyboard input and spinbutton arrow-key stepping. They retain positive integer
digit strings beyond native browser floating-point limits. Search queries and
booking JSON numbers use exact plain decimal digits; no party-size maximum is
introduced. Large integer API values remain exact for display and combined seat
counts use integer arithmetic. Restaurant capacity rules remain server-authoritative.

Stage 3 retains the JSON API. Browse `/restaurants`, restaurant details and
`/availability` without authentication. Sign up or log in through `/auth/signup`
or `/auth/login`, then send `Authorization: Bearer <token>` for diner routes.
Creating a reservation and moving several reservations require a caller-chosen
`Idempotency-Key`. Reuse the same key and exact parsed body after a lost response
to recover the original receipt; do not assume a network failure means refusal.
Declared pairs use `combinable`, `available_options` and `table_ids`. Single-table
requests continue to accept the Stage 1 `table_id` shape.

After a lost booking response, keep the unchanged form and choose **Retry this
booking**. The browser retains its original body and key. A changed booking field
creates a separate request. A table conflict retains the form and refreshes
availability. Submitting the unchanged form after success checks the same
confirmation without creating another booking. There is no background polling.

`POST /_test/reset` replaces all state from a JSON fixture and returns an empty
204 response. `GET /_test/export` and `POST /_test/import` transfer a private,
complete snapshot between independent processes. These unauthenticated test
controls are enabled as required. Exported state contains password hashes and
session tokens; keep exports as private test data rather than demo assets.
Stage 3 also accepts genuine exports from the team's Stage 1 and Stage 2 services.
Keep the browser page open during an import between requests. Its session token,
pending form and retry identity remain available without a reload. The browser
accepts original Stage 1 receipts with `table_id` and without `table_ids`.
Session identity is held in this tab's session storage where available; sign out
clears it and the private view. Service state is ephemeral across restart.

API responses use `application/json; charset=utf-8`; screen routes return HTML.
Explicit JSON null, arrays,
scalar bodies, malformed UTF-8 and invalid JSON are 400 `malformed_request` before
application authentication or idempotency. Empty bodies are passed to the Engine
as absent bodies. Unknown fields and query parameters reach the Engine unchanged.
Send JSON bodies with `Content-Length` framing (ordinary curl and HTTP clients do
this automatically).

Historical subminute IANA offsets inherit the recorded factory interpretation:
new timestamps use the nearest representable RFC3339 minute offset with adjusted
clock fields, preserving the exact instant and original `starts_at_local`. Saved
receipts retain their original strings. The literal-offset limitation is recorded
outside the service folder in the coordinator's timestamp decision.

Stop the foreground container with Ctrl-C. The `--rm` flag removes only that
container after it exits. Independent acceptance and official isolated harness
results are tracked outside this folder under `evidence/` and the run's check
output directories.

The HTTP adapter uses the packaged shared exact JSON codec for raw UTF-8 decode
and byte serialization before response headers. New writes use exact numeric
value semantics, including integral decimal/exponent forms; strict query integers
still require plain digits. Original successful receipts retain their source
representation and receipt-scoped numeric meaning across upgrades. The browser
preserves unsafe whole numeric response values spelled with decimal points or
exponents for exact displayed guest counts and summed capacities.

The original booking confirmation keeps the successful response's original
reference, revision and terms. The lookup screen loads the current reservation,
owner-only decision and ordered history from the service. Open each accepted-term
summary to see duration, cancellation cutoff, start grid, opening hours and table
capacities. History shows the terms at each event; it does not attach newer
policies to earlier events. Availability uses real `explain=true` responses and
the selected policy's available-option capacities. Restaurant detail remains the
original fixture configuration and does not override accepted booking terms.

From a confirmed, editable booking on `/lookup`, choose 2–12 total recurring visits
and 1–4 weeks between visits. The existing reservation is occurrence zero. The
service checks every later occurrence before confirming the agreement. A lost
response shows uncertainty; keep the form unchanged and retry with the retained
body/key. The original successful recurring response remains separate from the
current occurrence list, which is loaded with `GET /series/{series_id}`. Individual
changes show permanent exceptions; cancellations remain in the list and do not
cancel siblings. Load an agreement by its actual service-issued reference, or
open a listed occurrence to retrieve its current booking/history. There is no
background polling or later-stage bulk-amend/planner control.

Only fixture `manager_user_ids` confer policy-publication permission. The product
does not invent signup roles, and manager status never grants another diner's
private lookup, decision, history or series. Signing out clears the private view
and in-memory agreement references. Prior-version original receipts need not
contain Stage 3 fields; their exact response/body/key remain untouched. Current
details load separately after migration without replacing the original receipt.
