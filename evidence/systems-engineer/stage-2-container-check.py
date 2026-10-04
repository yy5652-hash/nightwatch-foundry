"""Own constrained API diagnostic; browser interactions are separately owned.

Default: committed Stage 2 core plus frozen accepted Stage 1 transport/runtime.
With --integrated: the complete committed Stage 2 subtree. Both modes run two
current processes, accepted Stage 1 migration source and earlier receipt source.
Artifacts contain no exports, passwords or bearer tokens.
"""
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
parser.add_argument("--integrated", action="store_true", help="Build the complete named Stage 2 subtree")
args = parser.parse_args()
repository = Path(__file__).resolve().parents[2]
workspace = repository.parents[1]
out = (repository / args.out).resolve()
assert out.is_relative_to(repository / "evidence/systems-engineer")
out.mkdir(parents=True, exist_ok=False)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S").lower()
prefix = "systems-engineer-s2-api-" + stamp
network = prefix + "-net"
image = "systems-engineer-tablekeeper-s2:api-" + stamp
accepted = "2a4b0408a3453bc87d86bca3d0ec571f479e03ca"
legacy_revision = "49287b4a5a1481f995c470ccae31776f03d4b863"
transport_revision = args.revision if args.integrated else accepted
record = {"kind": "API builder diagnostic, " + ("complete integrated image" if args.integrated else "frozen transport") + ", no UI acceptance",
          "core_revision": args.revision, "transport_revision": transport_revision,
          "started_utc": datetime.now(timezone.utc).isoformat(),
          "model": "configured gpt-6.1-sol; actual override/effort/usage/spend unknown",
          "commands": [], "containers": [], "cleanup": []}
created, network_created = [], False
started = time.monotonic()

def run(argv, *, artifact=None, payload=None):
    beginning = time.monotonic()
    result = subprocess.run(argv, input=payload, capture_output=True, cwd=repository)
    record["commands"].append({"argv": argv, "returncode": result.returncode,
                               "wall_seconds": time.monotonic() - beginning,
                               "artifact": artifact})
    if artifact:
        (out / artifact).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("command failed; inspect " + str(artifact or argv[0]))
    return result.stdout

try:
    with tempfile.TemporaryDirectory(prefix="systems-engineer-s2-api-context-", dir=workspace / "band-work") as temporary:
        context = Path(temporary)
        if args.integrated:
            sources = {}
            tree = run(["git", "ls-tree", "-r", "-z", args.revision, "--", "stage-2"])
            for entry in tree.decode().split("\0"):
                if not entry:
                    continue
                attributes, path = entry.split("\t", 1)
                mode, kind, object_id = attributes.split()
                assert kind == "blob" and mode in ("100644", "100755")
                relative = Path(path).relative_to("stage-2")
                assert ".." not in relative.parts
                sources[str(relative)] = run(["git", "show", args.revision + ":" + path])
        else:
            sources = {name: run(["git", "show", accepted + ":stage-1/" + name])
                       for name in ("Dockerfile", "server.py", ".dockerignore")}
            sources["core.py"] = run(["git", "show", args.revision + ":stage-2/core.py"])
        for name, value in sources.items():
            (context / name).parent.mkdir(parents=True, exist_ok=True)
            (context / name).write_bytes(value)
        record["build_source_sha256"] = {name: hashlib.sha256(value).hexdigest() for name, value in sources.items()}
        run(["docker", "build", "-t", image, str(context)], artifact="build.log")
    run(["docker", "network", "create", "--internal", network])
    network_created = True
    record["internal_network"] = json.loads(run(["docker", "network", "inspect", network]))[0]["Internal"]
    setup = [(prefix + "-source", 18113, image, args.revision, "stage-2", transport_revision),
             (prefix + "-destination", 18114, image, args.revision, "stage-2", transport_revision),
             (prefix + "-accepted", 18115, "systems-engineer-tablekeeper-s1:minute-04", accepted, "stage-1", accepted),
             (prefix + "-legacy", 18116, "systems-engineer-tablekeeper-s1:calendar-02", legacy_revision, "stage-1", legacy_revision)]
    for name, port, tag, revision, folder, transport_revision in setup:
        run(["docker", "run", "-d", "--name", name, "--network", network, "--cpus", "2", "--memory", "2g",
             "-e", "PORT=" + str(port), tag])
        created.append(name)
        health_start = time.monotonic()
        run(["docker", "exec", name, "python", "-c",
             "import time,urllib.request\nfor attempt in range(100):\n try:\n  assert urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=1).status==200\n  break\n except Exception:\n  time.sleep(.05)\nelse: raise RuntimeError('health timeout')" % port])
        health_elapsed = time.monotonic() - health_start
        settings = json.loads(run(["docker", "inspect", name]))[0]
        hashes = {}
        transport_folder = "stage-2" if args.integrated and folder == "stage-2" else "stage-1"
        for filename, source_revision, source_folder in [("core.py", revision, folder),
                                                         ("server.py", transport_revision, transport_folder)]:
            expected = hashlib.sha256(run(["git", "show", source_revision + ":" + source_folder + "/" + filename])).hexdigest()
            actual = run(["docker", "exec", name, "python", "-c",
                          "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())" % filename]).decode().strip()
            assert actual == expected
            hashes[filename] = {"expected": expected, "actual": actual, "source_revision": source_revision}
        record["containers"].append({"name": name, "port": port, "image": tag, "hashes": hashes,
            "post_launch_health_probe_seconds": health_elapsed, "running": settings["State"]["Running"],
            "cpus": settings["HostConfig"]["NanoCpus"] / 1e9, "memory_bytes": settings["HostConfig"]["Memory"],
            "network": settings["HostConfig"]["NetworkMode"], "mounts": settings["Mounts"]})
    source, destination, prior, legacy = [x[0] for x in setup]
    current_url = "http://127.0.0.1:18113"
    destination_url = "http://" + destination + ":18114"
    trace_path = "/tmp/systems-engineer-s2-member-oracle.json"
    run(["docker", "exec", "-i", source, "python", "-", "--url", current_url,
         "--destination-url", destination_url, "--source-url", "http://" + prior + ":18115",
         "--trace", trace_path], artifact="stage-2-http.log",
        payload=(repository / "evidence/systems-engineer/stage-2-builder-probes.py").read_bytes())
    run(["docker", "cp", source + ":" + trace_path, str(out / "member-oracle.json")])
    run(["docker", "exec", "-i", source, "python", "-", "--stage", "2", "--url", current_url,
         "--destination-url", destination_url, "--legacy-url", "http://" + legacy + ":18116"],
        artifact="inherited-http.log",
        payload=(repository / "evidence/systems-engineer/stage-1-builder-probes.py").read_bytes())
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
