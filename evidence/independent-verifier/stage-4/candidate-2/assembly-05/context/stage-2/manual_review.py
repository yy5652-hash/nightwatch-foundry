"""Record completed source and screenshot judgments with concrete observed evidence."""
import json
from pathlib import Path
from requirements import ROWS
target=Path(__file__).resolve().parent/'candidate-1'
rows={r['requirement_id']:r for r in ROWS};observations=[]
def record(rid,evidence,interaction,note='',method='independent source/runtime/screenshot review'):
    assert rid in rows
    paths=[str(target/p) for p in evidence]
    assert all(Path(p).is_file() for p in paths)
    observations.append(dict(requirement_id=rid,verdict='verified',evidence=paths,interaction=interaction,method=method,note=note))
runtime=['runtime-evidence/preflight.json','runtime-evidence/commands.json','image-identity.json','cleanup.json']
for rid in ['dockerfile','run-document','single-image','offline','cpu','memory','startup','packaged-assets','listen-all','port-override','port-default']:
    record('TK1-'+rid,runtime+['runtime-evidence/RUN-reviewed-source.md'],
      'Reviewed named clean-clone RUN.md; executed its docker build/start surface, default 8080 and override 18309. Separate internal-network clients reached both health endpoints; Docker inspections show 2 CPU, 2 GiB, no service mounts and Internal=true network. Startup measurements 0.272538083/0.292209417 s.',
      'This inherited runtime obligation is executed against the current Stage 2 service. Build cache was available. Assets, stdlib runtime and IANA data are packaged; no uncached-build or full-resource-exhaustion claim.')
for rid in ['source-provenance','complete-clone','two-builders','history-preserved']:
    record('TK1-'+rid,['source-audit.json','audit/authored.log','audit/root-tree.log','audit/systems-inputs.log','audit/interface-inputs.log','preflight-evidence/preflight.json'],
      'Reviewed exact candidate history, root intake, full eight-part source handoff, current production imports, authored paths and both committed source-input declarations. Clean detached clones contain complete committed service files with no symlink/submodule/nested-service repository.',
      'Inherited Stage 1 source audit remains intact. Current contributions are Systems core e683361 and Interface transport/browser ff8472 through 93544c6. Seat source-input exclusions are declarations rather than machine-wide forensic proof.')
record('TK1-own-stage',['official-evidence/report.json','official-evidence/stage-3.counts.json','official-evidence/stage-3.log','source-audit.json'],
  'Ran the unchanged isolated harness at --stage 2 from kickoff on the exact clean candidate. It claims Stage 2, reruns 120 Stage 1 checks and 25 Stage 2 checks on the Stage 2 container, then stops after one failed Stage 3 overshoot check.',
  'The own-stage deployment obligation advances with the current service; frozen Stage 1 remains byte-identical. Stage 3 overshoot collected 7, passed 0, failed 1, not executed 6; no later stage is established.')
for rid in ['frozen-stage1','copied-base','stage2-delivery','stage2-source']:
    record('TK2-'+rid,['source-audit.json','audit/frozen-diff.log','audit/source-copy.log','audit/authored.log','runtime-evidence/RUN-reviewed-source.md','image-identity.json'],
      'Compared frozen Stage 1 to 2a4b0408a3453bc87d86bca3d0ec571f479e03ca, reviewed complete initial five-file copy and authored history, then built the complete independent Stage 2 image from its own RUN.md and checked committed/image source hashes.',
      'The freeze manifest itself is unchanged. New independent decimal-limit observations revoke its prior acceptance in a separate supplemental verdict; byte preservation and historical ownership still hold.')
for width in [375,1280]:
    for route in ['search','signup','login','lookup']:
        evidence=['browser-01/browser/visual-review-pending.json',f'browser-01/browser/visual-{width}-{route}.png',f'browser-01/browser/visual-{width}-{route}-keyboard.png','visual-01/visual/browser-actions.json','visual-01/visual/assertions.json']
        record(f'TK2-visual-{width}-{route}-usable',evidence,
          f'Viewed the real {route} screen at {width} CSS pixels with labelled controls and consistent navigation; actual auth/search/booking/lookup flows and the 375px Tab/Enter pair booking/retry completed. Page measurements record scrollWidth <= clientWidth.',
          'Ordinary product flow usability passes this review. Exact integer and historical end-time display failures are separately failed rows; no claim of all-range faithful content is hidden in this visual judgment.')
        record(f'TK2-visual-{width}-{route}-focus',evidence,
          f'Pressed Tab in the real {route} screen at {width}px and inspected screenshot plus active-element bounds/computed outline: visible 3px solid rgb(170,107,41). On mobile pair selection, Enter focuses the labelled Guests input; Tab/Enter submits and retries the actual booking.')
        record(f'TK2-visual-{width}-{route}-contrast',evidence,
          'Inspected actual text/control colours and screenshots; separately computed effective text/background contrast through transparent ancestors: captured normal text >=4.5:1 and large text >=3:1, with disabled text excluded. Primary white-on-dark-green actions and brown focus outlines are distinct.',
          'Scoped screenshot/computed-style review, not a claim of complete WCAG certification. Measurements and actual feedback states are preserved.')
for state in ['available','unavailable','selected','loading','successful','refused','uncertain','empty']:
    file_state='available-unavailable' if state in ['available','unavailable'] else state
    evidence=[f'visual-01/visual/states-{width}-{file_state}.png' for width in [375,1280]]+['visual-01/visual/browser-actions.json','visual-01/visual/assertions.json']
    record('TK2-visual-state-'+state,evidence,
      f'Viewed genuine {state} state at both widths. Available seats are green, unavailable seats muted/disabled, selected pairs outlined; loading has an explicit progress message, success a reference, refusal clay feedback, uncertainty amber retry feedback and empty a closed-day message. Refusal followed actual rival booking; uncertainty followed actual committed response loss.')
for rid in ['coherent','human-labels','actions','navigation','no-invented-facts']:
    record('TK2-visual-'+rid,['browser-01/browser/visual-375-search.png','browser-01/browser/visual-1280-pair-form.png','visual-01/visual/states-1280-successful.png','visual-01/visual/states-375-uncertain.png','source-audit.json'],
      'Reviewed the real cream/green/clay product, serif headings and consistent labelled controls; restaurant and human table labels appear prominently, declared pairs show both labels, primary buttons are clear, and required route navigation is consistent. Local fixture names are used without reviews, ratings, photos, fabricated usage or establishment claims.',
      'General presentation passes. Precision and historical end-time truth are separately failed obligations; no hidden judging or product score is claimed.')
(target/'manual-observations.json').write_text(json.dumps(observations,indent=2))
print(json.dumps(dict(observations=len(observations),unique=len({o['requirement_id'] for o in observations}))))
