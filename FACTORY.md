# The factory

Nightwatch Foundry is four coding-agent seats in one BAND Desktop room. A human sends one
dispatch; after that the seats plan, build, hand off, review, reject, repair and report among
themselves. The mandates in `mandates/` say how each seat works and never name the problem,
so the same four files can be pointed at a different specification.

This document is written by the operator. Every number in it was measured from the result
repository's Git history, the official harness reports, the room, or the seats' own Codex
session logs; where something could not be measured it says so.

## Seats

| Seat | Mandate | Harness / model | Owns | Never does |
|---|---|---|---|---|
| Foundry Coordinator | `mandates/foundry-coordinator.md` | Codex / `gpt-6.1-sol` | Requirements ledger, stage plan, full-specification handoffs, sequencing of the shared tree, promotion, run ledger, final report | Implement alone; promote without the verifier's verdict |
| Systems Engineer | `mandates/systems-engineer.md` | Codex / `gpt-6.1-sol` | Integrity-critical behaviour: state, transactions, concurrency, idempotency, recovery | Special-case visible tests |
| Interface Engineer | `mandates/interface-engineer.md` | Codex / `gpt-6.1-sol` | The HTTP surface, the browser product, packaging and run instructions, presentation quality | Mask a backend failure with a cosmetic success |
| Independent Verifier | `mandates/independent-verifier.md` | Codex / `gpt-6.1-sol` | A fresh clone of the exact candidate, the official isolated checks, its own specification-derived probes, the verdict | Edit production code; accept a builder's summary as proof |

