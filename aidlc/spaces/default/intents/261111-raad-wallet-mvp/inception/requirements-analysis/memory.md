<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-11T18:58:44Z — Read "all recommended" plus the Q4 override as Q1-Q3 and Q5-Q9 option A and Q4 as 1.00 to 500.00 SAR with no daily total (Other). The Q4 variant that adds a 10,000 SAR daily cap was not chosen, so FR3.2 says there is no daily total.
- 2026-11-11T18:58:44Z — The deployment and landing-page requirements (FR7, FR8) come from the Request and team-practices.md, not the SOW; they are traced to those sources in requirements.md.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-11T18:58:44Z — Kept the corner-checklist items that need no fact from the person (double submit, stale balance, lost response, empty history) as requirements or assumptions instead of questions, to hold the question count to nine at Standard depth. The cost is that A2, A6 and A11 are assumptions the person has not yet confirmed; the gate is where they correct them.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-11T18:58:44Z — Five open questions are listed in requirements.md for later stages: the alarm email address, email sending limits for verification codes, who checks the Arabic wording, which service creates the wallet, and the region if Middle East residency is later required.
