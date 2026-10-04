# Source applicability: 4301-digit positive integers

Systems conclusion: **applicable to Stage 1 and inherited Stage 2**. This is a source-derived applicability decision, not a new numeric maximum, API field or production repair. The verifier's observed failures in message `aecc8522-615f-4006-ad0b-a42920d28f81` concern exact Stage 2 candidate `4b92041057beb669d2e6c528e8268f4d0d1e6421` and genuine frozen Stage 1 source `2a4b0408a3453bc87d86bca3d0ec571f479e03ca`. Systems did not rerun or copy the independent probe implementation. Its exact reported traces remain verifier-owned in `evidence/independent-verifier/stage-2/candidate-1/decimal-01/decimal-limit/`.

## Written requirements

Stage 1 §4 defines the base restaurant counts and table capacity without a numeric or digit-length maximum (official source lines 101–106). Section 5 limits values exceeding a **stated** maximum or length (line 170); it does not declare the Python conversion limit as an application range. The same section requires integer query values to be plain decimal digits (lines 175–178). `10^4300+1` is positive, integral, 4301 plain ASCII digits, and a valid lexical JSON number when sent unquoted. It is neither a string nor a boolean, fraction, exponent-form query, NaN or Infinity.

Section 8 requires each fitting slot even when no table meets party size; capacity filtering then gives empty single-table lists (lines 305–310). Stage 2 adds pair capacity filtering and empty available_options under the same condition. No independent query maximum is introduced. Booking capacity refusal is a separate rule and does not authorize refusing the availability search.

The reported bodies/queries are approximately 5 KB and perform only small-window availability/bounded interval comparisons. The published 2 CPU/2 GiB and per-request time requirements do not establish a 4300-digit field limit. Later-stage policy maxima are separate future fields; they do not change these inherited base fixture/query rules.

## Required behavior

- Each otherwise valid reset that changes only grid, duration, cutoff or capacity to this positive integer succeeds with 204. The exact value remains available in configuration/export/import; it is not rounded, changed to a JSON string or truncated.
- Huge grid with an ordinary fitting duration offers just the opening candidate; an off-grid attempted booking is refused under the ordinary grid rule.
- Huge duration gives no fitting slots and outside_opening_hours on an unfit booking; no arbitrary huge endpoint timestamp is created.
- Huge cutoff permits ordinary create but refuses a later edit/cancel under cutoff_passed, without mutating occupancy, records or receipts.
- Huge capacity is usable for ordinary parties, with exact summed capacity for declared pairs in Stage 2.
- A positive plain-digit party query beyond the small fixture capacities returns 200 with normal fitting slots, each empty available_table_ids and (Stage 2) empty available_options.
- JSON parse/serialize, query conversion, export/import and retry equality must preserve these exact integer values across both independently running services. Wrong JSON types and invalid lexical query forms retain their existing error rules.

## Independent arithmetic check and current cause

Command executed with official workspace Python:

```sh
../../.venv/bin/python -B - <<'PY'
import json,sys
value=10**4300+1
lexical='1'+'0'*4299+'1'
print(json.dumps({'python_version':sys.version.split()[0],
 'default_decimal_conversion_limit':sys.get_int_max_str_digits(),
 'lexical_digit_count':len(lexical),'integer_bit_length':value.bit_length(),
 'grid_offsets_in_5hour_window':list(range(0,300,value)),
 'ninety_minute_duration_fits_5hour_window':90<=300,
 'huge_duration_fits_5hour_window':value<=300,
 'huge_cutoff_refuses_ordinary_future_distance':1000000<=value,
 'huge_positive_party_has_no_capacity2_option':value>2}))
PY
```

Observed official Python 3.12.14, default decimal conversion limit 4300, lexical length 4301, integer bit length 14285, opening-window offsets `[0]`, duration does not fit, cutoff refuses the ordinary distance, and party exceeds capacity 2. This is a bounded arithmetic diagnostic, not service acceptance or a repeated HTTP observation. No conversion of the giant integer to text was needed to check these semantics.

The accepted adapter uses standard json.loads/json.dumps and reports parsing ValueError as malformed_request. Both stage cores convert the validated plain-digit party string using int. The runtime decimal conversion ceiling can therefore cause the reported refusals despite valid lexical syntax and otherwise supported integer arithmetic. Fix scope must cover inbound/outbound JSON and core query conversion together; handling only fixture arithmetic would leave this boundary incomplete.

Only this Systems evidence document was added. Neither frozen Stage 1 nor current Stage 2 production files were edited. The coordinator must sequence any explicit frozen-source repair and new exact-revision reviews after the independent supplemental verdict; prior frozen manifests, failures, provisional verdicts and receipt/timestamp decisions remain preserved. No stage promotion is claimed. Harness Codex; configured gpt-6.1-sol; actual override/effort/usage/spend unknown.
