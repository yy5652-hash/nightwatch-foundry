"""Minimal HTTP reproductions of independent Candidate 1 failures."""
import argparse
import copy
from probe import Probe

p = argparse.ArgumentParser()
p.add_argument("--base", required=True)
p.add_argument("--candidate", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()
a.peer = None
a.case = "minimal-rejection-reproductions"
probe = Probe(a)
fixture = {"users": [], "restaurants": [{"id": "r", "name": "V", "timezone": "UTC", "slot_minutes": 30,
           "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 0,
           "opening_hours": [{"weekday": "fri", "opens": "18:00", "closes": "23:00"}],
           "tables": [{"id": "t", "label": "T", "capacity": 2}]}], "reservations": []}
for field in ["opening_hours", "tables"]:
    missing = copy.deepcopy(fixture)
    del missing["restaurants"][0][field]
    probe.expect("reset-missing-restaurant-" + field, "POST", "/_test/reset", missing, status=422, code="validation_failed")
probe.expect("reset-status", "POST", "/_test/reset", fixture, status=204)
probe.expect("calendar-year-max", "GET", "/availability?restaurant_id=r&date=9999-12-31&party_size=2", status=200)
raise SystemExit(1 if probe.finish() else 0)
