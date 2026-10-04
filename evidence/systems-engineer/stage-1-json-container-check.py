"""Own complete named Stage1 image/genuine-source HTTP regression orchestration."""
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
out.relative_to(repo / "evidence/systems-engineer")
out.mkdir(parents=True, exist_ok=False)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f").lower()
prefix = "systems-engineer-json-" + stamp
network = prefix + "-net"
image = "systems-engineer-tablekeeper-s1:json-" + stamp
client_image = "systems-engineer-json-client:" + stamp
legacy = "49287b4a5a1481f995c470ccae31776f03d4b863"
old = "f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250"
clone = workspace / "band-work" / prefix
created, contexts = [], []
network_created = False
record = {"requested_revision": args.revision, "started_utc": datetime.now(timezone.utc).isoformat(),
          "kind": "own complete builder checks, independent acceptance pending", "commands": [],
          "services": [], "cleanup": [], "clone": str(clone), "highest_accepted": 0}
started = time.monotonic()


def run(argv, *, timeout=120, required=True):
    index = len(record["commands"])
    begin = time.monotonic()
    result = subprocess.run(argv, cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    log = out / ("command-%02d.log" % index)
    log.write_bytes(result.stdout)
    record["commands"].append({"argv": argv, "returncode": result.returncode,
                                "seconds": time.monotonic() - begin, "log": str(log)})
    if required and result.returncode:
        raise RuntimeError("command%d failed; see%s" % (index, log))
    return result.stdout


def health(name, port):
    script = ("import time,urllib.request\n"
              "for attempt in range(120):\n"
              " try:\n"
              "  assert urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=.5).status==200\n"
              "  break\n"
              " except Exception: time.sleep(.05)\n"
              "else: raise RuntimeError('health timeout')" % port)
    run(["docker", "exec", name, "python", "-c", script], timeout=60)


def inspect_resource(name):
    details = json.loads(run(["docker", "inspect", name]))[0]
    host = details["HostConfig"]
    assert host["NanoCpus"] == 2_000_000_000 and host["Memory"] == 2_147_483_648
    assert details["Mounts"] == [] and host["NetworkMode"] == network
    return {"name": name, "image_id": details["Image"], "cpus": 2, "memory_bytes": host["Memory"],
            "network": network, "mounts": [], "ports": host["PortBindings"]}


try:
    candidate = run(["git", "rev-parse", args.revision + "^{commit}"]).decode().strip()
    record["candidate"] = candidate
    run(["git", "clone", "--no-hardlinks", "--no-checkout", str(repo), str(clone)])
    run(["git", "-C", str(clone), "checkout", "--detach", candidate])
    assert run(["git", "-C", str(clone), "status", "--porcelain"]) == b""
    record["clean_clone_before"] = True
    stage = clone / "stage-1"
    filenames = ("Dockerfile", "server.py", "core.py", "json_codec.py", ".dockerignore", "RUN.md")
    record["current_source_sha256"] = {f: hashlib.sha256((stage / f).read_bytes()).hexdigest() for f in filenames}
    run(["docker", "build", "-t", image, str(stage)], timeout=300)
    service_specs = [(prefix + "-a", 8080, 18140, image, candidate),
                     (prefix + "-b", 18141, 18141, image, candidate)]
    for suffix, revision in (("legacy", legacy), ("old", old)):
        context = Path(tempfile.mkdtemp(prefix="systems-engineer-json-" + suffix + "-", dir=workspace / "band-work"))
        contexts.append(context)
        for filename in ("Dockerfile", "server.py", "core.py", ".dockerignore", "RUN.md"):
            (context / filename).write_bytes(run(["git", "show", revision + ":stage-1/" + filename]))
        tag = image + "-" + suffix
        run(["docker", "build", "-t", tag, str(context)], timeout=300)
        port = 18142 if suffix == "legacy" else 18143
        service_specs.append((prefix + "-" + suffix, port, port, tag, revision))
    client_context = Path(tempfile.mkdtemp(prefix="systems-engineer-json-client-", dir=workspace / "band-work"))
    contexts.append(client_context)
    for filename in ("stage-1-json-http-probes.py", "stage-1-builder-probes.py", "stage-1-2-decimal-probes.py",
                     "stage-1-response-ownership-probes.py"):
        shutil.copyfile(clone / "evidence/systems-engineer" / filename, client_context / filename)
    (client_context / "Dockerfile").write_text("FROM " + image + "\nWORKDIR /probe\nCOPY *.py ./\n")
    run(["docker", "build", "-t", client_image, str(client_context)], timeout=120)
    run(["docker", "network", "create", "--internal", network])
    network_created = True
    assert json.loads(run(["docker", "network", "inspect", network]))[0]["Internal"] is True
    for name, port, host_port, tag, revision in service_specs:
        before = time.monotonic()
        command = ["docker", "run", "-d", "--name", name, "--network", network, "--cpus", "2", "--memory", "2g",
                   "-p", str(host_port) + ":" + str(port)]
        if port != 8080:
            command.extend(["-e", "PORT=" + str(port)])
        command.append(tag)
        run(command)
        created.append(name)
        health(name, port)
        info = inspect_resource(name)
        info["start_to_health_seconds"] = time.monotonic() - before
        info["source_revision"] = revision
        info["source_sha256"] = {}
        for filename in (("core.py", "server.py", "json_codec.py") if revision == candidate else ("core.py", "server.py")):
            expected = hashlib.sha256(run(["git", "show", revision + ":stage-1/" + filename])).hexdigest()
            actual = run(["docker", "exec", name, "python", "-c",
                          "import hashlib;print(hashlib.sha256(open('/app/%s','rb').read()).hexdigest())" % filename]).decode().strip()
            assert actual == expected
            info["source_sha256"][filename] = actual
        assert info["start_to_health_seconds"] < 60
        record["services"].append(info)
    base, peer, legacy_name, old_name = [spec[0] for spec in service_specs]
    urls = ["http://" + name + ":" + str(port) for name, port, *_ in service_specs]
    client_specs = [
        ("numbers", ["stage-1-json-http-probes.py", "--base", urls[0], "--peer", urls[1],
                     "--legacy", urls[2], "--old", urls[3], "--out", "/tmp/systems-engineer-json-numbers"]),
        ("inherited", ["stage-1-builder-probes.py", "--url", urls[0], "--destination-url", urls[1], "--legacy-url", urls[2]]),
        ("digits", ["stage-1-2-decimal-probes.py", "--stage", "1", "--url", urls[0], "--destination-url", urls[1],
                    "--trace", "/tmp/systems-engineer-json-digits.json"]),
        ("ownership", ["stage-1-response-ownership-probes.py", "/tmp/systems-engineer-json-ownership.json"])]
    record["client_results"] = []
    for label, arguments in client_specs:
        name = prefix + "-" + label
        run(["docker", "create", "--name", name, "--network", network, "--cpus", "2", "--memory", "2g",
             client_image, "python", "-B", *arguments])
        created.append(name)
        info = inspect_resource(name)
        run(["docker", "start", name])
        exit_code = int(run(["docker", "wait", name], timeout=120).decode().strip())
        output = run(["docker", "logs", name])
        (out / (label + ".log")).write_bytes(output)
        if label == "numbers":
            run(["docker", "cp", name + ":/tmp/systems-engineer-json-numbers", str(out / "numbers")])
        elif label == "digits":
            run(["docker", "cp", name + ":/tmp/systems-engineer-json-digits.json", str(out / "digits.json")])
        elif label == "ownership":
            run(["docker", "cp", name + ":/tmp/systems-engineer-json-ownership.json", str(out / "ownership.json")])
        record["client_results"].append({"label": label, "exit_code": exit_code, "resource": info})
    record["numeric_summary"] = json.loads((out / "numbers/trace.json").read_text())["summary"]
    record["digit_summary"] = json.loads((out / "digits.json").read_text())["summary"]
    record["ownership_summary"] = json.loads((out / "ownership.json").read_text())["summary"]
    assert run(["git", "-C", str(clone), "status", "--porcelain"]) == b""
    record["clean_clone_after"] = True
    record["result"] = "passed" if all(r["exit_code"] == 0 for r in record["client_results"]) else "failed"
finally:
    for name in reversed(created):
        run(["docker", "logs", name], required=False)
        run(["docker", "rm", "-f", name], required=False)
        record["cleanup"].append({"name": name, "returncode": record["commands"][-1]["returncode"]})
    if network_created:
        run(["docker", "network", "rm", network], required=False)
        record["cleanup"].append({"name": network, "returncode": record["commands"][-1]["returncode"]})
    for context in contexts:
        shutil.rmtree(context)
    record["contexts_removed"] = all(not c.exists() for c in contexts)
    record["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: record.get(k) for k in ("candidate", "result", "numeric_summary", "digit_summary",
                     "client_results", "wall_seconds", "contexts_removed")}))
    if record.get("result") != "passed":
        raise SystemExit(1)
