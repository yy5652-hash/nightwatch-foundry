"""Preserve own exact-image finite-fraction evidence without production edits."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args = parser.parse_args()
repository = Path(__file__).resolve().parents[2]
out = (repository / args.out).resolve()
assert out.is_relative_to(repository / "evidence/systems-engineer")
out.mkdir(parents=True, exist_ok=False)
name = "systems-engineer-s1-fraction-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S").lower()
image = "systems-engineer-tablekeeper-s1:decimal-05-20261004t023841"
candidate = "f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
record = {"candidate": candidate, "image": image, "commands": [], "cleanup": []}
created = False
started = time.monotonic()


def run(argv, payload=None):
    beginning = time.monotonic()
    result = subprocess.run(argv, input=payload, capture_output=True, cwd=repository)
    record["commands"].append({"argv": argv, "returncode": result.returncode,
                               "wall_seconds": time.monotonic() - beginning})
    return result


try:
    result = run(["docker", "run", "-d", "--name", name, "--network", "none", "--cpus", "2", "--memory", "2g",
                  "-e", "PORT=18122", image])
    assert result.returncode == 0
    created = True
    result = run(["docker", "exec", name, "python", "-c",
                  "import time,urllib.request\nfor attempt in range(100):\n try:\n  assert urllib.request.urlopen('http://127.0.0.1:18122/health',timeout=1).status==200\n  break\n except Exception: time.sleep(.05)\nelse: raise RuntimeError('health')"])
    assert result.returncode == 0
    settings = json.loads(run(["docker", "inspect", name]).stdout)[0]
    record["constraints"] = {"cpus": settings["HostConfig"]["NanoCpus"] / 1e9, "memory_bytes": settings["HostConfig"]["Memory"],
                              "network": settings["HostConfig"]["NetworkMode"], "mounts": settings["Mounts"]}
    record["hashes"] = {}
    for filename in ("core.py", "server.py"):
        expected = hashlib.sha256(run(["git", "show", candidate + ":stage-1/" + filename]).stdout).hexdigest()
        actual = run(["docker", "exec", name, "python", "-c",
                      "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())" % filename]).stdout.decode().strip()
        assert actual == expected
        record["hashes"][filename] = {"expected": expected, "actual": actual}
    trace = "/tmp/systems-engineer-finite-fraction.json"
    result = run(["docker", "exec", "-i", name, "python", "-", "http://127.0.0.1:18122", trace],
                 (repository / "evidence/systems-engineer/stage-1-finite-fraction-client.py").read_bytes())
    (out / "probe.log").write_bytes(result.stdout + result.stderr)
    copied = run(["docker", "cp", name + ":" + trace, str(out / "probe.json")])
    assert copied.returncode == 0
    record["summary"] = json.loads((out / "probe.json").read_text())["summary"]
    assert result.returncode == 1 and record["summary"]["failed"] == 3
    record["result"] = "three service failures reproduced, not repaired"
finally:
    if created:
        result = run(["docker", "rm", "-f", name])
        record["cleanup"].append({"name": name, "returncode": result.returncode})
    record["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
print(str(out))
