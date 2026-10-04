"""Bind original saved packet and separately delivered marker recovery honestly."""
import datetime, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def main():
    old=json.loads((ROOT/'intake-pending-02/intake-pending.json').read_text())
    marker=(ROOT/'recovered-part-23.txt').read_bytes()
    package=old['package']
    assert marker.count(('END '+package).encode())==2
    assert ('FINAL COMPLETION MARKER: END '+package).encode() in marker
    assert old['part_count']==len(old['all_parts'])==23
    old.update(all_parts_received=True, end_received=True,
        final_completion_marker_received=True, acknowledged_before_execution=True,
        execution_authorized=True, reciprocal_acknowledgement_message_id=None,
        acknowledgement_method='Successful jam_reply_to_message staged on recovered-part inbound before any current source/runtime action; outgoing reply ID unavailable',
        acknowledgement_inbound='5d30a039-8507-4ff1-93f3-96d1f9911507',
        original_part23_message_id='b36d905e-7fdd-4528-87a6-f1b8c9f70004',
        marker_recovery_message_id='5d30a039-8507-4ff1-93f3-96d1f9911507',
        marker_recovery_sha256=hashlib.sha256(marker).hexdigest(),
        intake_method='Original full packet and 23 original accepted receipt IDs recovered from saved handoff; part23 content and both literal markers separately supplied on the named recovery inbound. No original receipt replaced and no transport resend inferred.',
        recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    assert not (ROOT/'intake.json').exists()
    (ROOT/'intake.json').write_text(json.dumps(old,indent=2)+'\n')
    print(json.dumps(dict(all_parts=23,both_markers=True,execution_authorized=True,candidate=old['candidate'])))
if __name__=='__main__':main()
