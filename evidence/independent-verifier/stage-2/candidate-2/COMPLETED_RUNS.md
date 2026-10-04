# Complete current-candidate protocol observations

Candidate `4dba10246b07b2dda19de260d529f9d94ba0a1ed`. Every row below is a complete fresh passing run, zero failed assertions. Exact executable commands and full-precision timing are in [completed-runs.json](completed-runs.json); each named directory retains actual observations. Initial failed or writer-stopped attempts are separately preserved in [RUNNER_ISSUES.md](RUNNER_ISSUES.md) and excluded here. Protocol seconds are distinct from whole driver or factory elapsed.

| Family | HTTP-only requests | Browser direct API operations | Browser-originated requests | Assertions | Protocol seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| http-01/original-minimal | 4 | — | — | 9 | 0.018515458 |
| http-01/calendar-minimal | 8 | — | — | 12 | 0.115221417 |
| http-01/race50 | 55 | — | — | 11 | 0.129082167 |
| http-01/decimal | 196 | — | — | 124 | 1.214231084 |
| http-01/semantic | 631 | — | — | 481 | 4.373067169 |
| http-01/opaque-ids | 374 | — | — | 308 | 1.137764626 |
| http-01/nesting | 516 | — | — | 484 | 2.761240335 |
| http-01/pairs | 949 | — | — | 2,459 | 6.983940795 |
| http-01/retained-amend | 5 | — | — | 2 | 0.111495167 |
| http-01/large-minutes | 39 | — | — | 26 | 0.202466917 |
| http-01/numeric | 30 | — | — | 27 | 0.116251042 |
| http-01/fractional | 38 | — | — | 35 | 0.076357584 |
| http-01/very-deep | 52 | — | — | 68 | 0.657595667 |
| http-01/deep-race | 246 | — | — | 38 | 12.466817006 |
| inherited-02/baseline | 1,485 | — | — | 1,497 | 7.704121796 |
| inherited-02/snapshot | 810 | — | — | 531 | 4.885018378 |
| inherited-02/decoder | 2,041 | — | — | 1,702 | 14.458446839 |
| inherited-02/legacy | 26 | — | — | 25 | 0.202716833 |
| origins-02/origins | 127 | — | — | 84 | 0.498262042 |
| reconstruction-http-01/deep | 360 | — | — | 216 | 5.446415169 |
| reconstruction-http-01/opaque | 80 | — | — | 48 | 0.453277833 |
| reconstruction-http-01/numeric | 24 | — | — | 18 | 0.302290709 |
| browser-01/general | — | 94 | 361 | 329 | 22.425975801 |
| browser-01/boundaries | — | 24 | 114 | 42 | 8.089584545 |
| browser-01/historical | — | 12 | 33 | 6 | 2.204395251 |
| browser-01/visual | — | 14 | 102 | 48 | 6.973340504 |
| reconstruction-browser-01/upgrade | — | 10 | 38 | 26 | 2.200765293 |
| reconstruction-browser-01/numeric | — | 51 | 546 | 420 | 53.054514607 |
| reconstruction-browser-01/opaque | — | 8 | 152 | 56 | 7.717275546 |
| upgrade-browser-01/four-upgrades | — | 52 | 76 | 84 | 7.437152586 |
| supplement-01/browser | — | 10 | 100 | 75 | 10.947053089 |
| supplement-oracle-02/oracle | 327 | — | — | 1,169 | 0.211197833 |
| coverage-closures-01/coverage | 32 | — | — | 24 | 0.164509625 |
| coverage-closures-01/overflow | — | 4 | 26 | 18 | 6.312536961 |
| calendar-browser-01/calendar | — | 15 | 55 | 30 | 3.135145835 |

HTTP-only totals: **24 runs, 8,455 requests, 9,398 assertions**. Browser totals: **11 runs, 294 direct API operations, 1,603 browser-originated requests, 1,134 assertions**. Four-origin upgrades separately record 24 actual forwardings that transport browser requests; these are not additional unique requests. All completed expectations pass. Official checker, startup/inspection, capture-invalidation and initial failed/writer-stopped observations are outside these totals.

The inherited fixture-ID suite additionally records 22 nonnormative admitted-fixture diagnostics. They are kept separate from the 308 conditional usability assertions and final normative matrix. Screenshots are real current observations, 156 files; no blank failed-run capture is counted as product evidence.
