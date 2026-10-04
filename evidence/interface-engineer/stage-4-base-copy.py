"""Authorized predecessor copy only; no service or verification preparation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "91e2c471acded1b861b3fec725f202297b1c6740"
SOURCE_TREE = "a0f0a4741bb0ab0125856510a000ade385344a04"
FROZEN = [(1, "75005d57fe0904753eac4eab5bf4e4c9a78b6d1b", 6),
          (2, "4dba10246b07b2dda19de260d529f9d94ba0a1ed", 9),
          (3, SOURCE, 9)]
OWNED = ["server.py", "Dockerfile", ".dockerignore", "RUN.md",
         "web/index.html", "web/app.js", "web/app.css"]
OUT = ROOT / "evidence/interface-engineer/stage-4-base-copy.json"
HANDOFF = ROOT / "evidence/interface-engineer/stage-4-base-copy-handoff.md"
COMMANDS = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    argv = ["git", *args]
    start = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True)
    COMMANDS.append({"argv": argv, "returncode": result.returncode,
                     "elapsed_seconds": time.monotonic() - start})
    result.check_returncode()
    return result.stdout


def entries(revision, folder):
    rows = []
    for line in git("ls-tree", "-r", revision, "--", folder).decode().splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, oid = meta.split()
        assert kind == "blob" and mode in {"100644", "100755"}, (path, mode)
        data = git("show", f"{revision}:{path}")
        working = ROOT / path
        assert working.is_file() and not working.is_symlink(), path
        assert working.read_bytes() == data, path
        assert bool(working.stat().st_mode & stat.S_IXUSR) == (mode == "100755"), path
        rows.append({"path": path, "mode": mode, "object_id": oid,
                     "sha256": sha(data), "bytes": len(data),
                     "working_mode": oct(stat.S_IMODE(working.stat().st_mode))})
    return rows


def main():
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    assert not OUT.exists() and not HANDOFF.exists(), "Preserve existing evidence"
    manifest_path = ROOT / "evidence/coordinator/accepted/stage-3.json"
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["candidate_full_revision"] == SOURCE
    assert git("rev-parse", f"{SOURCE}:stage-3").decode().strip() == SOURCE_TREE
    assert sha((ROOT / manifest["independent_verdict_path"]).read_bytes()) == manifest["independent_verdict_sha256"]
    before = {str(n): entries(rev, f"stage-{n}") for n, rev, _ in FROZEN}
    for n, _, count in FROZEN:
        assert len(before[str(n)]) == count
    frozen = {row["path"]: row for row in manifest["tree"]}
    for row in before["3"]:
        name = row["path"].removeprefix("stage-3/")
        assert row["mode"] == frozen[name]["mode"]
        assert row["object_id"] == frozen[name]["object_id"]
    assert set(OWNED) == set(frozen) - {"core.py", "json_codec.py"}
    copies = []
    for name in OWNED:
        source = ROOT / "stage-3" / name
        target = ROOT / "stage-4" / name
        assert not target.exists() and not target.is_symlink(), target
        data = source.read_bytes()
        mode = stat.S_IMODE(source.stat().st_mode)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(mode)
        assert target.read_bytes() == data
        assert stat.S_IMODE(target.stat().st_mode) == mode
        blob = git("hash-object", str(target.relative_to(ROOT))).decode().strip()
        assert blob == frozen[name]["object_id"]
        copies.append({"source": "stage-3/" + name, "target": "stage-4/" + name,
                       "source_blob": blob, "target_blob": blob,
                       "git_mode": frozen[name]["mode"], "working_mode": oct(mode),
                       "sha256": sha(data), "bytes": len(data),
                       "byte_identical": True, "mode_identical": True, "blob_identical": True})
    for n, rev, _ in FROZEN:
        assert entries(rev, f"stage-{n}") == before[str(n)]
    elapsed = time.monotonic() - start
    completed = datetime.now(timezone.utc).isoformat()
    proof = {"package": "TK-20261004-S4-interface-engineer-INITIAL-1",
             "parts_received": list(range(1, 20)), "part_count": 19,
             "both_final_end_markers_received": True,
             "final_inbound_id": "4d1466a9-fdad-45f6-8356-c8167b25a67f",
             "acknowledgement": "jam_reply_to_message staged before work; reciprocal message id not exposed",
             "shared_card": 23, "phase": "A: exact copy only; PhaseB held",
             "accepted_source_revision": SOURCE, "accepted_source_tree": SOURCE_TREE,
             "independent_verdict_seal": "315631a0565cbc671ba112842b452eb0b8624313",
             "freeze_manifest_path": str(manifest_path.relative_to(ROOT)),
             "freeze_manifest_sha256": sha(manifest_path.read_bytes()),
             "independent_verdict_path": manifest["independent_verdict_path"],
             "independent_verdict_sha256": manifest["independent_verdict_sha256"],
             "room_plan_sha256": sha((ROOT / "plan.md").read_bytes()),
             "script_sha256": sha(Path(__file__).read_bytes()),
             "started_utc": started, "completed_utc": completed, "elapsed_seconds": elapsed,
             "executed_command": "../../.venv/bin/python -B evidence/interface-engineer/stage-4-base-copy.py",
             "git_commands": COMMANDS, "copies": copies, "immutable_source_files": before,
             "immutable_sources_unchanged": True, "immutable_source_count": 24,
             "own_copy_count": 7, "tests_runtime_or_verification_preparation_executed": False,
             "highest_consecutive_accepted": 3, "stage4_acceptance": "not accepted",
             "model": {"harness": "Codex", "configured": "gpt-6.1-sol",
                       "actual_override_effort_tokens_catalog_estimate_billed_spend": "unknown"},
             "risks": ["Copy alone establishes no Stage4 runtime behavior",
                       "Extension requires complete nine-file proof and explicit PhaseB release",
                       "All four adopted interpretations and truthful compatibility bootstrap remain applicable"]}
    OUT.write_text(json.dumps(proof, indent=2) + "\n")
    table = "\n".join(f"| {r['target']} | {r['sha256']} | {r['git_mode']} |" for r in copies)
    HANDOFF.write_text(f"""# Stage 4 Interface predecessor copy

