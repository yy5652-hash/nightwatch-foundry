# JSON-REPAIR-2 own parser reference correction

The first host grammar run in `systems-engineer-json-parser-host-01` has665 assertions:664 passed, one failed,0.276602833s. Production module SHA6a063cf3a93b7e022b1fdace3d6357088cb7197b07a6f69c1c12d64d57a16263 is unchanged by the evidence repair. Its exact original executed probe is saved alongside the original summary/assertions/trace.

The failed `corpus-069 rejection` uses UTF-16 bytes `ff fe 7b 00 7d 00`. The probe passed bytes directly to the independent standard json.loads reference, which auto-detected UTF-16 and admitted an object. The adopted shared loads(bytes|str) contract requires strict UTF8 and no autodetection. The service correctly rejects those bytes; the reference must explicitly decode UTF8 before evaluating JSON grammar. This is an own reference error, not an observed container parser defect.

The corrected reference decodes bytes as UTF8 first. Its seeded original-tree renderer also uses ordinary comma separators in both whitespace variants. The first run's colon item separator produced some invalid multi-item original samples; their reference-defined valid/invalid expectations were still correct, but the new renderer ensures originals are valid and mutations supply the invalid corpus. Both original source and results remain unchanged in the first folder. Corrected runs use new output folders; no failed observation is relabelled as a later pass.

Separate initial same-module host numeric and direct depth/copy checks pass1442/1442 and171/171 assertions. These are module checks, not constrained HTTP or acceptance proof. The new committed full image and raw independent-process deep state transfer remain required.
