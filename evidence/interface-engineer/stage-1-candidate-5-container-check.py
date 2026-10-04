"""Build and inspect a clean named candidate, then execute own HTTP evidence.

Only seat-owned resources are created/removed. Source clone and all failed output
are retained; no shared graded source is changed. Host uses only its stdlib.
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
WORKSPACE = ROOT.parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--revision", default="f5e0a532dcf6c2f0c44eb32d5213a9bf7812c250")
args = parser.parse_args()
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ").lower()
slug = "interface-engineer-s1-candidate5-" + stamp
out = ROOT / "evidence/interface-engineer" / slug
out.mkdir()
clone = ROOT.parent / slug
legacy_context = out / "interface-engineer-legacy-context"
network = slug
image = "interface-engineer-tablekeeper-s1:candidate5-" + stamp
legacy_image = "interface-engineer-tablekeeper-s1:legacy-candidate5-" + stamp
legacy_revision = "49287b4a5a1481f995c470ccae31776f03d4b863"
original = "2a4b0408a3453bc87d86bca3d0ec571f479e03ca"
files = ("core.py", "server.py", "Dockerfile", "RUN.md", ".dockerignore")
commands, resources, checks, errors = [], [], [], []
created_containers = []
created_network = False
start = time.monotonic()


def execute(argv, *, cwd=ROOT, stdin=None, output=None, require=True):
    begin = time.monotonic()
    result = subprocess.run(argv, cwd=cwd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    entry = {"argv": argv, "cwd": str(cwd), "seconds": time.monotonic() - begin,
             "returncode": result.returncode}
    if stdin is not None:
        entry["stdin_sha256"] = hashlib.sha256(stdin).hexdigest()
    if output:
        (out / output).write_bytes(result.stdout)
        entry["output"] = output
    commands.append(entry)
    if require and result.returncode:
        raise RuntimeError("Command failed: " + " ".join(argv[:4]))
    return result.stdout


def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})
    if not condition:
        errors.append(name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


health_code = """import json,time,urllib.request
start=time.monotonic()
deadline=start+50
while True:
 try:
  with urllib.request.urlopen('http://127.0.0.1:'+__import__('sys').argv[1]+'/health',timeout=2) as r:
   if r.status==200 and json.loads(r.read())=={'status':'ok'}: break
 except Exception:
  if time.monotonic()>deadline: raise
  time.sleep(.05)
