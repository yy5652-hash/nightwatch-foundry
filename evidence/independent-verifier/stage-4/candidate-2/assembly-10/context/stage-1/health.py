"""Independent network health client; does not run inside the product process."""
import argparse
import json
import time
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("--url", required=True)
p.add_argument("--timeout", type=float, default=57)
a = p.parse_args()
began = time.monotonic()
attempts = 0
errors = []
while time.monotonic() - began < a.timeout:
    attempts += 1
    try:
        with urllib.request.urlopen(a.url, timeout=min(1, max(0.1, a.timeout-(time.monotonic()-began)))) as r:
            status, value = r.status, json.load(r)
        if status == 200 and value == {"status": "ok"}:
            print(json.dumps(dict(url=a.url, status=status, body=value, elapsed_seconds=time.monotonic()-began, attempts=attempts)))
            raise SystemExit(0)
    except Exception as e:
        errors.append(str(e))
    time.sleep(0.1)
print(json.dumps(dict(url=a.url, elapsed_seconds=time.monotonic()-began, attempts=attempts, last_error=errors[-1] if errors else "wrong health body")))
raise SystemExit(1)
