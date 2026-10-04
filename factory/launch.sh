#!/bin/zsh
# The commands the operator ran to start the scored run on 2026-10-04 (UTC).
# R is the empty result repository, M the directory holding the four mandate files,
# HUMAN the operator's Band participant id. Nothing else was sent to the room.
set -euo pipefail
R=${R:?result repository}; M=${M:?mandates directory}; HUMAN=${HUMAN:?human participant id}; OWNER=${OWNER:?band handle owner}
cd "$R"
mk() { band agent create --name "$1" --description "$3" --cwd "$R" --session "nw-final-$2" \
         --transport codex-app-server --runtime-auth subscription --runtime-model gpt-6.1-sol \
         --runtime-effort xhigh --runtime-approval never --runtime-sandbox danger-full-access \
         --no-spawn-sandbox --instructions-stdin < "$M/$2.md"; }
mk "Foundry Coordinator" foundry-coordinator "Lead seat: plans, delegates, integrates and reports; does not implement alone"
mk "Systems Engineer" systems-engineer "Builder seat: integrity-critical service behavior"
mk "Interface Engineer" interface-engineer "Builder seat: user-facing and integration surface"
mk "Independent Verifier" independent-verifier "Review seat: independent specification-derived verification; may reject"

ROOM=$(band chat new --as $OWNER/foundry-coordinator | grep -oE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1)
for member in $OWNER/systems-engineer $OWNER/interface-engineer $OWNER/independent-verifier $HUMAN; do
  band chat add --as $OWNER/foundry-coordinator $ROOM $member || true
done
LEAD=$(band room participants $ROOM | grep foundry-coordinator | grep -oE 'id=[0-9a-f-]+' | cut -d= -f2)
band room send $ROOM "$(cat "$(dirname "$0")/dispatch-tablekeeper.md")" --mention $LEAD   # the only human message
