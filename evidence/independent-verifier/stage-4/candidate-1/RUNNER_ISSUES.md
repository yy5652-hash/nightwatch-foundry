# Preserved current verifier issues

The first source audit fails before HTTP execution because it compares every implementation-commit path with a production-only list. Those commits also contain owned evidence. Its exact source, partial output and failed assertion remain in `source-audit/`. The corrected complete run in `source-audit-02/` checks the production subset explicitly and retains the other paths. No original result is rewritten.

A read-only CSV inspection encounters Python's default 131072-character field limit. The full reader uses `csv.field_size_limit(sys.maxsize)` and retains all original CSV fields. This is a reader error, not a service defect or evidence suppression.

A shared-board status inspection invokes `work room-status` without the required task UID and status. The CLI exits2 with the actual usage error; it changes no card. The version-matched `work edit`/`work list` documentation supplies the prospective board operations. This error is preserved in room tool history.

The seven completed HTTP clients have no client exception. Their twelve failed assertions are actual service error-classification divergences, not runner corrections. The full rejected coverage retains unexecuted obligations and does not reclassify those failures or silently claim missing product/upgrade evidence.
