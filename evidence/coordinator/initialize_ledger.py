"""Create a conservative source-complete ledger, never a coverage claim."""
from pathlib import Path
import csv
import hashlib
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
RESULT = ROOT / 'band-work/final-result'
EVIDENCE = RESULT / 'evidence/coordinator'
EVIDENCE.mkdir(parents=True, exist_ok=True)
rows = []
sources = []
for stage in range(1, 5):
    source = ROOT / f'kickoff/tablekeeper/spec/stage-{stage}.md'
    text = source.read_text()
    sources.append({'path': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    section = 'Preamble'
    paragraph = []
    fence = []
    fenced = False
    start = 1
    index = 0

    def emit(content, line, kind):
        global index
        if not content.strip():
            return
        pieces = [content] if kind == 'schema/example' else re.split(r'(?<=[.!?])\s+(?=[A-Z`"(])', content)
        for piece in pieces:
            index += 1
            owner = 'systems-engineer'
            if stage == 2 and any(w in section.lower() for w in ['screen', 'signup', 'search', 'booking form', 'confirmation', 'lookup', 'visual', 'uncertain', 'upgrade', 'ui']):
                owner = 'interface-engineer'
            if stage == 1 and any(w in section.lower() for w in ['delivery', 'runtime']):
                owner = 'interface-engineer'
            rows.append({'requirement_id': f'TK-S{stage}-{index:03}', 'source_section': section,
                         'source_line': line, 'introduced_stage': stage, 'applicable_stages': ','.join(str(s) for s in range(stage, 5)),
                         'source_kind': kind, 'requirement_text': piece.strip(), 'owner': owner,
                         'candidate_full_revision': 'UNASSIGNED', 'verification_method': 'Independent specification-derived black-box probe; atomization review pending',
                         'executable_command_or_interaction': 'UNVERIFIED', 'evidence_path': 'UNVERIFIED', 'verdict': 'unverified'})

    def flush():
        if paragraph:
            emit(' '.join(paragraph), start, 'prose')
            paragraph.clear()

    for lineno, line in enumerate(text.splitlines(), 1):
        if line.startswith('```'):
            if fenced:
                emit('\n'.join(fence), start, 'schema/example')
                fence.clear()
                fenced = False
            else:
                flush()
                fenced = True
                start = lineno
            continue
        if fenced:
            fence.append(line)
            continue
        if line.startswith('#'):
            flush()
            section = line.lstrip('#').strip()
        elif not line.strip():
            flush()
        elif line.startswith('|'):
            flush()
            if not re.fullmatch(r'[|:\-\s]+', line):
                emit(line, lineno, 'table contract')
        elif re.match(r'^(?:- |\d+\. )', line):
            flush()
            start = lineno
            paragraph.append(line)
        else:
            if not paragraph:
                start = lineno
            paragraph.append(line.strip())
    flush()

with (EVIDENCE / 'requirements-ledger.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(EVIDENCE / 'requirements-ledger.md').write_text(
    '# Initial requirements ledger\n\n'
    'This source-complete index preserves every prose, table and schema fragment from the four official specs. '
    'It is a conservative intake ledger, not a claim that every row is normative or atomic. '
    'The independent verifier must split bundled obligations and schema fields, remove explanatory-only fragments '
    'from normative coverage counts, and maintain inherited requirements in each stage matrix. '
    'No candidate, command or outcome is verified at intake.\n\n'
    f'Source fragments: {len(rows)}. All verdicts: unverified.\n\n'
    'See requirements-ledger.csv for stable source references, owner, applicable stages and evidence columns.\n')
(EVIDENCE / 'source-provenance.json').write_text(json.dumps(sources, indent=2) + '\n')
event = {'wall_time_utc': datetime.now(timezone.utc).isoformat(), 'event': 'intake',
         'run_id': 'TK-20261004', 'dispatch_observed_utc': '2026-10-04T00:12:39Z',
         'seat': 'foundry-coordinator', 'harness': 'Codex', 'operator_configured_model': 'gpt-6.1-sol',
         'runtime_model_override': 'unknown/not exposed', 'runtime_effort': 'unknown/not exposed',
         'usage_tokens': None, 'estimated_cost_usd': None, 'billed_cost_usd': None,
         'source_fragments': len(rows), 'highest_consecutive_accepted_stage': 0,
         'note': 'Clean empty result working tree; all four configured participants present; reciprocal seat replies confirmed. No implementation or checks yet.'}
with (EVIDENCE / 'run-ledger.jsonl').open('a') as f:
    f.write(json.dumps(event) + '\n')
print(json.dumps({'source_fragments': len(rows), 'requirements_ledger': str(EVIDENCE / 'requirements-ledger.csv')}))
