"""Genuine earlier-process historical export and immutable receipt probes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stage-1"))
import argparse
import re
from probe import Probe, fixture
from wire_oracle import expected_wire
import datetime as dt
from zoneinfo import ZoneInfo

parser = argparse.ArgumentParser()
parser.add_argument("--base", required=True)
parser.add_argument("--peer", required=True)
parser.add_argument("--legacy", required=True)
parser.add_argument("--candidate", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
args.case = "legacy-receipts"
p = Probe(args)
p.setup()
replaced_token = p.a
p.setup(fixture(zone="Europe/Berlin", opens="18:00", closes="23:00", tables=1), base=args.legacy)
old_token = p.a
old_body = p.body("t0", "0001-01-01T21:30", 2)
old = p.create(old_body, key="old-historic", base=args.legacy)
p.check("legacy-source-genuine", old.get("starts_at") == "0001-01-01T21:30:00+00:53:28" and old.get("ends_at") == "0001-01-01T23:00:00+00:53:28", "actual earlier HTTP process supplies historical second offsets", old)
future_body = p.body("t0", "2070-01-01T18:00", 2)
future = p.create(future_body, key="old-future", base=args.legacy)
moves = {"moves":[{"reference":future["reference"], "party_size":1}]}
batch = p.expect("legacy-batch-original", "POST", "/reservation-moves", moves, token=old_token, key="old-batch", base=args.legacy, status=201)
cancelled = p.expect("legacy-cancelled", "POST", "/reservations/"+future["reference"]+"/cancel", {}, token=old_token, base=args.legacy)
snapshot = p.state(base=args.legacy)
p.expect("legacy-import", "POST", "/_test/import", snapshot, status=204)
p.check("legacy-export-equality", p.state() == snapshot)
p.expect("legacy-replacement", "GET", "/reservations", token=replaced_token, status=401, code="unauthenticated")
p.check("legacy-record-immutable", p.call("GET", "/reservations/"+old["reference"], token=old_token) == (200, dict(old, table_ids=[old["table_id"]])))
p.check("legacy-original-receipt", p.call("POST", "/reservations", old_body, token=old_token, key="old-historic") == (200, old))
p.check("legacy-original-receipt", p.call("POST", "/reservations", future_body, token=old_token, key="old-future") == (200, future))
p.check("legacy-batch-original", p.call("POST", "/reservation-moves", moves, token=old_token, key="old-batch") == (200, batch))
p.check("legacy-cancelled", p.call("GET", "/reservations/"+future["reference"], token=old_token) == (200, dict(cancelled, table_ids=[cancelled["table_id"]])))
new_body = p.body("t0", "0001-01-01T18:00", 2)
new = p.create(new_body, token=old_token, key="new-historic")
local = dt.datetime(1, 1, 1, 18, tzinfo=ZoneInfo("Europe/Berlin"))
p.check("legacy-new-write", new.get("starts_at") == expected_wire(local) and new.get("starts_at_local") == new_body["starts_at_local"] and re.fullmatch(r".*[+-]\d{2}:\d{2}", new["starts_at"]) is not None, expected_wire(local), new)
mixed = p.state()
p.expect("legacy-mixed-transfer", "POST", "/_test/import", mixed, base=args.peer, status=204)
p.check("legacy-mixed-transfer", p.state(base=args.peer) == mixed)
p.check("legacy-peer-original-receipt", p.call("POST", "/reservations", old_body, token=old_token, key="old-historic", base=args.peer) == (200, old))
p.check("legacy-peer-original-receipt", p.call("POST", "/reservation-moves", moves, token=old_token, key="old-batch", base=args.peer) == (200, batch))
p.check("legacy-peer-original-receipt", p.call("GET", "/reservations/"+old["reference"], token=old_token, base=args.peer) == (200, dict(old, table_ids=[old["table_id"]])))
raise SystemExit(1 if p.finish() else 0)