All nineteen parts and both final END markers of TK-20261004-S4-interface-engineer-INITIAL-1 were acknowledged before work. Shared card 23 is in progress with exactly one textual Components line. This report completes authorized Phase A only. Highest independently accepted consecutive stage is 3; Stage 4 is not accepted.

Accepted source: `{SOURCE}`, Stage 3 tree `{SOURCE_TREE}`. Independent accepted verdict seal: `315631a0565cbc671ba112842b452eb0b8624313`. The coordinator freeze manifest and actual verdict bytes are bound in `stage-4-base-copy.json`. The resulting full own commit is reported after exact changed-path inspection; this document avoids a circular self-commit identifier.

| Copied target | Identical source/target SHA-256 | Git mode |
| --- | --- | --- |
{table}

The script checks all nine accepted Stage 3 working files against immutable named blobs/modes and the frozen manifest, then copies all seven Interface files from those proven working bytes without normalization. All seven targets match bytes, permission modes and Git blob identities. All 24 accepted Stage 1–3 files remain unchanged before/after. Systems owns the remaining two target files; coordinator proof of the complete nine-file copy is still required.

Executed from the absolute result repository:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-4-base-copy.py
```

Measured copy/check execution: {elapsed:.9f} seconds, a scoped duration. The proof saves actual Git argv/exits/timings, source/target hashes/blobs/modes, freeze/verdict hashes and preserved predecessor rows. Reproduction requires fresh target/evidence paths; the script refuses existing outputs or targets.

No extension, verification preparation, service, Docker build, HTTP/browser test or official harness was executed. Phase B remains held until the coordinator's whole predecessor proof and explicit release. Intermediate target state may be incomplete before the disjoint Systems copy. No Stage 4 behavior or independent acceptance is inferred.

Inputs are the complete cumulative assignment/specifications/guide/brief, four adopted decisions, room plan, frozen manifest and accepted own source. No peer/official probe or oracle implementation, external domain source, memory, abandoned result, host dependency or outside-workspace implementation was used. Exact value-based JSON/legacy profiles, immutable original receipts, semantic exact numeric controls, historical IANA instant/wall-field/minute-offset interpretation and genuine empty-history/revision-1/policy-0 bootstrap remain applicable. No history was rewritten. All commits use explicit owned paths and --only. Configured Codex/gpt-6.1-sol; actual model override, effort, usage and estimated/billed spend are unknown. Whole-factory timing and final public export/release/submission are coordinator/operator-owned.
""")
    event = {"timestamp_utc": completed, "event": "stage-4-interface-base-copy",
             "source_revision": SOURCE, "source_tree": SOURCE_TREE,
             "artifact": str(OUT.relative_to(ROOT)), "copied_files": 7,
             "byte_mode_blob_matches": 7, "immutable_source_files_unchanged": 24,
             "elapsed_seconds": elapsed, "runtime_or_tests_executed": False,
             "extension": "held pending complete predecessor proof and PhaseB release",
             "highest_consecutive_accepted": 3, "stage4_acceptance": "not accepted",
             "harness": "Codex", "configured_model": "gpt-6.1-sol",
             "actual_model_effort_usage_spend": "unknown"}
    with (ROOT / "evidence/interface-engineer/ledger.jsonl").open("a") as handle:
        handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    print(json.dumps({"copies": 7, "byte_mode_blob_matches": 7,
                      "immutable_source_files_unchanged": 24, "elapsed_seconds": elapsed,
                      "artifact": str(OUT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
