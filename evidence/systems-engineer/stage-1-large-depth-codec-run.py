"""Run each deep operation in its own constrained, mount-free codec process."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--image", required=True)
parser.add_argument("--candidate", required=True)
parser.add_argument("--out", required=True)
parser.add_argument("--depths", type=int, nargs="+", default=[10000, 20000])
parser.add_argument("--shapes", choices=["array", "object"], nargs="+", default=["array", "object"])
parser.add_argument("--operations", choices=["decoder", "validation", "equality", "encoder", "copy", "roundtrip"], nargs="+",
                    default=["decoder", "validation", "equality", "encoder", "copy", "roundtrip"])
args = parser.parse_args()
repo = Path.cwd().resolve()
out = Path(args.out).resolve()
out.relative_to(repo / "evidence/systems-engineer")
out.mkdir(exist_ok=False)
program = (repo / "evidence/systems-engineer/stage-1-large-depth-codec-probe.py").read_bytes()
(out / "executed-probe.py").write_bytes(program)
prefix = "systems-engineer-depth-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f").lower()
record = {"candidate": args.candidate, "image_id": args.image, "probe_sha256": hashlib.sha256(program).hexdigest(),
          "commands": [], "runs": [], "cleanup": [], "scope": "isolated codec operations; no HTTP claim"}
started = time.monotonic()


def run(argv, body=None, required=True, timeout=60):
    begin = time.monotonic()
    try:
        result = subprocess.run(argv, input=body, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        code, raw = result.returncode, result.stdout
    except subprocess.TimeoutExpired as error:
        code, raw = 124, error.stdout or b""
    log = out / ("command-%03d.log" % len(record["commands"]))
    log.write_bytes(raw)
    record["commands"].append({"argv": argv, "returncode": code, "seconds": time.monotonic() - begin,
                                "log": str(log), "stdin_sha256": None if body is None else hashlib.sha256(body).hexdigest()})
    if required and code:
        raise RuntimeError("Own runner command failed: " + str(log))
    return code, raw


expected = hashlib.sha256(run(["git", "show", args.candidate + ":stage-1/json_codec.py"])[1]).hexdigest()
try:
    for depth in args.depths:
        for shape in args.shapes:
            for operation in args.operations:
                name = prefix + "-" + str(len(record["runs"]))
                created = False
                entry = {"depth": depth, "shape": shape, "operation": operation, "name": name}
                try:
                    run(["docker", "create", "-i", "--name", name, "--network", "none", "--cpus", "2", "--memory", "2g",
                         "--entrypoint", "python", args.image, "-X", "faulthandler", "-B", "-", str(depth), shape, operation])
                    created = True
                    inspect = json.loads(run(["docker", "inspect", name])[1])[0]
                    assert inspect["Image"] == args.image and inspect["Mounts"] == []
                    assert inspect["HostConfig"]["NanoCpus"] == 2_000_000_000
                    assert inspect["HostConfig"]["Memory"] == 2_147_483_648
                    assert inspect["HostConfig"]["NetworkMode"] == "none"
                    entry["resource"] = {"cpu": 2, "memory_bytes": 2147483648, "network": "none", "mounts": []}
                    code, raw = run(["docker", "start", "-a", "-i", name], program, required=False)
                    state = json.loads(run(["docker", "inspect", name])[1])[0]["State"]
                    entry["cli_exit_code"], entry["process_exit_code"], entry["oom_killed"] = code, state["ExitCode"], state["OOMKilled"]
                    output = out / ("%s-%d-%s.log" % (shape, depth, operation))
                    output.write_bytes(raw)
                    decoded = []
                    for line in raw.decode(errors="replace").splitlines():
                        try: decoded.append(json.loads(line))
                        except ValueError: pass
                    entry["emitted_results"] = decoded
                    for item in decoded:
                        if "starting" in item:
                            assert item["starting"]["codec_sha256"] == expected
                    result = next((d["result"] for d in decoded if "result" in d), None)
                    entry["passed"] = bool(result is not None and result["failed"] == 0 and state["ExitCode"] == 0 and code == 0)
                    if result is None:
                        entry["classification"] = "runner timeout" if code == 124 else "isolated process failure/no final diagnostic result"
                except Exception as error:
                    entry["passed"] = False
                    entry["runner_exception"] = {"type": type(error).__name__, "message": str(error)}
                finally:
                    if created:
                        code, _ = run(["docker", "rm", "-f", name], required=False)
                        record["cleanup"].append({"name": name, "returncode": code})
                    record["runs"].append(entry)
                    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
finally:
    record["wall_seconds"] = time.monotonic() - started
    record["summary"] = {"processes": len(record["runs"]), "passed": sum(r["passed"] for r in record["runs"]),
                         "failed": sum(not r["passed"] for r in record["runs"])}
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"summary": record["summary"], "wall_seconds": record["wall_seconds"],
                      "failed_runs": [{k:r.get(k) for k in ("shape", "depth", "operation", "process_exit_code", "classification", "runner_exception")} for r in record["runs"] if not r["passed"]]}))
    raise SystemExit(bool(record["summary"]["failed"]))
