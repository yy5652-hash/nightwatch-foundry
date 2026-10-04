"""Own complete-context decoder repair driver; execute only after source release.

Adapted from Interface's own candidate-5 driver, preserving old evidence/code.
No verifier or service implementation is imported on the host. Each execution
retains a clean detached clone and unique output, removes only its own resources.
"""

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument("--revision", required=True, help="Full coherent implementation commit, never module-only")
parser.add_argument("--probe-revision", help="Exact own committed evidence source; defaults to current HEAD")
args = parser.parse_args()
if len(args.revision) != 40 or any(c not in "0123456789abcdef" for c in args.revision):
    parser.error("An exact full revision is required")
if args.probe_revision and (len(args.probe_revision) != 40 or any(c not in "0123456789abcdef" for c in args.probe_revision)):
    parser.error("An exact full probe revision is required")
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
slug = "interface-engineer-s1-decoder-" + stamp
short = "interface-engineer-jd2-" + stamp
out = ROOT / "evidence/interface-engineer" / slug
clone = ROOT.parent / slug
out.mkdir()
network = short
current_image = "interface-engineer-tablekeeper-s1:decoder-" + stamp
old_sources = ("49287b4a5a1481f995c470ccae31776f03d4b863", "f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250")
files = ("core.py", "server.py", "json_codec.py", "Dockerfile", "RUN.md", ".dockerignore")
commands, checks, resources, errors, created, old_contexts = [], [], [], [], [], []
created_network = False
start = time.monotonic()


def execute(argv, *, cwd=ROOT, stdin=None, log=None, require=True):
    begin = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    row = {"argv": argv, "cwd": str(cwd), "seconds": time.monotonic()-begin, "returncode": result.returncode}
    if stdin is not None:
        row["stdin_sha256"] = hashlib.sha256(stdin).hexdigest()
    if log:
        (out / log).write_bytes(result.stdout)
        row["output"] = log
    commands.append(row)
    if require and result.returncode:
        raise RuntimeError("Own command failed: " + " ".join(argv[:3]))
    return result.stdout


def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
    if not condition:
        errors.append(name)


def digest(value):
    return hashlib.sha256(value).hexdigest()


HEALTH = """import json,time,urllib.request,sys
start=time.monotonic()
while True:
 try:
  with urllib.request.urlopen('http://127.0.0.1:'+sys.argv[1]+'/health',timeout=2) as r:
   if r.status==200 and json.loads(r.read())=={'status':'ok'}:break
 except Exception:
  if time.monotonic()-start>50:raise
  time.sleep(.05)
print(json.dumps({'seconds':time.monotonic()-start,'status':200}))
"""
HASH = "import hashlib,json,pathlib;print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').glob('*.py')}))"

