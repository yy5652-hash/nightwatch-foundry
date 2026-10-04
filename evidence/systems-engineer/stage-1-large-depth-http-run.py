"""Constrained independent services and a state-decoder-free wire client."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument("--image", required=True)
parser.add_argument("--candidate", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
repo = Path.cwd().resolve()
out = Path(args.out).resolve()
out.relative_to(repo / "evidence/systems-engineer")
out.mkdir(exist_ok=False)
program = (repo / "evidence/systems-engineer/stage-1-large-depth-http-client.py").read_bytes()
(out / "executed-client.py").write_bytes(program)
prefix = "systems-engineer-deep-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f").lower()
network = prefix + "-net"
record = {"candidate": args.candidate, "image_id": args.image, "commands": [], "services": [], "cleanup": [],
          "client_sha256": hashlib.sha256(program).hexdigest()}
created, network_created = [], False
started = time.monotonic()


def run(argv, body=None, required=True, timeout=60):
    begin = time.monotonic()
    result = subprocess.run(argv, input=body, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    log = out / ("command-%03d.log" % len(record["commands"]))
    log.write_bytes(result.stdout)
    record["commands"].append({"argv": argv, "returncode": result.returncode, "seconds": time.monotonic() - begin,
                               "log": str(log), "stdin_sha256": None if body is None else hashlib.sha256(body).hexdigest()})
    if required and result.returncode:
        raise RuntimeError("Own command failed: " + str(log))
    return result


try:
    expected = {name: hashlib.sha256(run(["git", "show", args.candidate + ":stage-1/" + name]).stdout).hexdigest()
                for name in ("core.py", "server.py", "json_codec.py")}
    run(["docker", "network", "create", "--internal", network])
    network_created = True
    for index, port in enumerate((18161, 18162)):
        name = prefix + "-" + str(index)
        beginning = time.monotonic()
        run(["docker", "run", "-d", "--name", name, "--network", network, "--cpus", "2", "--memory", "2g", "-e", "PORT=" + str(port), args.image])
        created.append(name)
        run(["docker", "exec", name, "python", "-c",
             "import time,urllib.request\nfor i in range(200):\n try:\n  assert urllib.request.urlopen('http://127.0.0.1:%d/health',timeout=1).status==200\n  break\n except Exception:time.sleep(.05)\nelse:raise RuntimeError('health')" % port])
        inspect = json.loads(run(["docker", "inspect", name]).stdout)[0]
        assert inspect["Image"] == args.image and inspect["Mounts"] == []
        assert inspect["HostConfig"]["NanoCpus"] == 2000000000 and inspect["HostConfig"]["Memory"] == 2147483648
        actual = json.loads(run(["docker", "exec", name, "python", "-c",
                                "import hashlib,json;print(json.dumps({n:hashlib.sha256(open('/app/'+n,'rb').read()).hexdigest() for n in ('core.py','server.py','json_codec.py')}))"]).stdout)
        assert actual == expected
        record["services"].append({"name": name, "port": port, "startup_seconds": time.monotonic() - beginning,
                                   "source_sha256": actual, "image_id": inspect["Image"],
                                   "cpu": 2, "memory_bytes": 2147483648, "mounts": [], "offline_internal_network": network})
    client = prefix + "-client"
    run(["docker", "create", "-i", "--name", client, "--network", network, "--cpus", "2", "--memory", "2g", "--entrypoint", "python", args.image,
         "-X", "faulthandler", "-B", "-", "http://" + created[0] + ":18161", "http://" + created[1] + ":18162", "/tmp/systems-engineer-deep-http.json"])
    created.append(client)
    result = run(["docker", "start", "-a", "-i", client], program, required=False)
    record["client_exit_code"] = result.returncode
    run(["docker", "cp", client + ":/tmp/systems-engineer-deep-http.json", str(out / "probe.json")])
    record["summary"] = json.loads((out / "probe.json").read_text())["summary"]
    record["states_after_probe"] = {name: json.loads(run(["docker", "inspect", name]).stdout)[0]["State"] for name in created}
except Exception as error:
    record["runner_exception"] = {"type": type(error).__name__, "message": str(error)}
finally:
    for name in reversed(created):
        result = run(["docker", "rm", "-f", name], required=False)
        record["cleanup"].append({"name": name, "returncode": result.returncode})
    if network_created:
        result = run(["docker", "network", "rm", network], required=False)
        record["cleanup"].append({"name": network, "returncode": result.returncode})
    record["wall_seconds"] = time.monotonic() - started
    (out / "runtime.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"summary": record.get("summary"), "runner_exception": record.get("runner_exception"), "wall_seconds": record["wall_seconds"]}))
    raise SystemExit(bool(record.get("runner_exception") or record.get("summary", {}).get("failed", 1)))
