# Risk and Sequencing Rationale: RAAD Digital Wallet MVP

Conversation language: English.

## Sequencing Heuristic

The Bolt sequence uses a **risk-first** ordering after the walking skeleton, guided by the dependency graph. The rationale is qualitative rather than scored (Q2 B): WSJF scoring would be useful if the units competed for the same resource or had comparable risk profiles, but the DAG structure constrains the feasible orderings enough that qualitative judgment is sufficient.

## Bolt 1 — U1 Walking Skeleton (risk: architectural integration)

**Why first:** U1 is the only unit with no dependency; it is the team's affirmed skeleton practice and the prerequisite for every other Bolt. The skeleton's risk is integration: three repos, real AWS infrastructure, and an end-to-end flow that has never run together. Building it first means every subsequent Bolt builds on a proven foundation rather than discovering integration surprises late. If the skeleton cannot be verified on `dev`, nothing else can ship.

**Risk mitigated:** Architecture plumbing fails to connect (sign-in pool, API domain, money service, app). Discovered in Bolt 1, not Bolt 5.

## Bolt 2 — U2 Money Service (risk: correctness under concurrency and replay)

**Why second:** U2 is the highest-risk unit. It requires test-driven development for the money-movement core (Ledger's amount validation, balance arithmetic, transfer rules, and duplicate-request handling), ≥95% line and branch coverage on that core, a Hypothesis property test for money conservation, a replay test, and a concurrency test against a real Docker container. These are not optional — they are the team's affirmed quality floor for a system where a defect means wrong balances or double charges. Getting this right takes the most deliberate attention. It also gates U3: U3 generates its Dart API client from U2's finalized OpenAPI description, so U2 must finish before U3 can begin in earnest.

**Risk mitigated:** Incorrect money movement under concurrent or repeated requests. Discovered in Bolt 2 under full test coverage, not discovered in production.

## Bolt 3 — U4 Platform (risk: sign-in completeness and signal wiring)

**Why third:** U4 extends U1's platform stacks with the remaining sign-in settings, rate limits, firewall rules, and the account-confirmed signal from the sign-in service to the money service's entry point. Its risk is medium: the CDK work is well-understood, but the account-confirmed signal wiring (domain-design finding R-02) has an open implementation decision (how exactly the event bridge is configured). That decision is resolved in Infrastructure Design; placing U4 after U2 means U2's entry point is already implemented and tested when U4's signal wiring is built. U4 must also be live before U3's integration tests can run against real sign-in settings.

**Risk mitigated:** Rate limits and firewall rules not enforced; account-confirmed signal mis-wired. Discovered in Bolt 3 with dedicated CDK and integration tests, not discovered during app development.

## Bolt 4 — U5 Landing Page (risk: low)

**Why fourth:** U5 is the lowest-risk Bolt. It is a static site (HTML/CSS), has no business logic, and its only technical dependency on U1 is a team-practice enforcement (skeleton approved before anything else starts). Its two open questions (logo file, test-access email) do not block the build — they block the `prd` deploy. Placing it fourth, after the highest-risk work is done, means it does not compete for attention with U2 and U4. It can proceed before U3 unblocks.

**Risk mitigated:** Outstanding content items (logo, email) delay the build. Surfaced early in the external dependency map; `prd` deploy gates on them.

## Bolt 5 — U3 Mobile App (risk: build pipeline and integration test environment)

**Why last:** U3 depends on both U2 (API description finalized) and U4 (sign-in settings live for integration tests). There is no topologically valid earlier position. Its additional risk is the iOS build pipeline: a macOS runner (GitHub Actions) or a development laptop with Xcode is required, and that must be confirmed before Bolt 5 starts. The app itself is well-scoped — the screens and states are fully specified in the mockups — but the size (L) and the Arabic RTL layout add execution risk.

**Risk mitigated:** iOS build infrastructure not ready when needed. Surfaced in external-dependency-map.md as a Bolt 5 prerequisite.

## Deviation from Topological Order

The sequence U1 → U2 → U4 → U5 → U3 is fully topologically valid. No deviation exists. U5 could be built immediately after U1 (it has no code dependency), but placing it after U2 and U4 keeps the team's focus on the high-risk backend work first.

## Summary

| Bolt | Heuristic | Primary risk | Risk level |
|---|---|---|---|
| 1 | Skeleton-first (team practice) | Integration across three repos | High |
| 2 | Risk-first | Money correctness under concurrency/replay | High |
| 3 | Risk-first (medium) | Signal wiring, rate limits | Medium |
| 4 | Low-risk remainder | Content availability | Low |
| 5 | DAG-forced last | iOS build pipeline, RTL layout | Medium |

## Sources

- `unit-of-work.md` and `unit-of-work-dependency.md` in `inception/units-generation/`
- `team-practices.md` in `inception/practices-discovery/`: Walking Skeleton, Testing Posture
- `delivery-planning-questions.md` in this directory: Q1 D, Q2 B, Q6
- `bolt-plan.md` in this directory
