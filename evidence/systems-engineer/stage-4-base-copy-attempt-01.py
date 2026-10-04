"""Phase A only: exact frozen predecessor copy and explicit owned commit."""
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import time
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[2]
SOURCE = "91e2c471acded1b861b3fec725f202297b1c6740"
EXPECTED = {
    1: "75005d57fe0904753eac4eab5bf4e4c9a78b6d1b",
    2: "4dba10246b07b2dda19de260d529f9d94ba0a1ed",
    3: SOURCE,
}
OWNED = ["stage-4/core.py", "stage-4/json_codec.py"]
OUT = ROOT / "evidence/systems-engineer/stage-4-source-copy.json"
COMMANDS = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(argv):
    for attempt in range(6):
        started = time.perf_counter()
        result = subprocess.run(argv, cwd=ROOT, capture_output=True)
        COMMANDS.append({"argv": argv, "exit": result.returncode,
                         "seconds": time.perf_counter() - started,
                         "stdout": result.stdout.decode("utf-8", "replace"),
                         "stderr": result.stderr.decode("utf-8", "replace")})
        if result.returncode == 0:
            return result.stdout
        if b"index.lock" not in result.stderr or attempt == 5:
            raise RuntimeError(COMMANDS[-1])
        time.sleep(2)


def frozen():
    result = {}
    for stage, revision in EXPECTED.items():
        manifest_path = ROOT / f"evidence/coordinator/accepted/stage-{stage}.json"
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw)
        assert manifest["candidate_full_revision"] == revision
        files = []
        entries = run(["git", "ls-tree", "-r", revision, "--", f"stage-{stage}"]).decode().splitlines()
        actual = {}
        for entry in entries:
            prefix, path = entry.split("\t")
            mode, kind, blob = prefix.split()
            assert kind == "blob" and mode in ("100644", "100755")
            actual[path] = (mode, blob)
        expected = {f"stage-{stage}/{item['path']}": (item["mode"], item["object_id"])
                    for item in manifest["tree"]}
        assert actual == expected
        for path, (mode, blob) in actual.items():
            data = run(["git", "cat-file", "blob", blob])
            working = ROOT / path
            assert not working.is_symlink() and working.is_file()
            assert working.read_bytes() == data
            fs_mode = stat.S_IMODE(working.stat().st_mode)
            assert fs_mode == (0o755 if mode == "100755" else 0o644)
            files.append({"path": path, "git_mode": mode, "filesystem_mode": oct(fs_mode),
                          "blob": blob, "sha256": sha(data), "bytes": len(data),
                          "working_equals_accepted_blob": True})
        result[str(stage)] = {"revision": revision, "manifest_path": str(manifest_path.relative_to(ROOT)),
                              "manifest_sha256": sha(raw), "files": files}
        if stage == 3:
            verdict = (ROOT / manifest["independent_verdict_path"]).read_bytes()
            assert sha(verdict) == manifest["independent_verdict_sha256"]
            result[str(stage)]["independent_verdict_sha256"] = sha(verdict)
    return result


def main():
    assert not OUT.exists(), "Never replace a preserved copy observation"
    started = time.perf_counter()
    start_utc = datetime.now(timezone.utc).isoformat()
    before = frozen()
    copies = []
    for path in OWNED:
        source_path = path.replace("stage-4/", "stage-3/", 1)
        source = ROOT / source_path
        destination = ROOT / path
        assert not destination.exists() and not destination.is_symlink()
        data = source.read_bytes()
        mode = stat.S_IMODE(source.stat().st_mode)
        destination.parent.mkdir(exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(data)
        destination.chmod(mode)
        assert destination.read_bytes() == data
        assert stat.S_IMODE(destination.stat().st_mode) == mode
        blob = run(["git", "hash-object", path]).decode().strip()
        accepted = next(item for item in before["3"]["files"] if item["path"] == source_path)
        assert blob == accepted["blob"]
        copies.append({"source": source_path, "target": path, "sha256": sha(data),
                       "bytes": len(data), "filesystem_mode": oct(mode),
                       "git_mode": accepted["git_mode"], "source_blob": blob,
                       "byte_mode_blob_equal": True, "target_absent_before_copy": True})
    assert frozen() == before
    run(["git", "add", "--", *OWNED])
    committed = run(["git", "-c", "user.name=Systems Engineer", "-c",
                     "user.email=systems-engineer@nightwatch-foundry.invalid", "commit", "--only",
                     "-m", "Copy frozen Stage 3 Systems modules into Stage 4", "--", *OWNED]).decode()
    match = re.search(r"\[[^\]\n]+ ([0-9a-f]{7,40})\]", committed)
    assert match, committed
    revision = run(["git", "rev-parse", match.group(1)]).decode().strip()
    changed = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", revision]).decode().splitlines()
    assert set(changed) == set(OWNED), changed
    for copy in copies:
        entry = run(["git", "ls-tree", revision, "--", copy["target"]]).decode().strip()
        prefix, path = entry.split("\t")
        mode, kind, blob = prefix.split()
        assert path == copy["target"] and kind == "blob"
        assert mode == copy["git_mode"] and blob == copy["source_blob"]
        copy["target_committed_blob"] = blob
    after = frozen()
    assert before == after
    report = {"package": "TK-20261004-S4-systems-engineer-INITIAL-1",
              "parts_received": list(range(1, 20)), "end_received": True,
              "completeness_acknowledged_before_work": True,
              "final_part_receipt_message_id": "1a48adc4-a904-4e14-b407-79c37d8e412e",
              "reciprocal_completeness_acknowledgement_message_id": "unknown",
              "scope": "Phase A Systems exact two-file copy only; Phase B held",
              "base_copy_revision": revision, "changed_files": changed,
              "highest_consecutive_accepted_stage": 3, "stage4_accepted": False,
              "frozen_predecessors_before_and_after": before,
              "copies": copies, "source_script_sha256": sha(Path(__file__).read_bytes()),
              "invocation": [str(ROOT.parent.parent / ".venv/bin/python"), "-B", str(Path(__file__).resolve())],
              "start_utc": start_utc, "end_utc": datetime.now(timezone.utc).isoformat(),
              "seconds": time.perf_counter() - started, "commands": COMMANDS,
              "runtime_builds_or_probes": 0, "frozen_files_verified": sum(len(x["files"]) for x in before.values()),
              "harness": "Codex", "configured_model": "gpt-6.1-sol",
              "actual_model_override": "unknown", "effort": "unknown", "tokens": "unknown",
              "catalog_estimated_cost": "unknown", "billed_spend": "unknown"}
    with OUT.open("x") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"base_copy_revision": revision, "copies": len(copies),
                      "frozen_files_verified": report["frozen_files_verified"], "seconds": report["seconds"]}))


if __name__ == "__main__":
    main()
