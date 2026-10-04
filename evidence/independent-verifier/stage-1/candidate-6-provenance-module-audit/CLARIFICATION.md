# Named tree versus shared-index parent delta

Interface notice `56a18863-6f39-438f-a825-96eae1b24196` is independently checked
against exact Git history. Its service-tree distinction is correct; its claim
that the module entered the shared-index commit is not supported by the parent
delta. Original verifier provenance at b9174e1e7f8661dab6147bd662af540197cc12b4
and every earlier report remain unchanged.

Capturing commit **182582c41d21a23d8ccd95688fa7f1afa0437460** has parent
**c2fcedc853e0fe33e96f9d3f39c0c807b4e08d9f**, authored by Systems Engineer.
The parent's and capturing commit's complete Stage1 tree are both
`e358e87edb0958d52d061eaf4a699eccc9d3520a`. The capturing commit changes
exactly **33 paths: 32 verifier evidence paths and one Interface probe path**.
It changes **zero production paths** against its parent.

The original wiring commit **3dae12788ff59dce8c4ce8a6faa71394f140e3d2** has
a different codec blob. Its difference from the complete182 tree is solely
`stage-1/json_codec.py`. That difference was already committed in the parent
Systems traversal repair; it was not captured from the shared index by182.

| Named context | Codec Git blob | Codec SHA256 |
| --- | --- | --- |
| Wiring3dae127 | af35650538308791bafa87712060b14cdb0d47b9 | 913800d80172392e6357b4a9c6d2b5a80d47859779e4b0c7024b5e6e61a71078 |
| Systems repairc2fced / parent / capturing182 | c436803faa3e75fea7637513df76115ae20cdd48 | 771cd5c2ccd4e11bb74808998de65605845576d0bc6172fb2d428421bc83895c |

Thus a runtime bound to full182 must name the inherited repaired codec, while a
runtime bound to original3dae127 must name its original module. Neither is a
complete repaired candidate merely because a clone builds or a builder runs
diagnostics. Production release/sequence remains coordinator-owned. No source
edit, rollback, attribution rewrite or candidate execution follows this audit.

The earlier verifier `all_capturing_commit_paths` list already contains all33
actual changed paths. Its verifier source-byte matches and actual authorship
disclosure remain valid: verifier authored those32 evidence contents; Git author
for that capture is Interface. The codec remains attributable to the separate
Systems repair commit. This clarification preserves both distinctions.

Executable read-only command from the result root:

```sh
../../.venv/bin/python -B evidence/independent-verifier/stage-1/audit_shared_index.py --out evidence/independent-verifier/stage-1/candidate-6-provenance-module-audit/metadata-01
```

Use a new unique owned output directory to repeat. `metadata-01/proof.json`
records exact tree/blob identities, path lists and metadata; `commands.json`
records every read-only Git argv. Module bytes are hashed without importing or
executing them; no builder probe/oracle is read. No HTTP, official check, build,
container or network is executed. Current coverage and highest accepted stage0
are unchanged. Complete named candidate/both builder handoffs remain required.
Configuredgpt-6.1-sol; actual override/effort/usage/spend unknown.
