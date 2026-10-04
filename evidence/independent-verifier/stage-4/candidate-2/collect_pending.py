"""Collect original package evidence while explicitly withholding execution."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
PACKAGE = 'TK-20261004-S4-independent-verifier-CANDIDATE-2'


def main():
    out = ROOT / 'intake-pending-02'
    out.mkdir(exist_ok=False)
    source = REPO / 'evidence/coordinator/handoffs'
    packet = source / (PACKAGE + '.txt')
    delivery = source / (PACKAGE + '-delivery.json')
    raw = packet.read_bytes()
    d = json.loads(delivery.read_text())
    assert d['parts'] == len(d['deliveries']) == 23
    assert [x['part'] for x in d['deliveries']] == list(range(1, 24))
    assert all(x['status'] == 'accepted' for x in d['deliveries'])
    (out / 'original-full-packet.txt').write_bytes(raw)
    (out / 'original-delivery.json').write_bytes(delivery.read_bytes())
    value = dict(package=PACKAGE, candidate='58270860cb6a762c8a4c2a551672701fb00bd613',
        stage_4_tree='00e208c746a488a9b4cb0761efd04b90c4248dd8', part_count=23,
        all_parts=[dict(part=x['part'], message_id=x['message_id']) for x in d['deliveries']],
        all_original_acceptances=True,
        intake_method='Recovery of saved original full packet and original accepted receipt IDs; no resend claimed',
        packet_sha256=hashlib.sha256(raw).hexdigest(),
        end_received=raw.count(('END ' + PACKAGE).encode()) == 1,
        final_completion_marker_received=False, acknowledged_before_execution=False, execution_authorized=False,
        request_for_original_part23_content_message_id='43676873-950a-462a-b63f-c21a39adf6ba',
        preparation_provenance_correction='55758fc9359ffa09805da224a7631d54daa97337',
        shared_execution_card=28, current_candidate_operations=0,
        recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    assert not ('FINAL COMPLETION MARKER: END ' + PACKAGE).encode() in raw
    (out / 'intake-pending.json').write_text(json.dumps(value, indent=2) + '\n')
    (out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(original_parts_collected=23, final_marker_missing=True, execution_authorized=False)))


if __name__ == '__main__':
    main()
