<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-11T20:10:37Z — Read "put our logo in attached, and all recommended" as Q1 answer X (use the supplied logo) with Q2 to Q9 answer A. The image arrived in the chat only; no file was found on disk, so the palette was taken from how the image looks (near-black, silver-white chrome, blue and warm glints), not from pixel sampling.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-11T20:10:37Z — Designed a dark theme only, since the logo is drawn on black; a light theme would double the contrast checks and screenshots for a short timeline. Left Q5 answer A as the person chose it even though it gives no resend for an expired code; the gap is an open question for the gate.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-11T20:10:37Z — Still open: the logo file and a transparent-background version, the email address for "Request test access", a resend option for an expired confirmation code, whether to keep the DEV/STG chip, and a native reader for the Arabic wording.
