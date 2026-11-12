<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-11-12T15:03:26Z — Read Q1 A as a narrow exception to Domain Design ADR-005: UserConfirmed uses the shared event bus, but no transfer-completed event exists in the MVP. C2 carries at-least-once delivery, same-environment isolation and a 24-hour retry window; the public PUT /wallet remains the safety net.
- 2026-11-12T15:03:26Z — Treated POST /recipients/resolve as a read-like operation in the body rather than GET with an email query parameter, so the email does not enter URLs and ordinary access logs. Both resolve and transfer count toward one per-user lookup limit.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-11-12T15:03:26Z — Added C3 (sign-in behavior profile) and C4 (mobile environment configuration) although they are not network APIs, because U3 depends on U4's sign-in settings and environment outputs. They make those boundaries testable while U4 remains kind packaging and receives no Functional Design, an accepted Units Generation risk.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-11-12T15:03:26Z — Used PUT /wallet for idempotent wallet setup rather than creating a wallet as a side effect of GET /wallet. Used an Idempotency-Key header for transfers, so the body describes the business request and the key remains transport metadata. Used opaque cursor pagination instead of page numbers so a new transfer cannot shift later pages.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-11-12T15:03:26Z — Infrastructure Design supplies the real API hosts, event-bus resources and sign-in provider; Functional Design fixes the transfer-reference format; Delivery Planning and CI define how contract revisions are released and pinned across repos; the monitoring email is still unknown.
- 2026-11-12T15:24:41Z — Architecture review found four major gaps: the U4-to-U2 edge lacks token-verifier and edge-error details; transfer idempotency is ambiguous across refusal and transient outcomes; closed schemas contradict additive compatibility; and cross-repo contract release/pinning has no executable mechanism. It also found pagination, email-normalization, sign-in-provider capability and pre-bus publish ambiguities.
