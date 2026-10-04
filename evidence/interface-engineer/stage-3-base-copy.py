"""Exact seven-file predecessor copy only; no service/test execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REVISION = "4dba10246b07b2dda19de260d529f9d94ba0a1ed"
SOURCE_TREE = "422380c814043021c2df2daad8edbbb34d5b5887"
STAGE1_REVISION = "75005d57fe0904753eac4eab5bf4e4c9a78b6d1b"
OWNED = ["server.py", "Dockerfile", ".dockerignore", "RUN.md",
         "web/index.html", "web/app.js", "web/app.css"]
OUT = ROOT / "evidence/interface-engineer/stage-3-base-copy.json"
HANDOFF = ROOT / "evidence/interface-engineer/stage-3-base-copy-handoff.md"
LEDGER = ROOT / "evidence/interface-engineer/ledger.jsonl"
COMMANDS = []


def git(*args):
    argv = ["git", *args]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, check=True)
    COMMANDS.append({"argv": argv, "returncode": result.returncode})
    return result.stdout


def sha(data):
    return hashlib.sha256(data).hexdigest()


def entries(revision, folder):
    rows = []
    for line in git("ls-tree", "-r", revision, folder).decode().splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, oid = meta.split()
        assert kind == "blob" and mode in {"100644", "100755"}, (path, mode)
        data = git("show", f"{revision}:{path}")
        working = ROOT / path
        assert not working.is_symlink() and working.is_file(), path
        assert working.read_bytes() == data, path
        executable = bool(working.stat().st_mode & stat.S_IXUSR)
        assert executable == (mode == "100755"), path
        rows.append({"path": path, "mode": mode, "object_id": oid,
                     "sha256": sha(data), "bytes": len(data),
                     "working_mode": oct(stat.S_IMODE(working.stat().st_mode))})
    return rows


def main():
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    assert not OUT.exists() and not HANDOFF.exists(), "Preserve existing outputs"
    manifest_path = ROOT / "evidence/coordinator/accepted/stage-2.json"
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["candidate_full_revision"] == SOURCE_REVISION
    assert git("rev-parse", f"{SOURCE_REVISION}:stage-2").decode().strip() == SOURCE_TREE
    verdict_path = ROOT / manifest["independent_verdict_path"]
    assert sha(verdict_path.read_bytes()) == manifest["independent_verdict_sha256"]
    before2 = entries(SOURCE_REVISION, "stage-2")
    before1 = entries(STAGE1_REVISION, "stage-1")
    assert len(before2) == 9 and len(before1) == 6
    frozen = {x["path"]: x for x in manifest["tree"]}
    for row in before2:
        source_name = row["path"].removeprefix("stage-2/")
        saved = frozen[source_name]
        assert row["mode"] == saved["mode"] and row["object_id"] == saved["object_id"]
    copies = []
    for name in OWNED:
        source = ROOT / "stage-2" / name
        target = ROOT / "stage-3" / name
        assert not target.exists() and not target.is_symlink(), target
        data = source.read_bytes()
        source_mode = stat.S_IMODE(source.stat().st_mode)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(source_mode)
        assert target.read_bytes() == data
        assert stat.S_IMODE(target.stat().st_mode) == source_mode
        source_row = next(x for x in before2 if x["path"] == "stage-2/" + name)
        copies.append({"source": "stage-2/" + name, "target": "stage-3/" + name,
                       "source_blob": source_row["object_id"],
                       "git_mode": source_row["mode"], "working_mode": oct(source_mode),
                       "sha256": sha(data), "bytes": len(data),
                       "byte_identical": True, "mode_identical": True})
    assert entries(SOURCE_REVISION, "stage-2") == before2
    assert entries(STAGE1_REVISION, "stage-1") == before1
    elapsed = time.monotonic() - start
    proof = {
        "package": "TK-20261004-S3-interface-engineer-INITIAL-1",
        "parts_received": list(range(1, 14)), "part_count": 13,
        "complete_content_and_package_end_received": True,
        "final_inbound_id": "8826cba8-ff9f-4a13-a5b6-00276e3dc771",
        "acknowledgement": "jam_reply_to_message staged before any work; reciprocal message id not exposed",
        "shared_card": 20, "phase": "base copy only; extension held",
        "accepted_source_revision": SOURCE_REVISION, "accepted_source_tree": SOURCE_TREE,
        "coordinator_freeze_revision": "a7ef75573233fbf4652b56d6609e14d82d21594c",
        "freeze_manifest_path": str(manifest_path.relative_to(ROOT)),
        "freeze_manifest_sha256": sha(manifest_path.read_bytes()),
        "independent_verdict_path": manifest["independent_verdict_path"],
        "independent_verdict_sha256": manifest["independent_verdict_sha256"],
        "room_plan_sha256": sha((ROOT / "plan.md").read_bytes()),
        "script_sha256": sha(Path(__file__).read_bytes()),
        "started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed,
        "executed_command": "../../.venv/bin/python -B evidence/interface-engineer/stage-3-base-copy.py",
        "git_commands": COMMANDS, "copies": copies,
        "all_nine_stage2_source_files": before2,
        "all_six_stage1_source_files": before1,
        "stage1_and_stage2_unchanged": True,
        "own_copy_count": len(copies), "tests_or_runtime_executed": False,
        "highest_consecutive_accepted": 2, "stage3_acceptance": "not accepted",
        "model": {"harness": "Codex", "configured": "gpt-6.1-sol",
                  "actual_override_effort_tokens_catalog_estimate_billed_spend": "unknown"},
        "risks": ["Unpromoted base copy; no Stage3 behavior established",
                  "Extensions require coordinator complete nine-file proof and explicit release",
                  "All four adopted timestamp/receipt/numeric/control interpretations remain applicable"]}
    OUT.write_text(json.dumps(proof, indent=2) + "\n")
    table = "\n".join(f"| {r['target']} | {r['sha256']} | {r['git_mode']} |" for r in copies)
    HANDOFF.write_text(f"""# Stage 3 Interface predecessor base copy

