"""Run the own lexical/HTTP boundary reproduction on retained exact images."""
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
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S").lower()
record = {"commands": [], "processes": [], "cleanup": []}
created = []
started = time.monotonic()


def run(argv, payload=None):
    beginning = time.monotonic()
    result = subprocess.run(argv, input=payload, capture_output=True, cwd=repository)
    record["commands"].append({"argv": argv, "returncode": result.returncode,
                               "wall_seconds": time.monotonic() - beginning})
    return result


try:
    for stage, image, revision, port in (
        (2, "systems-engineer-tablekeeper-s2:api-20261004t014617", "ff8472b5edc8513c1cd994678ea01471e7fb1ddc", 18117),
        (1, "systems-engineer-tablekeeper-s1:minute-04", "2a4b0408a3453bc87d86bca3d0ec571f479e03ca", 18118)):
        name = "systems-engineer-decimal-reproduce-" + stamp + "-s" + str(stage)
        result = run(["docker", "run", "-d", "--name", name, "--network", "none", "--cpus", "2", "--memory", "2g",
                      "-e", "PORT=" + str(port), image])
        assert result.returncode == 0, result.stderr.decode()
        created.append(name)
        health = run(["docker", "exec", name, "python", "-c",
                      "import time,urllib.request\nfor i in range(100):\n try:\n  assert urllib.request.urlopen('http://127.0.0.1:%d/health').status==200\n  break\n except Exception: time.sleep(.05)\nelse: raise RuntimeError('health')" % port])
        assert health.returncode == 0
        settings = json.loads(run(["docker", "inspect", name]).stdout)[0]
        hashes = {}
        for filename in ("core.py", "server.py"):
            source = run(["git", "show", revision + ":stage-" + str(stage) + "/" + filename]).stdout
            expected = hashlib.sha256(source).hexdigest()
            actual = run(["docker", "exec", name, "python", "-c",
                          "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())" % filename]).stdout.decode().strip()
            assert actual == expected
            hashes[filename] = expected
        trace = "/tmp/systems-engineer-decimal-reproduction.json"
        result = run(["docker", "exec", "-i", name, "python", "-", "--url", "http://127.0.0.1:" + str(port),
                      "--stage", str(stage), "--reproduce", "--trace", trace],
                     (repository / "evidence/systems-engineer/stage-1-2-decimal-probes.py").read_bytes())
        (out / ("stage-" + str(stage) + ".log")).write_bytes(result.stdout + result.stderr)
        copied = run(["docker", "cp", name + ":" + trace, str(out / ("stage-" + str(stage) + ".json"))])
        assert copied.returncode == 0
        probe = json.loads((out / ("stage-" + str(stage) + ".json")).read_text())
        assert result.returncode == 1 and probe["summary"]["failed"] == 5
        record["processes"].append({"stage": stage, "revision": revision, "image": image, "name": name,
                                    "hashes": hashes, "summary": probe["summary"],
                                    "cpus": settings["HostConfig"]["NanoCpus"] / 1e9,
                                    "memory_bytes": settings["HostConfig"]["Memory"],
                                    "network": settings["HostConfig"]["NetworkMode"], "mounts": settings["Mounts"]})
finally:
    for name in reversed(created):
        result = run(["docker", "rm", "-f", name])
        record["cleanup"].append({"name": name, "returncode": result.returncode})
    record["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
print(str(out))