All four seats ran Codex CLI 0.160.0 with model `gpt-6.1-sol` at reasoning effort `xhigh`
(read from each seat's session log, not assumed from configuration).

## How a stage moves

1. **Handoff.** The coordinator sends each seat the complete task and the full specification
   text as a numbered package (`part i/N`, completion marker). A seat acknowledges every part
   by `@handle` before it starts. A file path alone is not a handoff.
2. **Build.** The two builders work in disjoint paths of one shared working tree and commit
   under their own identity with explicit pathspecs.
3. **Candidate.** The coordinator names one full commit as the candidate.
4. **Independent review.** The verifier clones that exact revision, builds it from its own
   `Dockerfile`, runs the official harness in isolated mode for this stage and every earlier
   one, then runs its own black-box probes derived from the specification: stated
   boundaries, 50-client races, retries, lost responses, export/import upgrades.
5. **Verdict.** `accept`, `reject` or `blocked`, committed with evidence. A rejection goes
   back to the owning builder with the smallest reproducible failure. The verifier re-runs
   the repaired revision itself.
6. **Freeze and carry forward.** An accepted stage folder is frozen; the next stage starts
   as a byte-for-byte copy and is widened.

## Stand it up

Prerequisites: BAND Desktop and its `band` CLI (we used 0.4.12), Codex CLI signed in with a
ChatGPT subscription, Docker, Git, Python 3.12, and a checkout of the kickoff repository.

```sh
# 1. one empty result repository
git init -b main result && cd result

# 2. four seats, each created from its mandate file
for seat in foundry-coordinator systems-engineer interface-engineer independent-verifier; do
  band agent create --name "<Seat Name>" --cwd "$PWD" --session "nw-$seat" \
    --transport codex-app-server --runtime-auth subscription \
    --runtime-model gpt-6.1-sol --runtime-effort xhigh \
    --runtime-approval never --runtime-sandbox danger-full-access --no-spawn-sandbox \
    --instructions-stdin < mandates/$seat.md
done

# 3. one fresh room with the four seats and the human, then exactly one message
room=$(band chat new --as <you>/foundry-coordinator | tail -1)
band chat add --as <you>/foundry-coordinator $room <you>/systems-engineer   # repeat per seat and for the human
band room send $room "$(cat factory/dispatch-tablekeeper.md)" --mention <coordinator participant id>
```

`factory/launch.sh` is the script we actually ran. For a different problem, replace the
dispatch: it is the only task-specific input. It names the workspace, the specification
files, the track, the seats' handles, the port ranges and the time budget.

Two warnings before you copy step 2. `--no-spawn-sandbox` with `danger-full-access` means
the seats run directly on the host with the operator's file permissions. We chose that
deliberately (see below) and confined the seats by instruction, not by isolation: use a
machine or account you are willing to give them.

## Design choices, why, and what they cost

| Choice | Why | What it cost |
|---|---|---|
| A verifier that may block promotion and re-runs everything itself | Shipped checks cover part of each stage; a seat that only reads green checks would promote spec violations | 246 M of 662 M tokens (37 %) and most of the wall-clock time |
| Full specification text inside every handoff | A seat that was told "see the room" builds from a summary | Handoffs of up to 23 parts; 974 text messages in the room |
| Two builders with disjoint ownership (integrity core / interface) | Real parallel work and a natural second reader of every contract | One shared-index incident: an Interface commit without a pathspec on the commit command captured 32 verifier evidence files (`182582c`). Both seats disclosed it; no graded file was affected |
| One shared working tree instead of a clone per seat | Seats see each other's commits immediately; no merge step | Strict pathspec discipline in every mandate, and the incident above |
| Host-native seats, no agent sandbox | Our sandboxed seats could not reach the Docker socket the official harness needs, and repeatedly failed to resume (see "What we tried that failed") | No isolation between seats and host; stated in the dispatch as a rule, not enforced |
| "Probe every untested boundary" in the dispatch, with no severity classes | We wanted code that meets the specification beyond the shipped checks | Stage 1 took 5 h 09 min of the 10 h 39 min. See below |
| One dispatch for all four stages | The run is then dark by construction | Nothing to steer when Stage 1 ran long; we could only watch |

## What happened in the scored run

Dispatch: 2026-10-04 00:12:31 UTC. Final report: 10:51:38 UTC. **10 h 39 min**, one human
message.

| Stage | Accepted (UTC) | Since dispatch | Accepted service revision | Verdict commit |
|---|---|---|---|---|
| 1 | 05:21:32 | 5 h 09 min | `75005d5` | `a22de6b` |
| 2 | 06:36:02 | 6 h 24 min | `4dba102` | `efd23ed` |
| 3 | 08:09:05 | 7 h 57 min | `91e2c47` | `315631a` |
| 4 | 10:42:30 | 10 h 30 min | `5827086` | `91272cb` |

Official checks, run by the operator on a fresh clone of the band's final commit `49bb986`
(`harness run --all --mode isolated`, 2026-10-04 11:40 UTC):

| Folder | Suite 1 | Suite 2 | Suite 3 | Suite 4 | Claims |
|---|---|---|---|---|---|
| `stage-1/` | 120/120 | does not pass | | | stage 1 |
| `stage-2/` | 120/120 | 25/25 | does not pass | | stage 2 |
| `stage-3/` | 120/120 | 25/25 | 7/7 | does not pass | stage 3 |
| `stage-4/` | 120/120 | 25/25 | 7/7 | 6/6 | stage 4 |

"Does not pass" is the required overshoot probe: a folder must not already satisfy the next
stage. These are the shipped checks only; the organisers' full suite decides.

What the band built: a Python 3.12 standard-library service with no third-party runtime
dependency, running as a non-root user in `python:3.12-slim-bookworm`, with a browser
product in plain HTML, CSS and JavaScript packaged in the image.

| Folder | Files | Lines |
|---|---|---|
| `stage-1/` | 6 | 1,415 |
| `stage-2/` | 9 | 2,182 |
| `stage-3/` | 9 | 2,798 |
| `stage-4/` | 9 | 3,385 |

Work split, from `git log`: 381 commits — Foundry Coordinator 133, Independent Verifier 101,
Interface Engineer 78, Systems Engineer 69. Commits that change a `stage-N/` folder: Interface
Engineer 21 (3,442 lines added), Systems Engineer 19 (6,946 lines added). The coordinator and
the verifier made none.

## Measured time and model spend

Token counters are the last cumulative `token_count` each seat's own Codex session log
recorded at or before the final report.

| Seat | Turns | Tokens | Share |
|---|---|---|---|
| Independent Verifier | 203 | 245.9 M | 37 % |
| Foundry Coordinator | 348 | 190.8 M | 29 % |
| Systems Engineer | 126 | 113.8 M | 17 % |
| Interface Engineer | 127 | 111.4 M | 17 % |
| **Total to the final report** | | **662.0 M** | |

Of those, 658.3 M were input tokens, 640.5 M of them (97 %) served from the prompt cache, and
3.7 M were output tokens.

After the final report the coordinator spent another 48 minutes and 113.4 M tokens settling
a backlog of queued inbound messages one at a time, changing nothing. Total including that
tail: 775.4 M tokens.

The room holds 20,512 events: 974 text messages (973 from seats, one from the human),
7,420 tool calls with their 7,420 results, 1,001 thoughts, 3,692 turn markers, four joins and
one error.

**Money.** The seats ran on a ChatGPT subscription, so there is no per-token bill, and we do
not know a list price for `gpt-6.1-sol`. We therefore report tokens and state no dollar
figure. BAND's own `band usage` did not attribute these sessions.

## How it catches and recovers from bad work

Every row below is a commit by the Independent Verifier and the first later commit that
changed that stage's code. All of them happened while the official shipped checks for the
stage were passing.

| UTC | Verdict | Finding | Repair |
|---|---|---|---|
| 00:43 | Reject Stage 1 (`dd64419`) | Boundary cases outside the shipped checks | `49287b4` Systems: represent instants beyond the calendar bounds |
| 00:55 | Reject Stage 1 (`a68a4ef`) | Calendar-edge timestamps serialised wrongly | `f4eeac5` Systems: nearest representable minute offsets, receipts preserved |
| 01:19 | **Revoke** Stage 1 acceptance (`86c7459`) | Valid large minute values failed | `2a4b040` Systems: remove an undocumented ceiling |
| 02:34 | Reject Stage 2 candidate 1 and **revoke** Stage 1 (`fe68f4e`) | 4,301-digit integers failed although the specification states no maximum | `78732dd`, then an exact JSON codec (`00940d4`); Stage 2 rebuilt on it (`c2b4c4b`) |
| 02:59 | Reject Stage 1 candidate 5 (`6c01976`) | Exact numbers in ignored unknown fields | `00940d4` Systems: standalone exact JSON codec |
| 04:35 | Reject Stage 1 candidate 6 (`7db8085`) | Deeply nested valid JSON hit the interpreter's recursion limit | `9e6143b` Systems: decode with an explicit stack |
| 09:16 | Reject Stage 4 (`16b6955`) | A closure request with a wrong JSON type returned the wrong error class, with the official checks at 6/6 | `6225a0e` Systems: validate types before parsing instants |

Mechanisms that made this work:

- **The verdict is tied to a commit.** The verifier names the exact revision and tree it
  cloned; a later commit is a new candidate.
- **An acceptance can be withdrawn.** Twice the verifier found a failure after accepting
  Stage 1 and revoked it in a new commit. The earlier acceptance stays in history.
- **Evidence is append-only.** Rejected candidates, failing probes and corrected
  expectations stay in `evidence/`; nothing is relabelled.
- **Later stages re-prove earlier ones.** Each review re-runs every earlier suite and
  imports state exported by the earlier accepted services.
- **Nobody approves their own work.** Builders hand over a revision with commands and
  results; the coordinator promotes only on the verifier's committed verdict.

## What we tried that failed

- **Sandboxed seats.** Our first factory ran each seat inside BAND's Docker sandbox. The
  seats could not reach the Docker socket the official harness needs, and after restarts the
  runtimes repeatedly failed to resume. A first attempt at the real track on 2026-09-30
  stalled this way and was abandoned. Host-native seats fixed it at the cost of isolation.
- **A room that filled up.** During the practice (`toy`) rehearsal a room stopped accepting
  messages at 1,000. The scored room later held 20,512 events without a refusal, but we
  added "keep the room economical" to every mandate because of it.
- **Unbounded verification depth.** The dispatch asked the verifier to probe every untested
  boundary and gave no way to rank findings. The band spent 5 h 09 min on Stage 1, most of
  it on inputs far outside anything the specification mentions: 4,301-digit integers, JSON
  nested thousands of levels deep, year-1 timestamps. Each finding was real under a literal
  reading and each repair is in the code, but for five hours the factory had no accepted
  stage. Stages 2, 3 and 4 then took 1 h 14 min, 1 h 33 min and 2 h 33 min.
- **The inbound backlog.** Seats queue messages that arrive while they work. The coordinator
  answered its backlog only after the final report: 48 minutes and 113.4 M tokens with no
  effect on the result.

## What we would change next

`factory/next-iteration/` holds revised mandates, still generic, that we prepared during the
run and did not use:

- every finding is **blocking** (violates a quoted requirement inside stated limits, loses
  or corrupts data, breaks later ordinary requests, or fails an official check) or
  **deferred** (reachable only beyond any stated limit); only blocking findings hold
  promotion;
- every stage gets a wall-clock budget, with one bounded extension;
- breadth first: reach the last stage, then spend what remains in a hardening phase on the
  deferred list;
- where the specification gives no limit, builders pick a generous documented one and refuse
  beyond it, instead of building unbounded generality;
- the commit command itself carries the pathspec, which would have prevented the
  shared-index incident;
- a seat settles queued messages as they arrive, so no backlog remains at the end.

## Disclosures and limits

- The run submitted here is one fresh room and one fresh result repository. Earlier rooms
  were development and are not part of this repository.
- The human sent one message. The operator observed the room read-only and ran no command
  in the result repository until the final report.
- The dispatch pointed the seats at an operator-written task brief
  (`factory/acceptance-brief-tablekeeper.md`) that summarises the published specifications
  by risk. It was available from the first message and is part of the single human input.
- The band reports four specification interpretations it had to choose (timestamp offsets
  for historical instants, immutable original receipts, exact JSON numbers, numeric input
  controls in the browser). They are listed in the final report in `room.json` and in
  `evidence/coordinator/`.
- The room's one error event (05:02 UTC) is the model provider's content filter refusing a
  single coordinator turn. The seat carried on with its next turn; nobody intervened.
- Finite tests do not establish behaviour under arbitrary load, and no accessibility
  conformance level is claimed.
- No hidden-suite result is claimed anywhere in this repository.
