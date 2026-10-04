#!/usr/bin/env python3
"""Reproducible exact-revision clone/runtime evidence; no production edits.

Review the saved preflight/RUN.md before invoking this script with --execute.
This builds the documented Dockerfile, uses a private internal network, and runs
default/override PORT containers. Clients execute INSIDE the internal Docker
network, without assuming host port bindings are reachable. Official harness
remains an unchanged, separate command.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--workspace", required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--keep-running", action="store_true")
    p.add_argument("--run-probes", action="store_true")
    a = p.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", a.candidate):
        p.error("--candidate requires a full commit revision")
    workspace = Path(a.workspace).resolve()
    source = Path(a.repo).resolve()
    out = Path(a.out).resolve()
    if workspace not in source.parents or workspace not in out.parents:
        p.error("repository and output must be inside task workspace")
    out.mkdir(parents=True, exist_ok=False)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S")
    prefix = f"independent-verifier-s1-{a.candidate[:12]}-{stamp}".lower()
    clone = workspace / "band-work" / prefix
    log = []

    def run(command, cwd=None):
        start = time.monotonic()
        with (out / (f"command-{len(log):03}.log")).open("w") as f:
            proc = subprocess.run(command, cwd=cwd or workspace, stdout=f, stderr=subprocess.STDOUT)
        log.append(dict(command=command, cwd=str(cwd or workspace), returncode=proc.returncode,
                        duration_seconds=time.monotonic()-start, log=f"command-{len(log):03}.log"))
        (out / "commands.json").write_text(json.dumps(log, indent=2))
        if proc.returncode:
            raise RuntimeError(f"Command failed ({proc.returncode}): {command}; see {out}")

    run(["git", "clone", "--no-hardlinks", "--no-checkout", str(source), str(clone)])
    run(["git", "checkout", "--detach", a.candidate], clone)
    run(["git", "status", "--porcelain=v1"], clone)
    run(["git", "log", "--format=%H %an <%ae> %s", "--all"], clone)
    run(["git", "ls-tree", "-r", a.candidate], clone)
    stage = clone / "stage-1"
    run_doc = (stage / "RUN.md").read_text()
    (out / "RUN-reviewed-source.md").write_text(run_doc)
    tree_issues = []
    for path in stage.rglob("*"):
        if path.name == ".git" or path.name == ".gitmodules":
            tree_issues.append(str(path))
        if path.is_symlink():
            tree_issues.append(str(path))
    preflight = dict(candidate=a.candidate, clone=str(clone), output=str(out),
                     runtime_prefix=prefix, tree_issues=tree_issues,
                     harness="Codex", configured_model="gpt-6.1-sol", actual_model="unknown", effort="unknown",
                     usage="unknown", billed_spend="unknown", verdict="unverified",
                     note="Review commit history, RUN.md and tree before executing checks.")
    (out / "preflight.json").write_text(json.dumps(preflight, indent=2))
    if tree_issues:
        raise RuntimeError("Clone contains forbidden nested Git metadata/symlinks")
    if not a.execute:
        print(json.dumps(preflight))
        return
    network = prefix + "-net"
    image = prefix + ":candidate"
    runner_image = prefix + ":probe-runner"
    containers = []
    created_network = False
    try:
        run(["docker", "build", "-t", image, "."], stage)
        run(["docker", "build", "-f", "Candidate5.Probe.Dockerfile", "-t", runner_image, "."], Path(__file__).parent.resolve())
        run(["docker", "network", "create", "--internal", network])
        created_network = True
        for name, host_port, container_port, override in [(prefix + "-source", 18300, 18309, True), (prefix + "-peer", 18301, 8080, False)]:
            cmd = ["docker", "run", "-d", "--name", name, "--network", network, "--cpus", "2", "--memory", "2g", "-p", f"127.0.0.1:{host_port}:{container_port}"]
            if override:
                cmd += ["-e", "PORT=18309"]
            cmd.append(image)
            began = time.monotonic()
            run(cmd)
            containers.append(name)
            # The health client reaches the service over its container interface,
            # so a 127.0.0.1-only product listener cannot pass this probe.
            run(["docker", "run", "--rm", "--name", name + "-health", "--network", network,
                 "--cpus", "2", "--memory", "2g", "--entrypoint", "python", runner_image, "/verifier/health.py",
                 "--url", f"http://{name}:{container_port}/health", "--timeout", "57"])
            readiness = time.monotonic()-began
            healthy = readiness < 60
            preflight[name] = dict(healthy=healthy, readiness_seconds=readiness,
                                   host_port=host_port, internal_port=container_port, port_override=override)
            run(["docker", "inspect", name])
            if not healthy:
                run(["docker", "logs", name])
                raise RuntimeError(f"Container did not become healthy within 60s: {name}")
        run(["docker", "network", "inspect", network])
        preflight.update(image=image, runner_image=runner_image, network=network, containers=containers, runtime_started=True,
                         client_execution="inside internal Docker network",
                         probe_command=["docker", "run", "--rm", "--name", prefix + "-probes", "--network", network,
                                        "--cpus", "2", "--memory", "2g", "-v", str(out) + ":/evidence", runner_image,
                                        "--base", f"http://{containers[0]}:18309", "--peer", f"http://{containers[1]}:8080",
                                        "--candidate", a.candidate, "--out", "/evidence/probes"])
        (out / "preflight.json").write_text(json.dumps(preflight, indent=2))
        if a.run_probes:
            run(preflight["probe_command"])
        print(json.dumps(preflight))
    finally:
        if not a.keep_running:
            for name in containers:
                run(["docker", "rm", "-f", name])
            if created_network:
                run(["docker", "network", "rm", network])
        (out / "preflight.json").write_text(json.dumps(preflight, indent=2))


if __name__ == "__main__":
    main()
