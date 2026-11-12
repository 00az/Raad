<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-11T20:53:07Z — Read Q1 B as "the sign-in service starts the wallet opening and the money service does the work", so the team rule that only RaadMoneyService changes balances still holds. Q1 B alone conflicted with AC1.2.5 (an app retry must end with one wallet), so follow-up Q6 was asked; the person chose the safety net (A).

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-11T20:53:07Z — Recorded ADR-006 (transfer and request key in one all-or-nothing Ledger change) and ADR-007 (app talks to the sign-in service directly) as architect decisions that were not put to the person as questions; both are marked Proposed for confirmation at the gate. Also corrected one line in the approved mockups.md, which had said the reference format would be decided here; it is now set in Functional Design.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-11T20:53:07Z — Kept TransferRequest separate from Transfer so a refused outcome is kept for replay but can never appear in the history; the cost is a second Ledger entity. Counted LandingPage as a component (code the team writes, own repo) while the platform is not (configuration with no rules, Q3 A).

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-11T20:53:07Z — Left for later stages: how the account-confirmed signal reaches MoneyApi across Raad and RaadMoneyService when Raad deploys first (infrastructure design); how the email and display name reach MoneyApi on the safety-net path (contract design); the transfer reference format (functional design).
