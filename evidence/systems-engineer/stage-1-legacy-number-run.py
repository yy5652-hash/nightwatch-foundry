"""Run evidence-only legacy numeric receipts across two actual services."""
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
prefix = "systems-engineer-legacy-number-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S").lower()
network = prefix + "-net"
services = [
    {"name": prefix + "-old", "port": 18123,
     "image": "systems-engineer-tablekeeper-s1:calendar-02",
     "revision": "49287b4a5a1481f995c470ccae31776f03d4b863"},
    {"name": prefix + "-current", "port": 18124,
     "image": "systems-engineer-tablekeeper-s1:decimal-05-20261004t023841",
     "revision": "f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"}]
record = {"services": services, "commands": [], "cleanup": []}
created = []
network_created = False
started = time.monotonic()


def run(argv, payload=None):
    beginning = time.monotonic()
    result = subprocess.run(argv, input=payload, capture_output=True, cwd=repository)
    index = len(record["commands"])
    (out / ("command-%02d.log" % index)).write_bytes(result.stdout + result.stderr)
    record["commands"].append({"argv": argv, "returncode": result.returncode,
                               "wall_seconds": time.monotonic() - beginning,
                               "log": "command-%02d.log" % index})
    return result


try:
    assert run(["docker", "network", "create", "--internal", network]).returncode == 0
    network_created = True
    for service in services:
        result = run(["docker", "run", "-d", "--name", service["name"], "--network", network,
                      "--cpus", "2", "--memory", "2g", "-e", "PORT=" + str(service["port"]), service["image"]])
        assert result.returncode == 0
        created.append(service["name"])
        health_start = time.monotonic()
        result = run(["docker", "exec", service["name"], "python", "-c",
                      "import time,urllib.request\nfor attempt in range(100):\n try:\n  assert urllib.request.urlopen('http://127.0.0.1:%s/health',timeout=1).status==200\n  break\n except Exception: time.sleep(.05)\nelse: raise RuntimeError('health')" % service["port"]])
        assert result.returncode == 0
        service["health_check_seconds"] = time.monotonic() - health_start
        settings = json.loads(run(["docker", "inspect", service["name"]]).stdout)[0]
        service["image_id"] = settings["Image"]
        service["constraints"] = {"cpus": settings["HostConfig"]["NanoCpus"] / 1e9,
                                  "memory_bytes": settings["HostConfig"]["Memory"],
                                  "network": settings["HostConfig"]["NetworkMode"], "mounts": settings["Mounts"]}
        service["hashes"] = {}
        for filename in ("core.py", "server.py"):
            result = run(["git", "show", service["revision"] + ":stage-1/" + filename])
            assert result.returncode == 0
            expected = hashlib.sha256(result.stdout).hexdigest()
            actual = run(["docker", "exec", service["name"], "python", "-c",
                          "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())" % filename]).stdout.decode().strip()
            assert actual == expected
            service["hashes"][filename] = {"expected": expected, "actual": actual}
    old, current = services
    trace = "/tmp/systems-engineer-legacy-number.json"
    client = repository / "evidence/systems-engineer/stage-1-legacy-number-client.py"
    record["client_sha256"] = hashlib.sha256(client.read_bytes()).hexdigest()
    result = run(["docker", "exec", "-i", current["name"], "python", "-",
                  "http://" + old["name"] + ":" + str(old["port"]),
                  "http://127.0.0.1:" + str(current["port"]), trace], client.read_bytes())
    assert run(["docker", "cp", current["name"] + ":" + trace, str(out / "probe.json")]).returncode == 0
    record["summary"] = json.loads((out / "probe.json").read_text())["summary"]
    assert result.returncode == 0 and record["summary"]["failed"] == 0
    record["result"] = "genuine old parser/export projection and original receipt replays observed"
finally:
    for name in reversed(created):
        result = run(["docker", "rm", "-f", name])
        record["cleanup"].append({"name": name, "returncode": result.returncode})
    if network_created:
        result = run(["docker", "network", "rm", network])
        record["cleanup"].append({"name": network, "returncode": result.returncode})
    record["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"out": str(out), "summary": record.get("summary"), "wall_seconds": record["wall_seconds"]}))
