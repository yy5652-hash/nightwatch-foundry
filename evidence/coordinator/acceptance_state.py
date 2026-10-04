"""Read append-only stage acceptance and revocation records."""
import hashlib
import json
from pathlib import Path

ACCEPTED = Path(__file__).parent / "accepted"
RESULT = Path(__file__).resolve().parents[2]


def manifests():
    return [(p, json.loads(p.read_text())) for p in sorted(ACCEPTED.glob("stage-*.json"))]


def revocations():
    return [(p, json.loads(p.read_text())) for p in sorted(ACCEPTED.glob("revoked-stage-*.json"))]


def current_manifests():
    latest = {}
    revoked = {(d["stage"], d["candidate_full_revision"]) for _, d in revocations()}
    for p, d in manifests():
        if d["stage"] not in latest or d["freeze_wall_time_utc"] > latest[d["stage"]][1]["freeze_wall_time_utc"]:
            latest[d["stage"]] = (p, d)
    return [latest[n] for n in sorted(latest) if (n, latest[n][1]["candidate_full_revision"]) not in revoked]


def verify_history():
    for _, d in manifests():
        p = RESULT / d["independent_verdict_path"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != d["independent_verdict_sha256"]:
            raise ValueError("Historical acceptance verdict changed or disappeared")
    for _, d in revocations():
        for path_key, digest_key in (("original_manifest_path", "original_manifest_sha256"),
                                     ("independent_verdict_path", "independent_verdict_sha256")):
            p = RESULT / d[path_key]
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != d[digest_key]:
                raise ValueError("Historical revocation evidence changed or disappeared")

