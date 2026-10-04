# Coordinator Stage 2 interface source review

Reviewed full committed interface revision: `a040054f2a8d00c560bea7f02324d1443c5a3f14`.
Review scope is source integration, not a complete Stage 2 runtime/coverage verdict.
The Systems core/module reconstruction was uncommitted during this review.

The adapter retains the accepted raw bytes codec contract, complete parsed object delivery,
case-insensitive header lookup, original URL, one shared Engine, concurrent threads and
backlog 128. Response bytes are prepared before headers. Static serving uses a fixed
screen/asset whitelist, explicit HTML/CSS/JS content types and local assets. Lost-response
handling does not retry committed backend work inside the transport.

Dockerfile packages core, server, codec and web assets in one image, installs IANA data
at build time and starts under the existing unprivileged user. Runtime downloads or host
packages are not introduced. RUN.md covers default/override PORT, real browser routes,
server-authoritative booking, unchanged-form retry and between-request upgrade behavior.

The browser source validates response JSON syntax before numeric token transformation,
preserves quoted text and resolves integral decimal/exponent tokens for exact unsafe-integer
display. Existing labelled semantic number controls, genuine API requests, search-generation
checks, uncertainty handling and explicit restaurant-zone end formatting remain present.
These source observations do not prove boundary performance, browser usability or migration
execution. The owning Interface handoff explicitly claims preparation/syntax only and holds
complete image execution for the committed Systems handoff.

Required next evidence: complete named core/module and interface integration; genuine
old/new Stage 1 and old Stage 2 transfers and retry identity; exact numeric presentation;
actual mobile/desktop/loading/refusal/uncertainty interactions; fresh independent cumulative
coverage and isolated official Stage 1/2 results. Stage 2 is unaccepted. The adopted timestamp,
receipt, semantic-control and exact-number/legacy-profile decisions remain disclosed.

Coordinator harness Codex/configured gpt-6.1-sol; actual model override, effort, usage and
spend unknown. This source review introduces no production edits or additional acceptance
requirements and does not copy or validate peer probe implementations.

