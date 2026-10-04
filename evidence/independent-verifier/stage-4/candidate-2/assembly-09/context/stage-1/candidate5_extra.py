"""Fresh legacy source plus independent regression/concurrency/upgrade clients."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

out = Path(sys.argv[1]).resolve()
repo = Path(sys.argv[2]).resolve()
metadata = json.loads((out / "preflight.json").read_text())
prefix = metadata["runtime_prefix"]
assert prefix.startswith("independent-verifier-")
legacy_revision = "49287b4a5a1481f995c470ccae31776f03d4b863"
legacy_clone = repo.parent / (prefix+"-legacy-clone")
legacy_name = prefix+"-legacy"
legacy_image = prefix+":legacy"
commands = []
legacy_started = False


def execute(command, log, cwd=None, must_pass=False):
    began = time.monotonic()
    with (out / log).open("w") as stream:
        result = subprocess.run(command, cwd=cwd or repo, stdout=stream, stderr=subprocess.STDOUT)
    commands.append(dict(command=command, cwd=str(cwd or repo), returncode=result.returncode,
                          duration_seconds=time.monotonic()-began, log=log))
    (out / "extra-commands.json").write_text(json.dumps(commands, indent=2))
    if must_pass and result.returncode:
        raise RuntimeError("Failed owned-runtime command; see "+str(out / log))
    return result.returncode


try:
    execute(["git", "clone", "--no-hardlinks", "--no-checkout", str(repo), str(legacy_clone)], "legacy-clone.log", must_pass=True)
    execute(["git", "checkout", "--detach", legacy_revision], "legacy-checkout.log", cwd=legacy_clone, must_pass=True)
    execute(["git", "status", "--porcelain=v1"], "legacy-status.log", cwd=legacy_clone, must_pass=True)
    assert not (out / "legacy-status.log").read_text()
    execute(["docker", "build", "-t", legacy_image, "."], "legacy-build.log", cwd=legacy_clone / "stage-1", must_pass=True)
    began = time.monotonic()
    execute(["docker", "run", "-d", "--name", legacy_name, "--network", metadata["network"], "--cpus", "2", "--memory", "2g", "-e", "PORT=18310", "-p", "127.0.0.1:18302:18310", legacy_image], "legacy-start.log", must_pass=True)
    legacy_started = True
    execute(["docker", "run", "--rm", "--name", prefix+"-legacy-health", "--network", metadata["network"], "--entrypoint", "python", metadata["runner_image"], "/verifier/health.py", "--url", "http://"+legacy_name+":18310/health", "--timeout", "57"], "legacy-health.log", must_pass=True)
    readiness = time.monotonic()-began
    execute(["docker", "inspect", legacy_name], "legacy-inspect.json", must_pass=True)
    identity = dict(current_revision=metadata["candidate"], legacy_revision=legacy_revision,
                    legacy_clone=str(legacy_clone), legacy_readiness_seconds=readiness,
                    legacy_clean=True, hash_checks=[])
    for name, clone in [(metadata["containers"][0], Path(metadata["clone"])), (metadata["containers"][1], Path(metadata["clone"])), (legacy_name, legacy_clone)]:
        expected = {file:hashlib.sha256((clone / "stage-1" / file).read_bytes()).hexdigest() for file in ["core.py", "server.py"]}
        command = ["docker", "exec", name, "python", "-c", "import hashlib,json;from pathlib import Path;print(json.dumps({f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in ['core.py','server.py']}))"]
        log = name+"-hash.json"
        execute(command, log, must_pass=True)
        observed = json.loads((out / log).read_text())
        identity["hash_checks"].append(dict(container=name, expected=expected, observed=observed, passed=expected == observed))
        assert expected == observed
    (out / "legacy-identity.json").write_text(json.dumps(identity, indent=2))
    for script, label in [("reproduce.py", "original-minimal"), ("reproduce_calendar.py", "calendar-minimal"), ("race50.py", "race50"), ("legacy_receipts.py", "legacy"), ("decimal_probe.py", "decimal")]:
        command = ["docker", "run", "--rm", "--name", prefix+"-"+label+"-client", "--network", metadata["network"], "--cpus", "2", "--memory", "2g", "-v", str(out)+":/evidence", "--entrypoint", "python", metadata["runner_image"], "/verifier/"+script,
                   "--base", "http://"+metadata["containers"][0]+":18309", "--candidate", metadata["candidate"], "--out", "/evidence/"+label]
        if label in ["legacy", "decimal"]:
            command += ["--peer", "http://"+metadata["containers"][1]+":8080"]
            if label == "legacy":
                command += ["--legacy", "http://"+legacy_name+":18310"]
        execute(command, label+"-client.log")
    execute(["docker", "run", "--rm", "--name", prefix+"-large-minutes-client", "--network", metadata["network"], "--cpus", "2", "--memory", "2g", "--entrypoint", "python", metadata["runner_image"], "/verifier/large_minutes.py", "http://"+metadata["containers"][0]+":18309", metadata["candidate"], "http://"+metadata["containers"][1]+":8080"], "large-minutes.json")
finally:
    for name in metadata["containers"]+([legacy_name] if legacy_started else []):
        assert name.startswith(prefix)
        execute(["docker", "rm", "-f", name], name+"-cleanup.log")
    assert metadata["network"].startswith(prefix)
    execute(["docker", "network", "rm", metadata["network"]], "network-cleanup.log")
print(json.dumps([{k:c[k] for k in ["returncode", "duration_seconds", "log"]} for c in commands]))
