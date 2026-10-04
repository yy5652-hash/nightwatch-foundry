"""Append a factual transport correction without changing sealed preparation."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from intake_prepare import REPO, preserve


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    out = ROOT / 'provenance-correction-01'
    out.mkdir(exist_ok=False)
    source = REPO / 'evidence/coordinator/handoffs/TK-20261004-S4-independent-verifier-REPAIR-1-delivery.json'
    source_raw = source.read_bytes()
    transport = json.loads(source_raw)
    original_raw = (ROOT / 'intake.json').read_bytes()
    original = json.loads(original_raw)
    deliveries = transport['deliveries']
    assert transport['parts'] == len(deliveries) == 22
    assert sorted(d['part'] for d in deliveries) == list(range(1, 23))
    assert len({d['message_id'] for d in deliveries}) == 22
    comparisons = []
    for part in original['all_parts']:
        entry = next(d for d in deliveries if d['part'] == part['part'])
        assert entry['status'] == entry['response']['status'] == 'accepted'
        assert part['message_id'] == entry['message_id'] == entry['response']['message_id']
        comparisons.append(dict(part=part['part'], original_message_id=part['message_id'],
                                accepted_original=True, matches_recorded_intake=True))
    sealed = preserve('df698fb0e260279a55a56c71a6edfb1c9f398199',
                      ['evidence/independent-verifier/stage-4/repair-1'])
    corrected = deepcopy(original)
    corrected.update(resent_parts=[], missing_parts_requested_on_inbound=None,
        recorded_original_accepted_parts=22, transport_resends=0,
        missing_part_request_delivered_to_coordinator=False,
        receive_context_note='Initially incomplete visible receive context does not establish missing delivery or a resend. All22 recorded intake IDs match the coordinator original accepted receipts.',
        unsupported_historical_claims=dict(resent_parts=original['resent_parts'],
            missing_parts_requested_on_inbound=original['missing_parts_requested_on_inbound']),
        provenance_correction_inbound='71885435-bb21-4a10-bef3-8029449c38ac',
        provenance_correction_basis='22 recorded accepted original receipts and coordinator explicit no-resend/no-delivered-missing-request statement',
        reciprocal_acknowledgment_message_id=None)
    assert corrected['all_parts'] == original['all_parts']
    assert corrected['all_parts_received'] and corrected['end_received'] and corrected['final_completion_marker_received'] and corrected['acknowledged_before_preparation']
    assert corrected['execution_authorized'] is False
    (out / 'corrected-intake.json').write_text(json.dumps(corrected, indent=2) + '\n')
    (out / 'original-transport-receipts.json').write_bytes(source_raw)
    (out / 'sealed-preparation-preservation.json').write_text(json.dumps(sealed, indent=2) + '\n')
    proof = dict(corrected_at=datetime.now(timezone.utc).isoformat(),
        original_intake_sha256=sha(original_raw), transport_source=str(source),
        transport_sha256=sha(source_raw), comparisons=comparisons,
        original_intake_and_preparation_untouched=True, all22_original_ids_match=True,
        resends_supported=False, reciprocal_acknowledgment_id='unknown',
        service_counts_changed=False, candidate_execution=False,
        coordinator_statement_inbound='71885435-bb21-4a10-bef3-8029449c38ac')
    (out / 'proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    (out / 'executed-source.py').write_bytes(Path(__file__).read_bytes())
    ledger = ROOT.parent / 'ledger.jsonl'
    before = ledger.read_bytes()
    event = dict(event='stage4-repair1-intake-provenance-correction', logged_at=proof['corrected_at'],
        original_error='Unsupported transport resend and delivered missing-part-request claims',
        original_records_retained=True, original_accepted_parts=22, recorded_message_ids_match=True,
        transport_resends=0, reciprocal_acknowledgment_id='unknown', current_execution_held=True,
        highest_consecutive_accepted=3, service_counts_changed=False,
        evidence='repair-1/INTAKE_PROVENANCE_CORRECTION.md')
    ledger.write_bytes(before + (json.dumps(event) + '\n').encode())
    assert ledger.read_bytes().startswith(before)
    assert (ROOT / 'intake.json').read_bytes() == original_raw
    print(json.dumps(dict(original_accepted_parts=22, ids_match=22, sealed_files_unchanged=sealed['files'],
                         original_intake_untouched=True, transport_resends=0, candidate_operations=0)))


if __name__ == '__main__':
    main()
