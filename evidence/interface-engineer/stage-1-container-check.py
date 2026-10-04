"""Build and probe the Stage 1 container, retaining unique evidence directories."""

import datetime
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN = ROOT / "evidence" / "interface-engineer" / ("interface-engineer-s1-" + STAMP)
RUN.mkdir()
IMAGE = "interface-engineer-tablekeeper-s1:" + STAMP.lower()
CONTAINER = "interface-engineer-tablekeeper-s1-" + STAMP.lower()
COMMANDS = []
START = time.monotonic()


def execute(command, filename, input_bytes=None):
    COMMANDS.append(command)
    with (RUN / filename).open("wb") as output:
        result = subprocess.run(command, input=input_bytes, stdout=output, stderr=subprocess.STDOUT)
    return result.returncode


revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "stage-1"], cwd=ROOT, text=True).strip()
code = execute(["docker", "build", "-t", IMAGE, str(ROOT / "stage-1")], "build.log")
try:
    if code == 0:
        code = execute(["docker", "run", "-d", "--name", CONTAINER, "--network", "none", "--cpus", "2", "--memory", "2g",
                        "-e", "PORT=9090", IMAGE], "start.log")
    if code == 0:
        code = execute(["docker", "exec", "-i", CONTAINER, "python", "-", "http://127.0.0.1:9090"], "probe.json",
                       (ROOT / "evidence" / "interface-engineer" / "stage-1-transport-probe.py").read_bytes())
        execute(["docker", "inspect", "--format", "{{json .HostConfig}}", CONTAINER], "container-limits.json")
        execute(["docker", "logs", CONTAINER], "service.log")
finally:
    # Only this invocation's uniquely named container is removed.
    execute(["docker", "rm", "-f", CONTAINER], "cleanup.log")
    metadata = {"started_at": STAMP, "base_revision": revision, "stage_1_dirty": bool(dirty),
                "elapsed_seconds": round(time.monotonic() - START, 4), "exit_code": code,
                "image": IMAGE, "container": CONTAINER, "commands": COMMANDS,
                "harness": "Codex", "operator_model": "gpt-6.1-sol", "runtime_override": "unknown",
                "effort": "unknown", "token_usage": "unknown", "catalog_estimated_cost_usd": "unknown"}
    (RUN / "run.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (ROOT / "evidence" / "interface-engineer" / "ledger.jsonl").open("a") as ledger:
        ledger.write(json.dumps({**metadata, "evidence_path": str(RUN.relative_to(ROOT))}) + "\n")
print(json.dumps({"evidence": str(RUN), "exit_code": code, "elapsed_seconds": metadata["elapsed_seconds"]}))
sys.exit(code)
