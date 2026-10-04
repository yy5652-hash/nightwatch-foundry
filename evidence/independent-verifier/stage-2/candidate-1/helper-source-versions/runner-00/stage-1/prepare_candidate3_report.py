"""Specialize the verifier-owned report assembler for the executed candidate."""
from pathlib import Path

here = Path(__file__).resolve().parent
source = (here / "candidate2_report.py").read_text()
source = source.replace("repaired-candidate", "timestamp-repaired candidate")
source = source.replace('CANDIDATE = "dd644198b6c0c24cebaee74435ac13d4dc33bd99"', 'CANDIDATE = "b4a124e3671ec22a4df0780343f6389ff4b70d05"')
source = source.replace('TARGET = HERE / "candidate-2"', 'TARGET = HERE / "candidate-3"')
source = source.replace("independent-verifier-s1-dd64419-", "independent-verifier-s1-b4a124e-")
source = source.replace('metadata = json.loads((TARGET / "runtime-01/preflight.json").read_text())', 'metadata = json.loads((TARGET / "runtime-02/preflight.json").read_text())')
source = source.replace('commands = json.loads((TARGET / "runtime-01/commands.json").read_text())', 'commands = json.loads((TARGET / "runtime-02/commands.json").read_text())')
source = source.replace('TARGET / "runtime-01" /', 'TARGET / "runtime-02" /')
source = source.replace('sources["runtime-01"]', 'sources["runtime-02"]')
source = source.replace('TK-20261004-S1-independent-verifier-CANDIDATE-2.txt', 'TK-20261004-S1-independent-verifier-CANDIDATE-3.txt')
source = source.replace('(\"candidate-handoff\", \"evidence/coordinator/handoffs/TK-20261004-S1-independent-verifier-CANDIDATE-3.txt\")]', '(\"candidate-handoff\", \"evidence/coordinator/handoffs/TK-20261004-S1-independent-verifier-CANDIDATE-3.txt\"), (\"timestamp-decision\", \"evidence/coordinator/timestamp-representation-decision.md\")]')
old = '["runtime-01/probes", "runtime-01/reproductions", "runtime-01/calendar", "runtime-02/calendar-minimal"]'
new = '["runtime-02/probes", "runtime-02/original-minimal", "runtime-02/calendar-minimal", "runtime-02/race50", "runtime-02/legacy"]'
assert source.count(old) == 2
source = source.replace(old, new)
source = source.replace('verdict="reject"', 'verdict="accept"')
source = source.replace('phase="stage-1-candidate-2-verdict"', 'phase="stage-1-candidate-3-verdict"')
source = source.replace('representation_question="Two historical RFC3339 failures retained pending explicit coordinator interpretation. Seven other failed rows cover two valid-local-date refusal families."', 'interpretation="Acceptance follows the recorded nearest-representable-minute-offset interpretation; genuine imported original strings/receipts, including historical offset seconds, remain immutable. Literal historic wire-offset compliance is an explicit exception."')
source = source.replace('with (TARGET / "coverage.csv").open("w", newline="") as f:', 'assert all(row["verdict"] == "verified" for row in rows), [(r["requirement_id"],r["verdict"]) for r in rows if r["verdict"] != "verified"]\nwith (TARGET / "coverage.csv").open("w", newline="") as f:')
source = source.replace('str(HERE / "candidate2_report.py")', 'str(HERE / "candidate3_report.py")')
source = source.replace('print(json.dumps({k:summary[k]', 'print(json.dumps({k:summary[k]')
assert 'CANDIDATE = "b4a124' in source and 'TARGET = HERE / "candidate-3"' in source
(here / "candidate3_report.py").write_text(source)
print("Prepared candidate-3 evidence assembler; no evidence or verdict generated yet")