print(json.dumps({'probe_seconds':time.monotonic()-start,'status':200}))
"""
hash_code = """import hashlib,json,pathlib,sys
print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/app').glob('*.py')}))
print(json.dumps({'separate_exec_interpreter_int_max_str_digits_not_service_process':sys.get_int_max_str_digits()}))
"""

try:
    probe_revision = execute(["git", "rev-parse", "HEAD"]).decode().strip()
    execute(["git", "clone", "--no-hardlinks", str(ROOT), str(clone)], output="clone.log")
    execute(["git", "checkout", "--detach", args.revision], cwd=clone, output="checkout.log")
    candidate = execute(["git", "rev-parse", "HEAD"], cwd=clone).decode().strip()
    initial_status = execute(["git", "status", "--porcelain"], cwd=clone).decode()
    check("Clone is clean and exactly the named full candidate", candidate == args.revision and initial_status == "")
    tree = execute(["git", "rev-parse", "HEAD:stage-1"], cwd=clone).decode().strip()
    source = {file: sha((clone / "stage-1" / file).read_bytes()) for file in files}
    unchanged = {}
    for file in files[1:]:
        old = execute(["git", "show", original + ":stage-1/" + file])
        unchanged[file] = {"original_sha256": sha(old), "candidate_sha256": source[file],
                           "unchanged": old == (clone / "stage-1" / file).read_bytes()}
        check("Interface runtime file unchanged: " + file, unchanged[file]["unchanged"])
    parsed_core = ast.parse((clone / "stage-1/core.py").read_text())
    constructor = next(n for n in ast.walk(parsed_core) if isinstance(n, ast.ClassDef) and n.name == "Engine")
    constructor = next(n for n in constructor.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    setup = [n for n in ast.walk(constructor) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and isinstance(n.func.value, ast.Name) and n.func.value.id == "sys"
             and n.func.attr == "set_int_max_str_digits"]
    check("Engine construction explicitly initializes decimal conversion", len(setup) == 1 and
          len(setup[0].args) == 1 and isinstance(setup[0].args[0], ast.Constant) and setup[0].args[0].value == 0)
    for file in ("server.py", "core.py"):
        ast.parse((clone / "stage-1" / file).read_text())
    (out / "source-proof.json").write_text(json.dumps({
        "candidate": candidate, "stage1_tree": tree, "clone": str(clone), "initial_status": initial_status,
        "source_sha256": source, "original_runtime_revision": original, "runtime_comparison": unchanged,
        "probe_revision": probe_revision,
        "probe_sha256": {p: sha((ROOT / "evidence/interface-engineer" / p).read_bytes()) for p in
                         ("stage-1-candidate-5-probe.py", "stage-1-transport-probe.py", "stage-1-candidate-5-container-check.py")},
        "static_boundary": "Engine() argument is evaluated before Server constructs its listener; decimal setting is in Engine.__init__",
        "syntax": "Both service files parsed using ast without executing host service imports",
        "source_inputs": "Complete seven-part assignment/spec/brief/guide, recorded timestamp/receipt decisions, own previous probes and exact current runtime; supplied independent failure descriptions only. No independent probe implementation read/copied."}, indent=2) + "\n")
    legacy_context.mkdir()
    legacy_hashes = {}
    for file in files:
        data = execute(["git", "show", legacy_revision + ":stage-1/" + file])
        (legacy_context / file).write_bytes(data)
        legacy_hashes[file] = sha(data)
    execute(["docker", "build", "-t", image, str(clone / "stage-1")], output="build-current.log")
    execute(["docker", "build", "-t", legacy_image, str(legacy_context)], output="build-legacy.log")
    execute(["docker", "network", "create", "--internal", network], output="network.log")
    created_network = True
    for label, tag, port, host, override, hashes in (
        ("source", image, 8080, 18225, False, source),
        ("destination", image, 9090, 18226, True, source),
        ("legacy", legacy_image, 8080, 18227, False, legacy_hashes),
    ):
        name = slug + "-" + label
        command = ["docker", "run", "-d", "--name", name, "--network", network,
                   "--cpus", "2", "--memory", "2g", "-p", str(host) + ":" + str(port)]
        if override:
            command += ["-e", "PORT=" + str(port)]
        launch = time.monotonic()
        execute(command + [tag], output="run-" + label + ".log")
        created_containers.append(name)
        ready = json.loads(execute(["docker", "exec", name, "python", "-c", health_code, str(port)],
                                  output="health-" + label + ".json"))
        elapsed = time.monotonic() - launch
        check(label + " healthy within 60 seconds of launch", elapsed < 60 and ready["status"] == 200)
        inspection = json.loads(execute(["docker", "inspect", name]))[0]
        actual_hashes = execute(["docker", "exec", name, "python", "-c", hash_code], output="hash-" + label + ".jsonl")
        actual_hashes = json.loads(actual_hashes.decode().splitlines()[0])
        check(label + " image core/server match named source", all(actual_hashes[f] == hashes[f] for f in ("core.py", "server.py")))
        config = inspection["HostConfig"]
        check(label + " constrained to 2 CPU and 2 GiB without mounts", config["NanoCpus"] == 2000000000 and
              config["Memory"] == 2147483648 and inspection["Mounts"] == [])
        listen_code = "import pathlib;print(pathlib.Path('/proc/net/tcp').read_text())"
        listener = execute(["docker", "exec", name, "python", "-c", listen_code], output="listener-" + label + ".txt").decode()
        check(label + " all-interface listener matches selected PORT", "00000000:" + f"{port:04X}" in listener)
        resources.append({"name": name, "label": label, "port": port, "host_port": host,
                          "port_override": override, "image": inspection["Image"], "env": inspection["Config"]["Env"],
                          "nano_cpus": config["NanoCpus"], "memory_bytes": config["Memory"], "mounts": inspection["Mounts"],
                          "network_mode": config["NetworkMode"], "health_from_launch_seconds": elapsed,
                          "runtime_hashes": actual_hashes})
    inspection = json.loads(execute(["docker", "network", "inspect", network]))[0]
    check("Service network has no outbound routing", inspection["Internal"] is True)
    inherited_bytes = (ROOT / "evidence/interface-engineer/stage-1-transport-probe.py").read_bytes()
    inherited = execute(["docker", "exec", "-i", created_containers[1], "python", "-", "http://127.0.0.1:9090"],
                        stdin=inherited_bytes, output="inherited-http.json", require=False)
    inherited = json.loads(inherited)
    check("Own inherited transport/concurrency/time checks pass", inherited["failed"] == 0)
    urls = ["http://" + created_containers[i] + (":9090" if i == 1 else ":8080") for i in range(3)]
    runner = slug + "-client"
    decimal_bytes = (ROOT / "evidence/interface-engineer/stage-1-candidate-5-probe.py").read_bytes()
    # The client also has constrained resources, but shares no interpreter with
    # any service. No mount is required: stdin carries only own probe source.
    decimal = execute(["docker", "run", "--rm", "-i", "--name", runner, "--network", network,
                       "--cpus", "2", "--memory", "2g", "--entrypoint", "python", image, "-", *urls],
                      stdin=decimal_bytes, output="decimal-legacy-http.json", require=False)
    decimal = json.loads(decimal)
    check("Own decimal/legacy checks pass", decimal["failed"] == 0)
    final_status = execute(["git", "status", "--porcelain"], cwd=clone).decode()
    check("Exact candidate clone remains clean after build/checks", final_status == "")
    (out / "summary.json").write_text(json.dumps({"candidate": candidate, "probe_revision": probe_revision,
        "stage1_tree": tree, "clone_status": final_status,
        "inherited": {k: inherited[k] for k in ("checks", "passed", "failed", "elapsed_seconds")},
        "decimal_legacy": {k: decimal[k] for k in ("operations", "assertions", "passed", "failed", "elapsed_seconds", "giant_digits")},
        "runtime_checks": checks}, indent=2) + "\n")
except Exception as exc:
    errors.append(type(exc).__name__ + ": " + str(exc))
finally:
    cleanup = []
    for name in reversed(created_containers):
        execute(["docker", "logs", name], output="logs-" + name.rsplit("-", 1)[1] + ".txt", require=False)
        execute(["docker", "rm", "-f", name], output="cleanup-" + name.rsplit("-", 1)[1] + ".log", require=False)
        cleanup.append(commands[-1])
    if created_network:
        execute(["docker", "network", "rm", network], output="cleanup-network.log", require=False)
        cleanup.append(commands[-1])
    if legacy_context.exists():
        shutil.rmtree(legacy_context)
    if any(row["returncode"] != 0 for row in cleanup):
        errors.append("Own resource cleanup returned a nonzero status")
    elapsed = time.monotonic() - start
    (out / "run.json").write_text(json.dumps({"candidate": args.revision, "legacy_source": legacy_revision,
        "commands": commands, "resources": resources, "checks": checks, "errors": errors,
        "cleanup": cleanup, "elapsed_seconds": elapsed, "clone": str(clone),
        "image_tags_retained": [image, legacy_image], "model": "operator-configured gpt-6.1-sol",
        "runtime_override_effort_usage_cost": "unknown", "build_cache": "Available Docker cache permitted; see actual build logs"}, indent=2) + "\n")
    print(json.dumps({"candidate": args.revision, "out": str(out), "elapsed_seconds": elapsed,
                      "checks": len(checks), "failures": errors}))
sys.exit(1 if errors else 0)
