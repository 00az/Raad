# Bolt Plan: RAAD Digital Wallet MVP

Conversation language: English.

A **Bolt** is one full build pass through the Construction stages (design → code → test) for one unit of work,
ending in something that runs and can be verified on `dev`. This plan sequences five Bolts in topological
order through the dependency graph, with risk-first ordering for the middle batch.

## Sequence Overview

```
Bolt 1 → Bolt 2 → Bolt 3 → Bolt 4 → Bolt 5
  U1        U2        U4        U5        U3
 (skeleton) (money)  (platform)(landing)  (app)
```

U1 is the only unit with no dependency; every other unit depends on it. After U1, U2 is next
(highest risk: TDD money-movement core, concurrency, idempotency). U4 follows (extends U1's platform
and must be live before U3 can test its sign-in). U5 is next (smallest unit, no technical dependency).
U3 is last (depends on U1, U2 and U4 all being complete).

All Bolts are executed serially, one at a time (Q4 A), owned by aidlc-developer-agent (classic scope;
team-formation was not run). The two engineers own repos as agreed in team-allocation.md.

Within U1, the engineers work side by side in separate repos: Engineer 1 owns the platform and money-service work, and Engineer 2 owns the mobile work. This is a split inside the same first unit, not a change to the later unit order. Both use the same pinned C1 pre-release; the mobile track can use a contract-based fake server while the backend is being built. U1 completion still requires the real integrated `dev` result. The work boundaries and handoff are in `team-allocation.md`.

---

## Bolt 1 — U1 Walking Skeleton

**Units:** U1 `u1-walking-skeleton`
**Walking skeleton:** Yes. This Bolt is the thin end-to-end slice the team affirmed as the first piece of every greenfield project.

**What it proves:** The three repos connect end-to-end on real AWS infrastructure — sign-in, money API, and app all work together on `dev`, and the deploy pipelines reach `dev`.

**Integration points exercised:**
- `Raad` (sign-in pool + API domain + `/money` mapping) → `RaadMoneyService` (balance, one transfer, first history page) → `RaadMobile` (sign-in, wallet, send, history screens in English)
- Each repo's `dev` deploy path and smoke test

**Definition of Done:**
1. The API smoke script passes against the deployed `dev` API.
2. The Flutter integration test passes on a simulator against `dev`.
3. Both test users can sign in; one can send a transfer; the history shows it.
4. The other engineer has reviewed and approved the pull request to `main` in each of the three repos (`Raad`, `RaadMoneyService`, `RaadMobile`).
5. All checks pass in CI for each merged PR.
6. `RaadMoneyService` provisions the dedicated `Transactions` table keyed by `transferId`; a completed transfer writes one immutable row atomically with both wallet balance changes. The row retains sender/recipient wallet IDs for later history indexes (ADR-008).
7. The partial C1 pre-release validates the request key but stores no idempotency outcome. Until U2 supplies replay protection, the mobile track reconciles an uncertain result through balance/history and does not resubmit the transfer.

**Expected demo:** A test user signs in on a simulator, the wallet shows a 1,000.00 SAR balance, a transfer of any amount within limits goes through to the second test user, and the history entry appears. The API smoke script output is shown alongside.

**Repo owner:** Engineer 1 (Raad, RaadMoneyService), Engineer 2 (RaadMobile) — this Bolt spans both.

---

## Bolt 2 — U2 Money Service

**Units:** U2 `u2-money-service`
**Walking skeleton:** No. Extends the skeleton.
**Repo:** `RaadMoneyService`
**Owner:** Engineer 1

**What it proves:** The money service is production-complete and correct under concurrency and replay — amount limits, idempotency, simultaneous-transfer safety, and all business refusals — so U3 can generate its API client from a finished spec, and U4 can wire the account-confirmed entry point.

