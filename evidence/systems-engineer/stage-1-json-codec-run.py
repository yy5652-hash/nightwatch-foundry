"""Build and run the committed standalone codec diagnostics, never the service."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("--revision", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
repo = Path.cwd().resolve()
workspace = repo.parents[1]
out = Path(args.out).resolve()
out.relative_to(workspace)
out.mkdir(parents=True, exist_ok=False)
commands = []
started = time.monotonic()
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f").lower()
resource = "systems-engineer-codec-" + stamp
image = "systems-engineer-json-codec:" + stamp
context = Path(tempfile.mkdtemp(prefix="systems-engineer-codec-", dir=out))
created = False
successful = False
result = {"scope": "standalone codec diagnostic, not HTTP acceptance",
          "started_at": datetime.now(timezone.utc).isoformat(), "image_tag": image,
          "container_name": resource, "commands": commands}


def run(argv, *, timeout=60, required=True):
    index = len(commands)
    start = time.monotonic()
    process = subprocess.run(argv, cwd=repo, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=timeout)
    log = out / ("command-%02d.log" % index)
    log.write_bytes(process.stdout)
    commands.append({"argv": argv, "returncode": process.returncode,
                     "seconds": time.monotonic() - start, "log": str(log)})
    if required and process.returncode:
        raise RuntimeError("Command %s failed; see %s" % (index, log))
    return process.stdout


try:
    revision = run(["git", "rev-parse", args.revision + "^{commit}"]).decode().strip()
    result["revision"] = revision
    sources = {"stage-1/json_codec.py": "json_codec.py",
               "evidence/systems-engineer/stage-1-json-codec-probes.py": "probes.py"}
    result["source_sha256"] = {}
    for source, destination in sources.items():
        raw = run(["git", "show", revision + ":" + source])
        (context / destination).write_bytes(raw)
        result["source_sha256"][source] = hashlib.sha256(raw).hexdigest()
    dockerfile = ("FROM python:3.12-slim-bookworm\n"
                  "ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1\n"
                  "WORKDIR /probe\nCOPY json_codec.py probes.py ./\n"
                  "USER 65532:65532\n"
                  'CMD ["python","-B","probes.py","--module","json_codec.py",'
                  '"--out","/tmp/systems-engineer-codec-output"]\n')
    (context / "Dockerfile").write_text(dockerfile)
    (out / "diagnostic-Dockerfile").write_text(dockerfile)
    run(["docker", "build", "-t", image, str(context)], timeout=180)
    image_info = json.loads(run(["docker", "image", "inspect", image]))[0]
    result["image_id"] = image_info["Id"]
    (out / "image-inspect.json").write_text(json.dumps(image_info, indent=2) + "\n")
    run(["docker", "create", "--name", resource, "--network", "none", "--cpus", "2",
         "--memory", "2g", image])
    created = True
    inspect = json.loads(run(["docker", "inspect", resource]))[0]
    (out / "container-inspect.json").write_text(json.dumps(inspect, indent=2) + "\n")
    host = inspect["HostConfig"]
    result["resource_proof"] = {"network": host["NetworkMode"], "nano_cpus": host["NanoCpus"],
                                "memory_bytes": host["Memory"], "mounts": inspect["Mounts"],
                                "image_id": inspect["Image"], "user": inspect["Config"]["User"]}
    assert host["NetworkMode"] == "none" and host["NanoCpus"] == 2_000_000_000
    assert host["Memory"] == 2_147_483_648 and inspect["Mounts"] == []
    assert inspect["Image"] == image_info["Id"]
    run(["docker", "start", resource])
    wait_code = run(["docker", "wait", resource]).decode().strip()
    result["probe_exit_code"] = int(wait_code)
    run(["docker", "logs", resource])
    run(["docker", "cp", resource + ":/tmp/systems-engineer-codec-output", str(out / "probes")])
    for filename in ("json_codec.py", "probes.py"):
        destination = out / ("packaged-" + filename)
        run(["docker", "cp", resource + ":/probe/" + filename, str(destination)])
        assert destination.read_bytes() == (context / filename).read_bytes()
    result["summary"] = json.loads((out / "probes/summary.json").read_text())
    assert result["summary"]["module_sha256"] == result["source_sha256"]["stage-1/json_codec.py"]
    assert result["probe_exit_code"] == 0 and result["summary"]["failed"] == 0
    successful = True
finally:
    if created:
        run(["docker", "rm", "-f", resource], required=False)
        result["cleanup_exit_code"] = commands[-1]["returncode"]
    shutil.rmtree(context)
    result["temporary_context_removed"] = not context.exists()
    result["successful"] = successful
    result["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result.get(key) for key in (
        "revision", "image_id", "successful", "probe_exit_code", "summary", "resource_proof",
        "cleanup_exit_code", "temporary_context_removed", "wall_seconds")}))
