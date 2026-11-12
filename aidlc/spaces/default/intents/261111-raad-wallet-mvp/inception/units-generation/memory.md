<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-12T14:24:51Z — Treated the team's Walking Skeleton practice as binding even though the classic scope sets skeleton off; it is carried by making U1 the only root and having every other unit depend on it. U5's edge on U1 is a practice edge, not a code dependency, and is labelled as such.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-12T14:24:51Z — The approved plan sent US6.2 and US6.4 to the Operation stages, but the traceability check accepts only a declared unit as an OK target and flagged both as gaps. Both were assigned to the units that build their parts, and the story map says so; the Operation stages still run the final proof. The check also accepts only one unit per OK target, so traceability.json names one lead unit per story while the story map lists every unit.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-12T14:24:51Z — Gave U4 the packaging kind, the closest fit for infrastructure code with no business logic, so it receives infrastructure, monitoring and pipeline designs but no business-logic model. Left U2 and U4 without an edge: neither needs the other's code, and the account-confirmed signal is proven end to end by U3's tests, which depend on both.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-12T14:24:51Z — RaadMoneyService, RaadMobile and RaadWeb must join the work before Code Generation; whether they already exist on GitHub under 00az is not yet known.