**Definition of Done:**
1. All `RaadMoneyService` checks pass: unit tests (pytest), integration tests against a local Docker container, Hypothesis property tests (money conservation, no negative balance), the replay test (same request → same result, money moves once), the concurrency test (simultaneous transfers from one wallet never overdraw it), and all rejection tests (insufficient funds; zero/negative/over-precise amount; unknown recipient; self-transfer; unauthenticated caller; another user's wallet).
2. ≥95% line and branch coverage on the money-movement core (amount validation, balance arithmetic, transfer rules, duplicate-request handling).
3. ≥80% overall line coverage on `RaadMoneyService`.
4. cdk-nag AwsSolutions rules pass on every CDK synth with no unsuppressed finding.
5. The complete OpenAPI description (C1 from Contract Design) is committed to `RaadMoneyService`.
6. The service deploys to `dev`, `stg` and `prd` and passes its smoke test on each.
7. The other engineer has reviewed and approved the pull request to `main`.
8. U2 introduces `TransferRequest` outcomes and the complete C1 idempotency matrix, including success written atomically with the existing transaction row and both balances, persisted business refusals, conflict handling and concurrent replay. Historical U1 transfers receive no fabricated key-to-outcome records; the transition starts fresh transfer intents and keys.
9. Sender-wallet and recipient-wallet history indexes extend U1's same `Transactions` table, and opaque-cursor paging passes the C1 stability and caller-binding checks. No second transfer-history store is introduced.
10. Provider/consumer contract checks use the canonical files and exact release pins in `contract-summary.md`. C2 event delivery and C5 edge/verifier behavior are tested at their boundaries; deployment to each environment waits for the matching platform resources and configuration, even while U2 and U4 can be developed independently.

**Expected demo:** The `pytest` run output showing all money-movement tests passing, coverage report at ≥95%/≥80%, and the `dev`/`stg`/`prd` smoke test results.

---

## Bolt 3 — U4 Platform

**Units:** U4 `u4-platform`
**Walking skeleton:** No. Extends the skeleton.
**Repo:** `Raad`
**Owner:** Engineer 1

**What it proves:** The full shared platform is in production: rate limits, firewall, resend and password-reset rules, and the account-confirmed signal path are all live and tested in every environment.

**Definition of Done:**
1. All `Raad` CDK stack tests pass and cdk-nag AwsSolutions rules pass on every synth.
2. Sign-in settings live in `dev`, `stg` and `prd`: one account per normalized email, the same refusal message for wrong password and unconfirmed account, code resend invalidating the old code, password reset, the password rule and session lengths from assumptions A4/A5, only email and display name stored.
3. Rate limits and firewall rules for sign-in, recipient lookups and transfers are deployed and enforced (AC1.3.5, AC3.5.4, NFR12).
4. The account-confirmed signal is wired from the sign-in service to the money service's entry point and confirmed working in `dev`.
5. Platform deploys to `dev`, `stg` and `prd`; the platform smoke test passes in each (API domain answers, a test user can sign in).
6. The other engineer has reviewed and approved the pull request to `main`.

**Expected demo:** Platform smoke test results for `dev`/`stg`/`prd`; a manual sign-up and confirmation flow that shows the new code invalidating the old one; rate-limit enforcement shown by the API firewall rejecting excess requests.

---

## Bolt 4 — U5 Landing Page

**Units:** U5 `u5-landing-page`
**Walking skeleton:** No.
**Repo:** `RaadWeb`
**Owner:** Engineer 2

**What it proves:** The landing page is live and reachable in every environment before U3 brings testers on board.

**Definition of Done:**
1. The Arabic and English landing page (screen S12) is deployed to `dev`, `stg` and `prd` on S3 behind CloudFront.
2. The smoke test fetches the page successfully in each environment.
3. The **Request test access** button is wired to the confirmed test-access email address (open question; build can proceed with a placeholder if still outstanding, but `prd` deploy gates on the real address).
4. The other engineer has reviewed and approved the pull request to `main`.

**Note:** The logo file and test-access email are still outstanding (unit-of-work.md Open Questions). The build can proceed; `prd` deploy gates on these being supplied. See external-dependency-map.md.

**Expected demo:** The page loads in a browser pointed at each environment's CloudFront URL; the smoke test output is shown.

---

## Bolt 5 — U3 Mobile App

**Units:** U3 `u3-mobile-app`
**Walking skeleton:** No. Completes the app on top of the skeleton.
**Repo:** `RaadMobile`
**Owner:** Engineer 2
**Prerequisite:** Bolt 2 (U2 complete — API description finalized) and Bolt 3 (U4 complete — sign-in settings live for integration tests).

**What it proves:** The full app is in testers' hands and all acceptance criteria are verifiable end-to-end against `dev`.

**Definition of Done:**
1. All `RaadMobile` checks pass: `flutter test` (unit and widget tests), `flutter analyze` (zero warnings), `integration_test` on an iOS simulator and an Android emulator against `dev`.
2. ≥80% line coverage.
3. The Dart API client is generated from U2's finalized OpenAPI description.
4. All account screens are complete: sign-up, confirmation (with **Send the code again**), the **Have a confirmation code?** link, password reset, sign-out, stay-signed-in, and the wallet-setup-failed screen.
5. All money screens are complete: amount hint, every refusal message with typed values preserved, retry rules, PendingTransfer after a lost answer, offline rules, BalanceSnapshot with its out-of-date mark, **Load more**, **Refresh** / pull-to-refresh, empty and error views.
6. Arabic and English with correct RTL layout and mixed-direction rules.
7. Accessibility checklist from `accessibility-checklist.md` passed.
8. Builds for `dev`, `stg` and `prd` distributed via TestFlight (iOS) and Google Play internal testing (Android).
9. The other engineer has reviewed and approved the pull request to `main`.

**Expected demo:** Integration test run against `dev` on both simulator and emulator; TestFlight and Google Play build links; a walkthrough of the Arabic layout in the simulator.

---

## Bolt Sequence Summary

| Bolt | Unit | Size | Key risk addressed | Prerequisite Bolts |
|---|---|---|---|---|
| 1 | U1 Walking skeleton | L | Architecture integration across three repos | — |
| 2 | U2 Money service | L | Concurrency, idempotency, TDD money core | Bolt 1 |
| 3 | U4 Platform | M | Sign-in completeness, rate limits, signal wiring | Bolt 1 |
| 4 | U5 Landing page | S | None (low-risk) | Bolt 1 (team practice) |
| 5 | U3 Mobile app | L | Full UX coverage, iOS build pipeline | Bolts 2 and 3 |

## Sources

- `requirements.md` in `inception/requirements-analysis/`: FR1–FR8, NFR1–NFR15 and acceptance criteria each Bolt's Definition of Done must satisfy
- `components.md` and `decisions.md` in `inception/domain-design/`: the five components (MobileApp, MoneyApi, Ledger, WalletDirectory, LandingPage) and ADR-001 to ADR-008 informing each unit's scope
- `unit-of-work.md` and `unit-of-work-dependency.md` in `inception/units-generation/`
- `contract-summary.md` in `inception/contract-design/`
- `team-practices.md` in `inception/practices-discovery/`
- `delivery-planning-questions.md` in this directory: Q1 D, Q2 B, Q3 A, Q4 A, Q5 B, Q6, B1–B5, Q7