try:
    probe_revision = args.probe_revision or execute(["git", "rev-parse", "HEAD"]).decode().strip()
    execute(["git", "clone", "--no-hardlinks", str(ROOT), str(clone)], log="clone.log")
    execute(["git", "checkout", "--detach", args.revision], cwd=clone, log="checkout.log")
    head = execute(["git", "rev-parse", "HEAD"], cwd=clone).decode().strip()
    status = execute(["git", "status", "--porcelain"], cwd=clone).decode()
    check("Exact clean named clone", head == args.revision and not status)
    hashes = {name: digest((clone / "stage-1" / name).read_bytes()) for name in files}
    for name in ("core.py", "server.py", "json_codec.py"):
        tree = ast.parse((clone / "stage-1" / name).read_text())
        if name != "json_codec.py":
            wired = any(isinstance(n, ast.Import) and any(a.name == "json_codec" for a in n.names) or
                        isinstance(n, ast.ImportFrom) and n.module == "json_codec" for n in ast.walk(tree))
            if not wired:
                raise RuntimeError("Refuse intermediate unwired candidate: " + name)
    tree_id = execute(["git", "rev-parse", "HEAD:stage-1"], cwd=clone).decode().strip()
    probe_names = ("stage-1-json-repair-probe.py", "stage-1-decoder-repair-container-check.py", "stage-1-transport-probe.py", "stage-1-decoder-repair-probe.py")
    probe_source = {name: execute(["git", "show", probe_revision+":evidence/interface-engineer/"+name]) for name in probe_names}
    (out / "source-proof.json").write_text(json.dumps({"candidate": head, "stage1_tree": tree_id,
        "clone": str(clone), "initial_status": status, "source_hashes": hashes,
        "module_identity_basis": "Actual json_codec.py blob from named full coherent service revision; never superseded module009 assumption",
        "latest_module_repair_provenance": "JSON-REPAIR-2: exact released full candidate module hash; prior candidate6 decoder refusals remain preserved",
        "probe_revision": probe_revision, "probe_hashes": {n: digest(data) for n,data in probe_source.items()},
        "executed_driver_sha256": digest(Path(__file__).read_bytes()),
        "source_inputs": "Complete assigned task/spec/adopted decisions, own prior probes/drivers, supplied owner/API handoffs and failure descriptions. No verifier probe or shipped test code read."}, indent=2)+"\n")
    execute(["docker", "build", "-t", current_image, str(clone / "stage-1")], log="build-current.log")
    images = [current_image, current_image]
    expected = [hashes, hashes]
    for index, revision in enumerate(old_sources):
        context = out / ("interface-engineer-old-context-"+str(index))
        context.mkdir()
        old_contexts.append(context)
        old_hashes = {}
        for name in files:
            if name == "json_codec.py":
                continue
            data = execute(["git", "show", revision+":stage-1/"+name])
            (context/name).write_bytes(data)
            old_hashes[name] = digest(data)
        image = "interface-engineer-tablekeeper-s1:decoder-old"+str(index)+"-"+stamp
        execute(["docker", "build", "-t", image, str(context)], log="build-old"+str(index)+".log")
        images.append(image)
        expected.append(old_hashes)
    execute(["docker", "network", "create", "--internal", network], log="network.log")
    created_network = True
    urls = []
    for index, label in enumerate(("a", "b", "old", "c5")):
        name = short+"-"+label
        if len(name) > 63:
            raise RuntimeError("Invalid own service DNS label")
        port = 9090 if index == 1 else 8080
        command = ["docker", "run", "-d", "--name", name, "--network", network,
                   "--cpus", "2", "--memory", "2g", "-p", str(18240+index)+":"+str(port)]
        if index == 1:
            command += ["-e", "PORT=9090"]
        launch_utc = datetime.now(timezone.utc).isoformat()
        launch = time.monotonic()
        execute(command+[images[index]], log="run-"+label+".log")
        created.append(name)
        health = json.loads(execute(["docker", "exec", name, "python", "-c", HEALTH, str(port)], log="health-"+label+".json"))
        elapsed = time.monotonic()-launch
        healthy_utc = datetime.now(timezone.utc).isoformat()
        check(label+" healthy within 60s", health["status"] == 200 and elapsed < 60)
        if index < 2:
            check(label+" early health observed within requested5s", health["status"] == 200 and elapsed < 5)
        info = json.loads(execute(["docker", "inspect", name]))[0]
        actual = json.loads(execute(["docker", "exec", name, "python", "-c", HASH], log="hash-"+label+".json"))
        py_files = ("core.py", "server.py", "json_codec.py") if index < 2 else ("core.py", "server.py")
        check(label+" image matches exact source", all(actual[n] == expected[index][n] for n in py_files))
        check(label+" constrained with no mounts", info["HostConfig"]["NanoCpus"] == 2000000000 and
              info["HostConfig"]["Memory"] == 2147483648 and not info["Mounts"])
        listener = execute(["docker", "exec", name, "python", "-c", "import pathlib;print(pathlib.Path('/proc/net/tcp').read_text())"], log="listen-"+label+".txt").decode()
        check(label+" all-interface correct PORT", "00000000:"+f"{port:04X}" in listener)
        urls.append("http://"+name+":"+str(port))
        resources.append({"label": label, "name": name, "source_revision": head if index < 2 else old_sources[index-2],
                          "image": info["Image"], "nano_cpus": info["HostConfig"]["NanoCpus"],
                          "memory_bytes": info["HostConfig"]["Memory"], "mounts": info["Mounts"],
                          "network": info["HostConfig"]["NetworkMode"], "port": port, "host_port": 18240+index,
                          "launch_utc": launch_utc, "healthy_observation_utc": healthy_utc,
                          "health_from_launch_seconds": elapsed, "health_poll_seconds": health["seconds"],
                          "startup_scope": "docker run invocation to successful health-command return, before all source inspection",
                          "runtime_hashes": actual})
    net = json.loads(execute(["docker", "network", "inspect", network]))[0]
    check("Internal offline network", net["Internal"] is True)
    inherited = execute(["docker", "exec", "-i", created[1], "python", "-", "http://127.0.0.1:9090"],
                        stdin=probe_source["stage-1-transport-probe.py"],
                        log="inherited-http.json", require=False)
    inherited = json.loads(inherited)
    check("Own inherited integration checks", inherited["failed"] == 0)
    repaired = execute(["docker", "run", "--rm", "-i", "--name", short+"-client", "--network", network,
                        "--cpus", "2", "--memory", "2g", "--entrypoint", "python", current_image, "-", *urls],
                       stdin=probe_source["stage-1-json-repair-probe.py"],
                       log="json-repair-http.json", require=False)
    repaired = json.loads(repaired)
    check("Own JSON repair integration checks", repaired["failed"] == 0)
    deep = execute(["docker", "run", "--rm", "-i", "--name", short+"-deep", "--network", network,
                    "--cpus", "2", "--memory", "2g", "--entrypoint", "python", current_image, "-", *urls[:2]],
                   stdin=probe_source["stage-1-decoder-repair-probe.py"], log="decoder-deep-http.json", require=False)
    deep = json.loads(deep)
    check("Own actual deep decoder integration checks", deep["failed"] == 0 and not deep["blocked"])
    final_status = execute(["git", "status", "--porcelain"], cwd=clone).decode()
    check("Exact clone remains clean", not final_status)
    (out / "summary.json").write_text(json.dumps({"candidate": head, "stage1_tree": tree_id, "probe_revision": probe_revision,
        "clone_status": final_status, "inherited": {k: inherited[k] for k in ("checks", "passed", "failed", "elapsed_seconds")},
        "json_repair": {k: repaired[k] for k in ("operations", "assertions", "passed", "failed", "seconds", "max_request_seconds")},
        "decoder_deep": {k: deep[k] for k in ("depths", "shapes", "client_recursion_limit", "operations", "assertions", "passed", "failed", "seconds", "max_request_seconds", "max_body_bytes", "blocked")},
        "runtime_checks": checks}, indent=2)+"\n")
