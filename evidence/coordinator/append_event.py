"""Append JSON evidence; never overwrite an earlier event."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

event = json.loads(sys.argv[1])
event.setdefault('wall_time_utc', datetime.now(timezone.utc).isoformat())
event.setdefault('run_id', 'TK-20261004')
event.setdefault('seat', 'foundry-coordinator')
event.setdefault('harness', 'Codex')
event.setdefault('operator_configured_model', 'gpt-6.1-sol')
event.setdefault('runtime_model_override', 'unknown/not exposed')
event.setdefault('runtime_effort', 'unknown/not exposed')
event.setdefault('usage_tokens', None)
event.setdefault('estimated_cost_usd', None)
event.setdefault('billed_cost_usd', None)
with (Path(__file__).parent / 'run-ledger.jsonl').open('a') as stream:
    stream.write(json.dumps(event, ensure_ascii=True) + '\n')
print(event['event'])
