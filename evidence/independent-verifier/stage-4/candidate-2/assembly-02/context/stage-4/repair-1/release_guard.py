"""Preparation is never a repaired-candidate execution release."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from stage4_probe import validate_release

REJECTED = '261e4d9456a04a8b57ed46db71a09ac267ff15a9'
PREPARATION = 'TK-20261004-S4-independent-verifier-REPAIR-1'


def validate(release, browser=False):
    if release.get('candidate') == REJECTED:
        raise ValueError('Rejected candidate1 cannot acquire repaired evidence')
    if release.get('new_complete_execution_package') is not True:
        raise ValueError('New full execution package is required; preparation alone is insufficient')
    if release.get('preparation_only') is not False:
        raise ValueError('Preparation is not an execution release')
    if not re.fullmatch('[0-9a-f]{40}', release.get('candidate', '')):
        raise ValueError('Named full repaired candidate is required')
    validate_release(release)
    source = json.loads(Path(release['source_proof_path']).read_text())
    if source.get('candidate') != release['candidate'] or source.get('stage_4_tree') != release.get('stage_4_tree') or not re.fullmatch('[0-9a-f]{40}', source.get('stage_4_tree', '')):
        raise ValueError('Source proof must name the exact new candidate and graded tree')
    resources = json.loads(Path(release['resource_proof_path']).read_text())
    if resources.get('internal') is not True or not resources.get('containers'):
        raise ValueError('Actual constrained internal runtime proof is required')
    intake_path = Path(release['package_intake_path'])
    intake = json.loads(intake_path.read_text())
    identifier = intake.get('package', intake.get('package_identifier', ''))
    if identifier == PREPARATION or 'CANDIDATE' not in identifier:
        raise ValueError('An acknowledged candidate-execution intake is required')
    if intake.get('candidate') != release['candidate']:
        raise ValueError('Execution intake must name this exact candidate')
    for key in ['all_parts_received', 'end_received', 'final_completion_marker_received',
                'acknowledged_before_execution', 'execution_authorized']:
        if intake.get(key) is not True:
            raise ValueError('Incomplete current intake: ' + key)
    parts = intake.get('all_parts', [])
    if not parts or sorted(p['part'] for p in parts) != list(range(1, intake['part_count'] + 1)):
        raise ValueError('Every actual current numbered part must be bound')
    message_ids = [p.get('message_id', '') for p in parts]
    if len(set(message_ids)) != len(parts) or any(not re.fullmatch('[0-9a-f-]{36}', value) for value in message_ids):
        raise ValueError('Actual unique current inbound message IDs are required')
    if not release.get('rejected_evidence_preserved'):
        raise ValueError('Original rejected artifacts must remain preserved')
    preserved = Path(release.get('rejected_preservation_path', ''))
    if not preserved.is_file() or hashlib.sha256(preserved.read_bytes()).hexdigest() != release.get('rejected_preservation_sha256'):
        raise ValueError('Concrete named rejected-evidence preservation proof is required')
    preservation = json.loads(preserved.read_text())
    if preservation.get('revision') != 'a744fd0cbe3fa24399088d3e4dc8db960bf5c9f3' or not preservation.get('records') or any(record.get('identical') is not True for record in preservation['records']):
        raise ValueError('Rejected evidence must match its original named seal')
    if browser:
        from stage4_browser import validate_selectors
        validate_selectors(release)
        proof = Path(release['selector_proof_path'])
        value = json.loads(proof.read_text())
        if value.get('candidate') != release['candidate']:
            raise ValueError('Selectors must be actually observed on the new exact candidate')
    return release
