"""Execute repair reproductions and calendar probes in the owned runtime."""
import json
import subprocess
import sys
import time
from pathlib import Path

out = Path(sys.argv[1]).resolve()
metadata = json.loads((out / "preflight.json").read_text())
prefix = metadata["runtime_prefix"]
assert prefix.startswith("independent-verifier-")
commands = []


def execute(command, log):
    began = time.monotonic()
    with (out / log).open("w") as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
    commands.append(dict(command=command, returncode=result.returncode, duration_seconds=time.monotonic()-began, log=log))
    (out / "extra-commands.json").write_text(json.dumps(commands, indent=2))
    return result.returncode


try:
    if "--race50" in sys.argv[2:]:
        execute(["docker", "build", "-f", str(Path(__file__).resolve().parent / "Probe.Dockerfile"), "-t", metadata["runner_image"], str(Path(__file__).resolve().parent)], "runner-refresh.log")
    scripts = [("race50.py", "race50")] if "--race50" in sys.argv[2:] else [("reproduce_calendar.py", "calendar-minimal")] if "--calendar-minimal" in sys.argv[2:] else [("reproduce.py", "reproductions"), ("calendar_edges.py", "calendar")]
    for script, label in scripts:
        cmd = ["docker", "run", "--rm", "--name", prefix+"-"+label, "--network", metadata["network"],
               "--cpus", "2", "--memory", "2g", "-v", str(out)+":/evidence", "--entrypoint", "python",
               metadata["runner_image"], "/verifier/"+script, "--base", "http://"+metadata["containers"][0]+":18309",
               "--candidate", metadata["candidate"], "--out", "/evidence/"+label]
        execute(cmd, label+"-client.log")
finally:
    for name in metadata["containers"]:
        assert name.startswith(prefix)
        execute(["docker", "rm", "-f", name], name+"-cleanup.log")
    assert metadata["network"].startswith(prefix)
    execute(["docker", "network", "rm", metadata["network"]], "network-cleanup.log")

print(json.dumps([{k:c[k] for k in ["returncode", "duration_seconds", "log"]} for c in commands]))
