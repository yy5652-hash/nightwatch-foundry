"""Reproduce rejected closure classification over HTTP in our retained image."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

repo = Path.cwd()
out = repo / 'evidence/systems-engineer/systems-engineer-s4-repair1-reproduction-01'
out.mkdir(exist_ok=False)
probe = repo / 'evidence/systems-engineer/stage-4-repair1-closure-probes.py'
name = 'systems-engineer-s4-repro-' + datetime.now(timezone.utc).strftime('%H%M%S%f')
image = 'sha256:934973ca96214e3ce4ca5bfeb26be956724e66550e7a577236654e81552aada2'
record = {'started_utc': datetime.now(timezone.utc).isoformat(), 'commands': [],
          'candidate': '261e4d9456a04a8b57ed46db71a09ac267ff15a9', 'fresh_build': False,
          'service_image': image, 'method': 'actual HTTP; client runs via docker exec in the constrained service',
          'probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest()}
began = time.monotonic()

def run(argv, data=None):
    start = time.monotonic()
    result = subprocess.run(argv, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = 'command-%02d' % len(record['commands'])
    (out / (log + '.stdout')).write_bytes(result.stdout)
    (out / (log + '.stderr')).write_bytes(result.stderr)
    record['commands'].append({'argv': argv, 'exit': result.returncode, 'seconds': time.monotonic()-start, 'log': log})
    return result

created = False
try:
    assert run(['docker', 'run', '-d', '--name', name, '--network', 'none', '--cpus', '2', '--memory', '2g', image]).returncode == 0
    created = True
    health = "import time,urllib.request\nfor i in range(100):\n try:\n  assert urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=.5).status==200\n  break\n except Exception:time.sleep(.05)\nelse:raise RuntimeError('health')"
    assert run(['docker', 'exec', name, 'python', '-c', health]).returncode == 0
    info = json.loads(run(['docker', 'inspect', name]).stdout)[0]
    assert info['HostConfig']['NanoCpus'] == 2000000000 and info['HostConfig']['Memory'] == 2147483648
    assert info['Mounts'] == [] and info['HostConfig']['NetworkMode'] == 'none'
    record['constraints'] = {'cpu': 2, 'memory_bytes': 2147483648, 'mounts': [], 'network': 'none'}
    source = run(['docker', 'exec', name, 'python', '-c', "import hashlib;print(hashlib.sha256(open('/app/core.py','rb').read()).hexdigest())"]).stdout.decode().strip()
    expected = run(['git', 'show', record['candidate'] + ':stage-4/core.py']).stdout
    assert source == hashlib.sha256(expected).hexdigest()
    record['packaged_core_sha256'] = source
    executed = run(['docker', 'exec', '-i', name, 'python', '-'], probe.read_bytes())
    trace = json.loads(executed.stdout)
    assert executed.returncode == 1 and trace['summary']['failed'] == 24
    failures = [row for row in trace['assertions'] if not row['passed']]
    assert len(failures) == 24 and all(row['label'].endswith(('-status', '-code')) for row in failures)
    record['result'] = 'reproduced twelve wrong-type cases; 24 status/code assertions fail as expected'
    record['summary'] = trace['summary']
    (out / 'trace.json').write_text(json.dumps(trace, indent=2) + '\n')
    (out / 'executed-probe.py').write_bytes(probe.read_bytes())
finally:
    if created:
        cleanup = run(['docker', 'rm', '-f', name])
        record['cleanup_exit'] = cleanup.returncode
    record['finished_utc'] = datetime.now(timezone.utc).isoformat()
    record['wall_seconds'] = time.monotonic()-began
    (out / 'runtime.json').write_text(json.dumps(record, indent=2)+'\n')
    (out / 'executed-driver.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({key: record.get(key) for key in ('result', 'summary', 'cleanup_exit', 'wall_seconds')}))
