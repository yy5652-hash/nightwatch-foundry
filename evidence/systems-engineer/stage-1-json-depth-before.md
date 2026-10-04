# Nested JSON module boundary: observed before repair

Assignment boundary: coordinator message `967c90be-6337-455c-aea6-3c9b209b6b99`
within complete JSON-REPAIR-1. Tested module revision
`00940d4777c316c1369e744109885d58c85373ec`, SHA-256
`913800d80172392e6357b4a9c6d2b5a80d47859779e4b0c7024b5e6e61a71078`.
These are own codec observations, not an HTTP rejection or independent verdict.
Existing core, Interface runtime files and Stage 2 are still held.

Stage 1 section 3.4 imposes no nesting ceiling on ignored valid fields. The own
probe independently checks a shallow finite decimal leaf with stdlib Decimal and
then composes valid object/array wrappers. This construction proves grammar
without asking the tested codec to declare its own input valid. Saved raw UTF-8
payloads, wrapper counts, hashes and measured byte lengths accompany each run.
No recursion-limit setting is changed.

Initial command:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-depth-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-depth-before-01
```

It produced 60 assertions, 3 passed and 57 failed, in 0.022967459 s. Shapes are
object, array and alternating; wrapping depths 750, 1000, 1100 and 1200. Maximum
payload is 13,242 bytes. Operations are a composed parse/encode/equality check,
direct-tree validation, encoding, exact equality and historical equality.
Recursive Python traversal refuses valid nested trees. The composed operation
does not isolate the decoder; the initial room description that included parsing
as a failed boundary was too broad and is corrected by the separate observation
below. Original observations remain unchanged.

The second probe revision adds a decoder-only observation and depth 1600:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-json-depth-probes.py --module stage-1/json_codec.py --out evidence/systems-engineer/systems-engineer-json-depth-before-02
```

It produced 90 assertions, 18 passed and 72 failed, in 0.033346375 s, maximum
17,642 bytes. All 15 decoder-only checks pass on this actual Python 3.12 runtime.
The failed paths are recursive validation/encoding/equality, with recorded
`JsonCodecError` messages `Invalid recursive JSON tree`, `Unable to encode JSON
tree` or `Invalid recursive JSON comparison`. The reported recursion limit is
1000. A separate decoder-only control also decoded arrays at depths 2500 and
3000, payloads 5,001 and 6,001 bytes. No decoder refusal is asserted.

At 1100 wrappers the payload lengths are 12,142 bytes for objects, 2,242 bytes for
arrays and 7,192 bytes for alternating containers. The finite unknown leaf is
`1e4300`, with ordinary boolean and Unicode string controls. Its historical
profile comparison must stably return false because an actual old successful
receipt cannot contain an overflowed float; it must not raise a depth error.

The correction will remove recursive tree traversal using explicit stacks,
preserving validation, cycle refusal, exact/legacy equality and the bytes API.
The standard decoder is retained because all isolated decoder controls passed;
no parser defect is invented. New constrained-image checks will bind the repaired
module separately. Real deep receipt/export/import behavior remains pending core
release and will require its own HTTP observations. These modest payloads do not
prove arbitrary-depth performance. No peer test source was read/copied, host
dependency installed or unrelated path changed. Highest accepted stage remains 0.
