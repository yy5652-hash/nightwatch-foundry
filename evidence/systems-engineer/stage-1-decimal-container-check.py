"""Own exact-commit Stage 1 decimal/inherited HTTP image diagnostic."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument("--revision", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
repository = Path(__file__).resolve().parents[2]
workspace = repository.parents[1]
out = (repository / args.out).resolve()
assert out.is_relative_to(repository / "evidence/systems-engineer")
out.mkdir(parents=True, exist_ok=False)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S").lower()
prefix = "systems-engineer-s1-decimal-" + stamp
image = "systems-engineer-tablekeeper-s1:decimal-05-" + stamp
network = prefix + "-net"
legacy_revision = "49287b4a5a1481f995c470ccae31776f03d4b863"
record = {"candidate": args.revision, "started_utc": datetime.now(timezone.utc).isoformat(),
          "kind": "own builder diagnostic, independent acceptance pending",
          "model": "configured gpt-6.1-sol; actual override/effort/usage/spend unknown",
          "commands": [], "containers": [], "cleanup": []}
created, network_created = [], False
started = time.monotonic()


def run(argv, *, payload=None, artifact=None):
    beginning = time.monotonic()
    result = subprocess.run(argv, input=payload, capture_output=True, cwd=repository)
    record["commands"].append({"argv": argv, "returncode": result.returncode,
                               "wall_seconds": time.monotonic() - beginning, "artifact": artifact})
    if artifact:
        (out / artifact).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("failed command; inspect " + str(artifact or argv[0]))
    return result.stdout


try:
    with tempfile.TemporaryDirectory(prefix="systems-engineer-s1-decimal-context-", dir=workspace / "band-work") as temporary:
        context = Path(temporary)
        sources = {name: run(["git", "show", args.revision + ":stage-1/" + name])
                   for name in ("Dockerfile", "server.py", "core.py", ".dockerignore", "RUN.md")}
        for name, value in sources.items():
            (context / name).write_bytes(value)
        record["build_source_sha256"] = {name: hashlib.sha256(value).hexdigest() for name, value in sources.items()}
        run(["docker", "build", "-t", image, str(context)], artifact="build.log")
    run(["docker", "network", "create", "--internal", network])
    network_created = True
    record["internal_network"] = json.loads(run(["docker", "network", "inspect", network]))[0]["Internal"]
    setup = [(prefix + "-source", 18119, image, args.revision),
             (prefix + "-destination", 18120, image, args.revision),
             (prefix + "-legacy", 18121, "systems-engineer-tablekeeper-s1:calendar-02", legacy_revision)]
    for name, port, tag, revision in setup:
        run(["docker", "run", "-d", "--name", name, "--network", network, "--cpus", "2", "--memory", "2g",
             "-e", "PORT=" + str(port), tag])
        created.append(name)
        health_start = time.monotonic()
        run(["docker", "exec", name, "python", "-c",
             "import time,urllib.request\nfor attempt in range(100):\n try:\n  assert urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=1).status==200\n  break\n except Exception: time.sleep(.05)\nelse: raise RuntimeError('health timeout')" % port])
        elapsed = time.monotonic() - health_start
        settings = json.loads(run(["docker", "inspect", name]))[0]
        hashes = {}
        for filename in ("core.py", "server.py"):
            expected = hashlib.sha256(run(["git", "show", revision + ":stage-1/" + filename])).hexdigest()
            actual = run(["docker", "exec", name, "python", "-c",
                          "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())" % filename]).decode().strip()
            assert actual == expected
            hashes[filename] = {"expected": expected, "actual": actual, "source_revision": revision}
        record["containers"].append({"name": name, "port": port, "image": tag, "hashes": hashes,
             "post_launch_health_probe_seconds": elapsed, "cpus": settings["HostConfig"]["NanoCpus"] / 1e9,
             "memory_bytes": settings["HostConfig"]["Memory"], "network": settings["HostConfig"]["NetworkMode"],
             "mounts": settings["Mounts"], "running": settings["State"]["Running"]})
    source, destination, legacy = [item[0] for item in setup]
    source_url = "http://127.0.0.1:18119"
    destination_url = "http://" + destination + ":18120"
    trace = "/tmp/systems-engineer-s1-decimal-regression.json"
    run(["docker", "exec", "-i", source, "python", "-", "--stage", "1", "--url", source_url,
         "--destination-url", destination_url, "--trace", trace], artifact="decimal-http.log",
        payload=(repository / "evidence/systems-engineer/stage-1-2-decimal-probes.py").read_bytes())
    run(["docker", "cp", source + ":" + trace, str(out / "decimal-regression.json")])
    run(["docker", "exec", "-i", source, "python", "-", "--url", source_url,
         "--destination-url", destination_url, "--legacy-url", "http://" + legacy + ":18121"],
        artifact="inherited-http.log", payload=(repository / "evidence/systems-engineer/stage-1-builder-probes.py").read_bytes())
    trace_data = json.loads((out / "decimal-regression.json").read_text())
    def verify_private(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("state", "tokens"):
                    assert set(item) == {"private_state_sha256"}
                elif key in ("password", "token", "password_hash"):
                    assert set(item) == {"fingerprint"}
                else:
                    verify_private(item)
        elif isinstance(value, list):
            for item in value:
                verify_private(item)
    verify_private(trace_data)
    assert trace_data["summary"]["failed"] == 0
    record["decimal_summary"] = trace_data["summary"]
    record["private_trace_check"] = "all state/tokens and credential payloads fingerprinted"
    record["result"] = "passed"
finally:
    for name in reversed(created):
        result = subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        record["cleanup"].append({"argv": ["docker", "rm", "-f", name], "returncode": result.returncode})
    if network_created:
        result = subprocess.run(["docker", "network", "rm", network], capture_output=True)
        record["cleanup"].append({"argv": ["docker", "network", "rm", network], "returncode": result.returncode})
    record["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
print(str(out))
