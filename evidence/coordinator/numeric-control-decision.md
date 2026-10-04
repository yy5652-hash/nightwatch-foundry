# Exact numeric controls interpretation

Recorded by Foundry Coordinator on 2026-10-04 for Stage 2 and inherited stages.

Stage 2 section 7.1 calls party-size-input a "Number" and section 7.3 calls booking-party-size a "Number input, pre-filled from the search". Neither section prescribes an HTML type attribute. Stage 1 section 7.3 accepts integral party_size values at least one, with table capacity as the applicable upper bound; the base fixture specification does not impose a universal numeric maximum.

The coordinator adopts an exact semantic numeric control: the visible editable field retains the complete decimal integer, has a visible label and spinbutton semantics, a numeric input mode, visible increment/decrement controls, and exact keyboard stepping with minimum one. Text storage is an implementation detail used to preserve integers beyond native browser floating-point range. The required test IDs remain on the actual editable field. There is no substitute hidden value or mocked DOM getter. The control must remain usable by keyboard and on a 375px viewport.

Requests still transmit party_size as an integer JSON token and a plain decimal query value, never a JSON string or a rounded/exponent-form substitute. Response integer values and combined capacities must display exactly. Validation remains authoritative on the server. Response syntax validation must reject malformed JSON before any lossless integer representation is applied.

This interpretation is derived from the published functional wording; it does not assert an unstated native HTML input type obligation. Independent verification must assess the real control, exact visible/input/query/body/retry values, labels, keyboard and mobile behavior against the complete specification. This decision is not a verifier acceptance. Preserve candidate-1 and builder failure evidence and report any residual judging ambiguity honestly.

