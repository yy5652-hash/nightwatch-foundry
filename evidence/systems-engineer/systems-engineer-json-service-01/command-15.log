# Tablekeeper Stage 1

From this folder, build and start the complete HTTP service:

```sh
docker build -t interface-engineer-tablekeeper-stage-1 .
docker run --rm --name interface-engineer-tablekeeper-stage-1 \
  --cpus=2 --memory=2g -e PORT=8080 -p 18200:8080 \
  interface-engineer-tablekeeper-stage-1
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

Stage 1 provides the JSON API. Browse `/restaurants`, restaurant details and
`/availability` without authentication. Sign up or log in through `/auth/signup`
or `/auth/login`, then send `Authorization: Bearer <token>` for diner routes.
Creating a reservation and moving several reservations require a caller-chosen
`Idempotency-Key`. Reuse the same key and exact parsed body after a lost response
to recover the original receipt; do not assume a network failure means refusal.

`POST /_test/reset` replaces all state from a JSON fixture and returns an empty
204 response. `GET /_test/export` and `POST /_test/import` transfer a private,
complete snapshot between independent processes. These unauthenticated test
controls are enabled as required. Exported state contains password hashes and
session tokens; keep exports as private test data rather than demo assets.

JSON responses use `application/json; charset=utf-8`. Explicit JSON null, arrays,
scalar bodies, malformed UTF-8 and invalid JSON are 400 `malformed_request` before
application authentication or idempotency. Empty bodies are passed to the Engine
as absent bodies. Unknown fields and query parameters reach the Engine unchanged.
Send JSON bodies with `Content-Length` framing (ordinary curl and HTTP clients do
this automatically).

Stop the foreground container with Ctrl-C. The `--rm` flag removes only that
container after it exits. Independent acceptance and official isolated harness
results are tracked outside this folder under `evidence/` and the run's check
output directories.