Complete thirteen-part TK-20261004-S3-interface-engineer-INITIAL-1 plus both END markers was acknowledged before work. Shared card 20 covers the full assignment. This entry executes only the authorized base copy. Highest consecutive independently accepted stage is 2; Stage 3 is not accepted.

Accepted source full revision: `{SOURCE_REVISION}`, Stage 2 tree `{SOURCE_TREE}`. Coordinator freeze: `a7ef75573233fbf4652b56d6609e14d82d21594c`. Immutable Stage 1 full revision remains `{STAGE1_REVISION}`. The resulting own full base-copy revision is reported after commit and exact own changed-path inspection, avoiding a circular self-commit identifier.

| Copied target | SHA-256 of identical source/target bytes | Git mode |
| --- | --- | --- |
{table}

The executable copy script first compares every accepted Stage 2 working file with the immutable named Git blob and frozen manifest. It writes only the seven owned targets from those proven working bytes and preserves permission modes. Seven of seven target copies compare byte-for-byte and mode-for-mode. All nine accepted Stage 2 and six Stage 1 files compare unchanged after the copy. Systems owns the other two target files and the coordinator proves the complete predecessor copy separately.

Executed from the result repository:

```sh
../../.venv/bin/python -B evidence/interface-engineer/stage-3-base-copy.py
```

Measured copy/check time: {elapsed:.9f} seconds; this is scoped execution, not whole factory elapsed. Manifest `stage-3-base-copy.json` saves actual Git argv, blob identities, hashes, counts, timestamps, modes and source preservation. Reproduction requires a fresh Stage 3 target and fresh evidence names; existing outputs are refused and must not be deleted or overwritten.

No service, Docker build, browser/API test, official harness or verification preparation was executed. No source extension is authorized until the coordinator records all nine inherited files identical and explicitly releases the existing implementation phase. Intermediate target state may be incomplete until the disjoint Systems copy lands. This copy establishes no Stage 3 runtime behavior or acceptance.

Authoring inputs are the complete cumulative assignment/specifications/brief and adopted decisions, authoritative room plan, participant guide, frozen manifest and accepted source bytes. No peer probe/oracle, official test implementation, external domain source, memory, abandoned result, outside-workspace implementation or host dependency was read/copied/executed. Every commit uses explicit owned paths and --only; all previous source, outputs and history remain preserved. Timestamp minute-offset interpretation, immutable original receipts, exact numeric/legacy profiles and semantic numeric controls remain disclosed. Codex/configured gpt-6.1-sol; actual model override, effort, token usage, catalog estimate and billed spend unknown.
""")
    event = {"timestamp_utc": proof["completed_utc"], "event": "stage-3-interface-base-copy",
             "source_revision": SOURCE_REVISION, "source_tree": SOURCE_TREE,
             "artifact": str(OUT.relative_to(ROOT)), "copied_files": 7,
             "byte_and_mode_matches": 7, "immutable_source_files_unchanged": 15,
             "elapsed_seconds": elapsed, "runtime_or_tests_executed": False,
             "extension": "held pending full predecessor proof/release",
             "highest_consecutive_accepted": 2, "stage3_acceptance": "not accepted",
             "harness": "Codex", "configured_model": "gpt-6.1-sol",
             "actual_model_effort_usage_spend": "unknown"}
    with LEDGER.open("a") as handle:
        handle.write(json.dumps(event, separators=(",", ":")) + "\n")
    print(json.dumps({"copied": 7, "byte_mode_matches": 7, "sources_unchanged": 15,
                      "elapsed_seconds": elapsed, "artifact": str(OUT.relative_to(ROOT))}))


if __name__ == "__main__":
    main()