except Exception as exc:
    errors.append(type(exc).__name__+": "+str(exc))
finally:
    cleanup = []
    for name in reversed(created):
        execute(["docker", "logs", name], log="logs-"+name.rsplit("-", 1)[1]+".txt", require=False)
        execute(["docker", "rm", "-f", name], log="cleanup-"+name.rsplit("-", 1)[1]+".log", require=False)
        cleanup.append(commands[-1])
    if created_network:
        execute(["docker", "network", "rm", network], log="cleanup-network.log", require=False)
        cleanup.append(commands[-1])
    for context in old_contexts:
        shutil.rmtree(context)
    if any(r["returncode"] for r in cleanup):
        errors.append("Own cleanup failed")
    elapsed = time.monotonic()-start
    (out / "run.json").write_text(json.dumps({"candidate": args.revision, "old_sources": old_sources,
        "commands": commands, "resources": resources, "checks": checks, "errors": errors,
        "cleanup": cleanup, "elapsed_seconds": elapsed, "clone": str(clone),
        "images_retained": [current_image, *["interface-engineer-tablekeeper-s1:decoder-old"+str(i)+"-"+stamp for i in range(2)]],
        "build_cache": "Available cache permitted; actual build logs retained",
        "model": "configured gpt-6.1-sol", "actual_override_effort_usage_spend": "unknown"}, indent=2)+"\n")
    print(json.dumps({"candidate": args.revision, "out": str(out), "seconds": elapsed, "errors": errors}))
sys.exit(1 if errors else 0)
