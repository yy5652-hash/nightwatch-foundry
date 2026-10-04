"""Repeat only the corrected large-minute probe in two fresh current processes."""
import json
import subprocess
import sys
import time
from pathlib import Path

out, repo = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
metadata = json.loads((out/"preflight.json").read_text())
prefix = metadata["runtime_prefix"]
assert prefix.startswith("independent-verifier-")
commands = []


def execute(command, log, stdin=None):
    began = time.monotonic()
    with (out/log).open("w") as stream:
        result = subprocess.run(command, input=stdin, text=True, cwd=repo, stdout=stream, stderr=subprocess.STDOUT)
    commands.append(dict(command=command, cwd=str(repo), log=log, returncode=result.returncode, duration_seconds=time.monotonic()-began))
    (out/"extra-commands.json").write_text(json.dumps(commands, indent=2))
    return result.returncode


try:
    source = (repo/"evidence/independent-verifier/stage-1/large_minutes.py").read_text()
    code = execute(["docker", "exec", "-i", metadata["containers"][0], "python", "-", "http://127.0.0.1:18309", metadata["candidate"],
                    "http://"+metadata["containers"][1]+":8080"], "large-minutes.json", source)
finally:
    for name in metadata["containers"]:
        assert name.startswith(prefix)
        execute(["docker", "rm", "-f", name], name+"-cleanup.log")
    assert metadata["network"].startswith(prefix)
    execute(["docker", "network", "rm", metadata["network"]], "network-cleanup.log")
result = json.loads((out/"large-minutes.json").read_text())
print(json.dumps({k:result[k] for k in ["http_operations", "assertions", "failed_assertions", "duration_seconds"]}))
raise SystemExit(code)
