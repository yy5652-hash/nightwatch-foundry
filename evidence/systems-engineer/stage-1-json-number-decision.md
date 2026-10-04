# Stage 1 JSON numeric value and legacy receipt analysis

Requested by coordinator message `57734b7a-1f7c-4ef2-a988-67607f0f61ce`, within frozen candidate-5 analysis. This is source reasoning and builder diagnostic evidence, not a production repair, new acceptance or source release. Candidate `f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250` remains rejected; both graded stages remain unchanged.

## Source reading

Stage 1 §5 distinguishes JSON type from invalid value. Its plain-decimal spelling restriction expressly applies to integer-valued query parameters. No corresponding spelling restriction is stated for body numbers. Section 8 requires an integer party size, not an integer token spelling; §7 compares the same JSON value after parsing. The current `integer_field` requires the Python class `int`, so it refuses body `1.0` and `1e0` even though their exact numeric values are integers. That implementation choice is narrower than the source's value-based reading.

My recommendation is to accept exact integer-valued body numbers by value: `1`, `1.0` and `1e0` are equal numbers for integer validation and current receipt comparison. Preserve boolean/string distinctions. A genuinely fractional party value receives 422 `validation_failed`, regardless of its magnitude. Query `1.0`, `1e0`, signs and other non-digit forms remain 422. Valid finite numbers in unknown fields are ignored for endpoint behavior while retained in complete parsed retry bodies; they cannot become malformed solely because a binary float would overflow.

For base fixture counts/capacity, my source recommendation is also 422 for a genuine fraction: it has the correct JSON number type but violates the integral-count rule. Strings and booleans remain wrong types, with 400 for these base fields. This status reading requires the coordinator's recorded decision; earlier fractional-count diagnostic expectations must remain historical rather than being relabeled. Party-size's explicit 422 override includes wrong types. Bounds already stated by the source continue to apply; no numeric or digit ceiling follows from the implementation language.

Literal `NaN`, `Infinity` and `-Infinity` are not JSON numeric tokens and remain malformed. Valid finite exponent/fraction tokens must reach authentication, missing-key/used-key resolution and endpoint checks in their existing order. The independently confirmed finite-fraction precedence failures are separate observations, not acceptance of this proposed design.

## Genuine old receipt evidence

Own client `stage-1-legacy-number-client.py` imports no service or verifier code. Driver `stage-1-legacy-number-run.py` ran a genuine pre-serializer Stage 1 image from revision `49287b4a5a1481f995c470ccae31776f03d4b863` and the matching candidate-5 image in two independent processes. The old service actually issued accounts, tokens, bookings and successful original receipts. Its unchanged HTTP export was transferred in memory into candidate 5. No export, password hash or session token was written to the evidence.

The observed state has schema 1 and receipts with exactly `body`, `key`, `method`, `path`, `response`, `user_id`. Neither source schema nor receipt fields identify numeric parser semantics or original numeric lexemes. Genuine source behavior:

| Original ignored numeric token | Old exported body value | Original retry | Source-parser alias | Distinct body |
|---|---|---|---|---|
| `0.100000000000000005` | `0.1` | 200, original response | `0.1`: 200 | `0.10000000000000002`: 409 |
| `9007199254740993.0` | `9007199254740992.0` | 200, original response | integer `9007199254740992`: 200 | integer `9007199254740993`: 409 |

Both original retries still returned exactly their real original response after candidate-5 import, using their actual old token. Distinct-body refusals persisted. Counterfactual decoding of the actual export with exact Decimal values shows that neither exact original token equals its exported value. That comparison is an analytical check against a genuine export, not a claim that an exact production codec was executed.

This establishes irreversible information loss before export. Exact-only comparison on historical bodies would break the original request retry. Converting every incoming number to float would break another observed obligation: the exact integer `9007199254740993` must remain different from the old rounded float receipt. Historical comparison must retain whether each incoming number had an integer token or a decimal/exponent token.

## Compatibility design recommendation

Keep newly executed writes exact and compare their numeric values without a spelling distinction; nested booleans remain distinct from numbers. Do not round complete new bodies to binary floats merely to accommodate older receipts.

When importing genuine unmarked old receipts, attach a private persisted source numeric profile. For that receipt's comparison only, integer tokens retain their exact integer meaning and decimal/exponent tokens undergo the old source's float projection. Compare recursively with the source's boolean/type distinctions. Re-export/re-import must preserve this profile alongside newer exact receipts. A new internal format/profile can identify exact receipts; relying on current stage number, response shape or a global import mode is insufficient when one state contains both origins. The implementation-defined state may carry comparison metadata, without substituting JSON strings for public numbers or changing original response values.

The archived public receipt and its comparison representation serve different purposes. Preserve the original emitted JSON values and schema for replay. Do not expand a legacy `0.1` to the exact binary floating ratio on export or response: that changes the JSON value the diner actually received. Preserve the integer/float provenance needed to reproduce old comparison in a separate private representation. The original request spelling cannot be reconstructed from the archive and must not be invented.

A finite incoming number that overflows the old float projection cannot equal any successfully archived old infinite value: the old engine rejected non-finite values before writing a receipt. It should be a different body for a used legacy key, with the normal 409 result, rather than a global malformed-JSON refusal. New keys and unknown fields remain subject to exact current semantics.

Exact number decoding, validation, equality and encoding must be coordinated across Engine and Interface's transport. A Decimal or coefficient/exponent representation is a possible internal choice, but binary floats are insufficient and converting ignored exponents immediately into enormous expanded integers is unnecessary. Retain exact finite numeric meaning, emit numeric JSON tokens, and preserve original receipts. Any chosen standard-library representation must be checked for its own exponent/context limits; no arbitrary replacement bound is justified here. This analysis does not claim performance for arbitrary payload sizes.

Required repair evidence would distinguish current `1`/`1.0`/`1e0` equality, genuine fractions at ordinary and observed large magnitudes, nested unknown finite exponent values, literal invalid constants, query grammar, missing/used-key precedence, failed-key reuse, atomic state, mixed legacy/exact receipt import and second export/import, and unchanged original responses. Independent reviewers derive their own checks.

## Executed command and measured result

From the result repository:

```sh
../../.venv/bin/python -B evidence/systems-engineer/stage-1-legacy-number-run.py --out evidence/systems-engineer/systems-engineer-s1-legacy-number-01
git diff f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250 --exit-code -- stage-1 stage-2
```

HTTP run: **16 operations, 24 assertions, zero failures**, 0.061681459 seconds. Complete driver: 1.212972709 seconds. Runtime resources: 2 CPU, 2 GiB, internal offline Docker network, no service mounts. Core/server image hashes match each full named revision. Both services and own network were removed with return code 0; images retained. Images: `systems-engineer-tablekeeper-s1:calendar-02` and `systems-engineer-tablekeeper-s1:decimal-05-20261004t023841`. Exact Docker argv, image IDs, resource inspections, hash proof, cleanup and per-command timing are in `systems-engineer-s1-legacy-number-01/runtime.json`; redacted observations and hashes in `probe.json`. All earlier genuine failures remain untouched.

Only Systems-owned evidence files changed. No service edits or approval/promotion are claimed. Highest independently accepted consecutive stage remains 0. Historical minute-offset/original-string and original-receipt schema decisions remain applicable. Harness Codex; configured model gpt-6.1-sol; actual runtime override, effort, usage, estimated cost and billed spend unknown. Factory elapsed is coordinator-owned.
