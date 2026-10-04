"""Fresh exact-candidate offline single-container boundary audit, with cleanup."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--repo", required=True)
p.add_argument("--workspace", required=True)
p.add_argument("--candidate", required=True)
p.add_argument("--out", required=True)
a = p.parse_args()
repo, workspace, out = Path(a.repo).resolve(), Path(a.workspace).resolve(), Path(a.out).resolve()
assert out.is_relative_to(workspace) and repo.is_relative_to(workspace)
out.mkdir(parents=True, exist_ok=False)
prefix = "independent-verifier-s1-numeric-"+time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()).lower()
clone = workspace/"band-work"/prefix
image, name = prefix+":service", prefix+"-service"
commands = []
service_started = False


def execute(argv, filename, cwd=repo, stdin=None, required=True):
    began = time.monotonic()
    with (out/filename).open("w") as stream:
        completed = subprocess.run(argv, input=stdin, text=True, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
    commands.append(dict(argv=argv, cwd=str(cwd), log=filename, returncode=completed.returncode, duration_seconds=time.monotonic()-began))
    (out/"commands.json").write_text(json.dumps(commands, indent=2))
    if required and completed.returncode:
        raise RuntimeError("Command failed; see "+str(out/filename))
    return completed.returncode


try:
    execute(["git", "clone", "--no-hardlinks", "--no-checkout", str(repo), str(clone)], "clone.log")
    execute(["git", "checkout", "--detach", a.candidate], "checkout.log", cwd=clone)
    execute(["git", "status", "--porcelain=v1"], "status.log", cwd=clone)
    assert not (out/"status.log").read_text()
    execute(["docker", "build", "-t", image, "."], "build.log", cwd=clone/"stage-1")
    began = time.monotonic()
    execute(["docker", "run", "-d", "--name", name, "--network", "none", "--cpus", "2", "--memory", "2g", "-e", "PORT=18320", image], "start.log")
    service_started = True
    health = "import urllib.request,time; deadline=time.monotonic()+55\nwhile True:\n try:\n  r=urllib.request.urlopen('http://127.0.0.1:18320/health',timeout=2); assert r.status==200; print(r.read().decode()); break\n except Exception:\n  if time.monotonic()>deadline: raise\n  time.sleep(.05)"
    execute(["docker", "exec", name, "python", "-c", health], "health.log")
    readiness = time.monotonic()-began
    execute(["docker", "inspect", name], "inspect.json")
    inspect = json.loads((out/"inspect.json").read_text())[0]
    assert inspect["HostConfig"]["NanoCpus"] == 2000000000
    assert inspect["HostConfig"]["Memory"] == 2147483648
    assert inspect["HostConfig"]["NetworkMode"] == "none" and not inspect["Mounts"]
    expected = {filename: hashlib.sha256((clone/"stage-1"/filename).read_bytes()).hexdigest() for filename in ["core.py", "server.py"]}
    hash_code = "import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['core.py','server.py']}))"
    execute(["docker", "exec", name, "python", "-c", hash_code], "image-hashes.json")
    observed = json.loads((out/"image-hashes.json").read_text())
    assert observed == expected
    (out/"identity.json").write_text(json.dumps(dict(candidate=a.candidate, clone=str(clone), clean=True, cpu=2, memory_bytes=2147483648,
                                                    network="none", port=18320, startup_seconds=readiness, expected_hashes=expected, observed_hashes=observed), indent=2))
    source = (repo/"evidence/independent-verifier/stage-1/numeric_forms_current.py").read_text()
    (out/"numeric_forms_current.py").write_text(source)
    (out/"client-source-proof.json").write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),stdin_source="numeric_forms_current.py"),indent=2))
    code = execute(["docker", "exec", "-i", name, "python", "-", "http://127.0.0.1:18320", a.candidate], "probes.json", stdin=source, required=False)
    result = json.loads((out/"probes.json").read_text())
    print(json.dumps({key:result[key] for key in ["candidate_full_revision", "http_operations", "assertions", "failed_assertions", "duration_seconds"]}))
finally:
    if service_started:
        execute(["docker", "logs", name], "service.log", required=False)
        execute(["docker", "rm", "-f", name], "cleanup.log")
raise SystemExit(code)
