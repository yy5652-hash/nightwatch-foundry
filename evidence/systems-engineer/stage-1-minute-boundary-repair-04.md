# Stage 1 base-fixture minute-count repair 4

Complete scoped package: `TK-20261004-S1-systems-engineer-MINUTE-BOUNDARY-4`, all five parts and final marker received. Completeness acknowledgement `8b17b4f8-9971-45c3-97a3-fced8cf35340` preceded the investigation. The coordinator reported an independent accept for `b4a124e3671ec22a4df0780343f6389ff4b70d05`, but withheld freeze/promotion while this source-applicability question was resolved. This is a new scoped candidate repair, not an alteration of prior verdicts.

## Source applicability

Stage 1 §4 defines the base fixture's grid, absolute reservation duration and cancellation cutoff without an upper bound. Section 5 makes values exceeding a **stated** maximum invalid; no maximum is stated for these three fixture fields. Section 8 instead bounds actual bookable slots by that day's opening/closing instants. Section 9 defines duration as absolute time. Later-stage policy-field bounds do not impose an undocumented maximum on these Stage 1 base fixture fields.

The obsolete `timedelta(minutes=count)` construction in fixture validation added Python's arithmetic limit as an undocumented input restriction. The application already uses integer microsecond arithmetic for duration, cutoff and closing fit, and enumerates only the bounded local opening window for grid candidates. Removing this unused representability check therefore does not create arbitrary unbounded-duration bookings or unrepresentable endpoint timestamps. Positive grid/duration and nonnegative cutoff integer validation is retained, including existing type/error distinctions.

## Preserved reproduction and repair

Before editing core, an offline container built from the unchanged timestamp candidate rejected each of `slot_minutes`, `reservation_duration_minutes` and `cancellation_cutoff_minutes` set to `10^18`: reset returned 422 `validation_failed` rather than 204. The fixture, command and assertions are inspectable in `stage-1-builder-probes.py`, scenario `StageOne.test_unbounded_base_fixture_minute_counts`. Original failure log: `stage-1-minute-reproduction-04.log`, one scenario with three failing subcases, 0.106 s. The unchanged container's core hash matches `b4a124e3671ec22a4df0780343f6389ff4b70d05`; `stage-1-minute-before-runtime-04.json` records that equality, network none, 2 CPU and 2 GiB.

Exact reproduction command:

```sh
docker run -d --name systems-engineer-s1-minute-before-04 --network none --cpus 2 --memory 2g -e PORT=18109 systems-engineer-tablekeeper-s1:timestamp-03
docker exec -i systems-engineer-s1-minute-before-04 python - --url http://127.0.0.1:18109 --destination-url http://127.0.0.1:18109 StageOne.test_unbounded_base_fixture_minute_counts < evidence/systems-engineer/stage-1-builder-probes.py
```

Production diff deletes only the five-line obsolete check in `stage-1/core.py`. The new builder scenario verifies that a huge grid yields only the opening candidate and rejects an off-grid booking; a huge duration yields no slots and refuses an unfit create; a huge cutoff refuses amendment/cancellation of an ordinary future booking. Failed writes leave export snapshots unchanged, successful create receipts replay unchanged, and each resulting state exports/imports with its exact huge configuration.

Command `../../.venv/bin/python -B evidence/systems-engineer/stage-1-builder-probes.py` passed all 15 scenarios without skips in 1.972 s. Evidence: `stage-1-minute-regression-04.log`. Existing calendar endpoints, historic RFC3339 interpretation, genuine earlier-service receipt import, current-service import, DST, concurrency, swaps and rollback diagnostics remain included. Constrained fresh-image HTTP execution follows in an append-only entry.

Only Systems-owned core/evidence files changed. Engine.request and the export schema remain unchanged. Stage 2 is not implemented. The coordinator's historic timestamp interpretation exception remains applicable: exact IANA instants/original wall fields are preserved using adjusted minute-offset wire clocks; successful imported legacy receipt strings are retained. Independent exact-revision re-execution is required before freeze. Harness Codex; configured gpt-6.1-sol; actual override, effort, usage and spend unknown.

## Committed implementation and constrained HTTP result

Implementation revision: `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`. Build command `docker build -t systems-engineer-tablekeeper-s1:minute-04 stage-1` passed; `stage-1-minute-build-04.log` preserves output. Build cache was available; this is not an uncached-build claim.

The full 15-scenario suite passed without skips over HTTP in 2.581 s (`stage-1-minute-http-04.log`). Two repaired service processes and one genuine prior serializer-free service ran independently, each at 2 CPU/2 GiB with no mounts on an internal Docker network. Ports: current source 18110, current destination 18111, legacy source 18112. All image core hashes match their named committed implementations, including legacy `49287b4a5a1481f995c470ccae31776f03d4b863`. The huge configurations were transferred between independent repaired processes; earlier receipt compatibility was checked against the genuine prior service. Export credentials/tokens remained in memory.

Exact suite command:

```sh
docker exec -i systems-engineer-s1-minute-source-04 python - --url http://127.0.0.1:18110 --destination-url http://systems-engineer-s1-minute-destination-04:18111 --legacy-url http://systems-engineer-s1-minute-legacy-04:18112 < evidence/systems-engineer/stage-1-builder-probes.py
```

`stage-1-minute-runtime-04.json` records all exact setup/health/hash/probe/cleanup argv, revision/hash equality and resource/network observations. All three Systems-owned probe containers and their internal network were removed with zero cleanup return codes; the unchanged pre-repair reproduction container was also removed. Images are retained. Prior failed observations remain unchanged. This new full candidate requires independent review before the coordinator freezes Stage 1; builder diagnostics do not promote it or establish hidden-suite coverage.
