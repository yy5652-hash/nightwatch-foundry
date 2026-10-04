"""Stage 50 real HTTP requests before releasing their final body byte."""
import argparse
import concurrent.futures
import http.client
import json
import threading
import time
import urllib.parse
from probe import Probe, safe

parser = argparse.ArgumentParser()
parser.add_argument("--base", required=True)
parser.add_argument("--candidate", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
args.peer = None
args.case = "staged-50-http"
p = Probe(args)
p.setup()
p.expect("auth-reservation-list-unknown", "GET", "/reservations", auth="Bearer unknown", status=401, code="unauthenticated")
body = p.body()
payload = json.dumps(body).encode()
address = urllib.parse.urlsplit(args.base)
barrier = threading.Barrier(50)


def worker(number):
    start = time.monotonic()
    connection = http.client.HTTPConnection(address.hostname, address.port, timeout=5)
    try:
        connection.putrequest("POST", "/reservations")
        connection.putheader("Content-Type", "application/json; charset=utf-8")
        connection.putheader("Content-Length", str(len(payload)))
        connection.putheader("Authorization", "Bearer "+p.a)
        connection.putheader("Idempotency-Key", "staged-50")
        connection.endheaders()
        connection.send(payload[:-1])
        # Every connection has initiated its HTTP request before any can finish.
        barrier.wait(timeout=3)
        connection.send(payload[-1:])
        response = connection.getresponse()
        status = response.status
        value = json.loads(response.read())
        ctype = response.getheader("Content-Type")
    except Exception as error:
        barrier.abort()
        status, value, ctype = 0, {"transport_error":str(error)}, ""
    finally:
        connection.close()
    finish = time.monotonic()
    with p.lock:
        p.counter += 1
        p.trace.append(dict(operation=p.counter, method="POST", path="/reservations", peer=args.base,
                            body=body, has_token=True, key="staged-50", status=status, response=safe(value),
                            duration_seconds=finish-start, request_started_monotonic=start, request_finished_monotonic=finish,
                            method_note="Valid Content-Length request body sent except final byte; release barrier after all 50 HTTP requests are initiated."))
        p.statuses.append(status)
        p.latencies.append(("/reservations", finish-start, status))
        p.content_types.append(ctype.lower().replace(" ", ""))
        p.race_latencies.append(dict(request=number, group="staged-50", elapsed_seconds=finish-start,
                                     started_monotonic=start, finished_monotonic=finish, status=status))
    return status, value


with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    receipts = list(executor.map(worker, range(50)))
statuses = [status for status, _ in receipts]
events = sorted([(x["started_monotonic"], 1) for x in p.race_latencies]+[(x["finished_monotonic"], -1) for x in p.race_latencies])
active = peak = 0
for _, delta in events:
    active += delta
    peak = max(peak, active)
p.check("max-concurrency", peak == 50 and statuses.count(201) == 1 and statuses.count(200) == 49,
        "50 overlapping real requests; one 201 and 49 original replays", {"peak":peak, "status_counts":{str(status):statuses.count(status) for status in set(statuses)}})
p.check("max-concurrency-timing", peak == 50 and all(x["elapsed_seconds"] < 5 and x["status"] > 0 for x in p.race_latencies))
p.check("retry-no-duplicate", all(value == receipts[0][1] for _,value in receipts) and len(p.call("GET", "/reservations", token=p.a)[1].get("reservations", [])) == 1)
raise SystemExit(1 if p.finish() else 0)
