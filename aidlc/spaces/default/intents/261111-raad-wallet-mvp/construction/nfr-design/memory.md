<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
- 2026-11-12T21:04:26Z [unit u1-walking-skeleton] — Existing NFR answers settle the product constraints, so no new interview is needed. Concrete deadlines, initial admission settings and alarm windows are proposed engineering choices for the Unit's gate; physical AWS selections remain in Infrastructure Design.
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
- 2026-11-12T21:04:26Z [unit u1-walking-skeleton] — Prefer bounded synchronous calls and authoritative store transactions over caches, queues or stateful circuit breakers at demo scale. Preserve all seven accepted Functional Design concerns as implementation risks, with no assertion that downstream design prose fixed them.
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
