"""Own packaged-image parser/numeric/copy controls, distinct from HTTP."""
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
args = parser.parse_args()
repo = Path.cwd().resolve()
out = Path(args.out).resolve()
out.relative_to(repo / "evidence/systems-engineer")
out.mkdir(exist_ok=False)
prefix = "systems-engineer-parser-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f").lower()
record = {"candidate": args.candidate, "image_id": args.image, "commands": [], "runs": [], "cleanup": [], "scope": "codec diagnostics only, not HTTP"}
started = time.monotonic()


def run(argv, body=None, required=True):
    begin = time.monotonic()
    result = subprocess.run(argv, input=body, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    log = out / ("command-%03d.log" % len(record["commands"]))
    log.write_bytes(result.stdout)
    record["commands"].append({"argv": argv, "returncode": result.returncode, "seconds": time.monotonic() - begin,
                               "log": str(log), "stdin_sha256": None if body is None else hashlib.sha256(body).hexdigest()})
    if required and result.returncode:
        raise RuntimeError("Own command failed: " + str(log))
    return result


try:
    expected = hashlib.sha256(run(["git", "show", args.candidate + ":stage-1/json_codec.py"]).stdout).hexdigest()
    for label, filename in (("grammar", "stage-1-iterative-parser-probes.py"), ("numeric", "stage-1-json-codec-probes.py"), ("copy", "stage-1-json-depth-probes.py")):
        created = False
        name = prefix + "-" + label
        program = run(["git", "show", args.candidate + ":evidence/systems-engineer/" + filename]).stdout
        (out / ("executed-" + filename)).write_bytes(program)
        try:
            run(["docker", "create", "-i", "--name", name, "--network", "none", "--cpus", "2", "--memory", "2g", "--entrypoint", "python", args.image,
                 "-X", "faulthandler", "-B", "-", "--module", "/app/json_codec.py", "--out", "/tmp/systems-engineer-parser"])
            created = True
            inspect = json.loads(run(["docker", "inspect", name]).stdout)[0]
            assert inspect["Image"] == args.image and inspect["Mounts"] == []
            assert inspect["HostConfig"]["NanoCpus"] == 2000000000 and inspect["HostConfig"]["Memory"] == 2147483648
            assert inspect["HostConfig"]["NetworkMode"] == "none"
            result = run(["docker", "start", "-a", "-i", name], program, required=False)
            state = json.loads(run(["docker", "inspect", name]).stdout)[0]["State"]
            run(["docker", "cp", name + ":/tmp/systems-engineer-parser", str(out / label)])
            summary = json.loads((out / label / "summary.json").read_text())
            assert summary["module_sha256"] == expected
            record["runs"].append({"label": label, "summary": summary, "exit_code": result.returncode,
                                   "oom_killed": state["OOMKilled"], "process_exit_code": state["ExitCode"],
                                   "cpu": 2, "memory_bytes": 2147483648, "mounts": [], "network": "none"})
        finally:
            if created:
                result = run(["docker", "rm", "-f", name], required=False)
                record["cleanup"].append({"name": name, "returncode": result.returncode})
except Exception as error:
    record["runner_exception"] = {"type": type(error).__name__, "message": str(error)}
finally:
    record["wall_seconds"] = time.monotonic() - started
    record["passed"] = not record.get("runner_exception") and len(record["runs"]) == 3 and all(r["exit_code"] == 0 and r["summary"]["failed"] == 0 for r in record["runs"])
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"passed": record["passed"], "runner_exception": record.get("runner_exception"), "wall_seconds": record["wall_seconds"],
                      "summaries": {r["label"]: r["summary"] for r in record["runs"]}}))
    raise SystemExit(not record["passed"])
