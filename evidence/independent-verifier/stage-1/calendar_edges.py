"""Calendar-domain HTTP boundaries; no production or shipped-test imports.

An integer ordinal-seconds oracle avoids converting valid local instants into
Python's bounded UTC datetime. Historic second offsets are saved explicitly.
"""
import argparse
import datetime as dt
import re
from zoneinfo import ZoneInfo
from probe import Probe, fixture


def instant(value):
    parsed = dt.datetime.fromisoformat(value)
    return parsed.toordinal()*86400 + parsed.hour*3600 + parsed.minute*60 + parsed.second - int(parsed.utcoffset().total_seconds())


def run(p):
    for label, zone in [("utc", "UTC"), ("berlin", "Europe/Berlin"), ("new-york", "America/New_York")]:
        for tag, day in [("min", "0001-01-01"), ("max", "9999-12-31")]:
            p.setup(fixture(zone=zone, opens="18:00", closes="23:00", duration=90, slot=30, tables=1))
            prefix = "edge-"+label+"-"+tag
            starts = [day+"T"+clock for clock in ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30"]]
            value = p.expect(prefix+"-availability", "GET", "/availability?restaurant_id=r&date="+day+"&party_size=2")
            slots = value.get("slots", []) if isinstance(value, dict) else []
            p.check(prefix+"-slots", [s.get("starts_at_local") for s in slots] == starts, starts, slots)
            # Test the final fitting start, not just the opening instant.
            local = starts[-1]
            status, receipt = p.call("POST", "/reservations", p.body("t0", local, 2), token=p.a, key=prefix)
            p.check(prefix+"-create", status == 201, 201, {"status":status, "receipt":receipt})
            expected_start = dt.datetime.fromisoformat(local).replace(tzinfo=ZoneInfo(zone))
            expected_end = expected_start.replace(hour=23, minute=0)
            try:
                p.check(prefix+"-start-instant", instant(receipt["starts_at"]) == instant(expected_start.isoformat()), expected_start.isoformat(), receipt.get("starts_at"))
                p.check(prefix+"-end-instant", instant(receipt["ends_at"]) == instant(expected_end.isoformat()), expected_end.isoformat(), receipt.get("ends_at"))
            except (KeyError, ValueError, TypeError):
                p.check(prefix+"-start-instant", False, expected_start.isoformat(), receipt)
                p.check(prefix+"-end-instant", False, expected_end.isoformat(), receipt)
            # RFC3339 numeric offsets have hours and minutes, not offset seconds.
            if tag == "min" and label != "utc":
                rfc = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[+-]\d{2}:\d{2}"
                p.check(prefix+"-rfc3339", status == 201 and all(re.fullmatch(rfc, receipt.get(k, "")) for k in ["starts_at", "ends_at"]), "RFC3339 explicit offset", receipt)
    # Six hours at the minimum date additionally exercises a positive zone
    # offset crossing the UTC calendar minimum; no valid local date is removed.
    p.setup(fixture(zone="Europe/Berlin", opens="00:00", closes="06:00", duration=90, slot=30, tables=1))
    p.expect("edge-berlin-min-midnight-availability", "GET", "/availability?restaurant_id=r&date=0001-01-01&party_size=2")
    p.expect("edge-berlin-min-midnight-create", "POST", "/reservations", p.body("t0", "0001-01-01T00:00", 2), token=p.a, key="min-midnight", status=201)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    args.peer = None
    args.case = "calendar-edges"
    probe = Probe(args)
    run(probe)
    raise SystemExit(1 if probe.finish() else 0)
