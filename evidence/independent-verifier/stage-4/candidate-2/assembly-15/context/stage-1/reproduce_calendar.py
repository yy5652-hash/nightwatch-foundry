"""Eight-operation reproduction of UTC-range calendar refusals."""
import argparse
from probe import Probe

parser = argparse.ArgumentParser()
parser.add_argument("--base", required=True)
parser.add_argument("--candidate", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
args.peer = None
args.case = "minimal-calendar-reproductions"
p = Probe(args)
for label, zone, day, weekday, opens, closes, local in [
    ("new-york-max", "America/New_York", "9999-12-31", "fri", "18:00", "23:00", "21:30"),
    ("berlin-min-midnight", "Europe/Berlin", "0001-01-01", "mon", "00:00", "06:00", "00:00")]:
    f = {"users":[{"id":"u", "email":"a@probe.invalid", "password":"verifier-pass", "display_name":"A"}],
         "restaurants":[{"id":"r", "name":"V", "timezone":zone, "slot_minutes":30,
                         "reservation_duration_minutes":90, "cancellation_cutoff_minutes":0,
                         "opening_hours":[{"weekday":weekday,"opens":opens,"closes":closes}],
                         "tables":[{"id":"t","label":"T","capacity":2}]}], "reservations":[]}
    p.expect("reset-status", "POST", "/_test/reset", f, status=204)
    login = p.expect("login-status", "POST", "/auth/login", {"email":"a@probe.invalid", "password":"verifier-pass"})
    p.expect("edge-"+label+"-availability", "GET", "/availability?restaurant_id=r&date="+day+"&party_size=2")
    p.expect("edge-"+label+"-create", "POST", "/reservations", {"restaurant_id":"r","table_id":"t","starts_at_local":day+"T"+local,"party_size":2}, token=login["token"], key=label, status=201)
raise SystemExit(1 if p.finish() else 0)
