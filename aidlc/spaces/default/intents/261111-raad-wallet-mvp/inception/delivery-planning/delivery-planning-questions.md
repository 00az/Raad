# Delivery Planning Questions

Conversation language: English.

These questions plan the Bolt sequence — the order the five units of work move through Construction.
A **Bolt** is one build pass through the Construction stages (design → code → test) over one or more units,
ending in something that runs and can be verified. The five units are:

| Unit | What it is | Depends on |
|---|---|---|
| U1 `u1-walking-skeleton` | The first thin slice: sign-in, one transfer, history. Spans `Raad`, `RaadMoneyService`, `RaadMobile`. | nothing |
| U2 `u2-money-service` | Completes the money service in `RaadMoneyService`. | U1 |
| U3 `u3-mobile-app` | Completes the Flutter app in `RaadMobile`. | U1, U2, U4 |
| U4 `u4-platform` | Completes the shared platform in `Raad`. | U1 |
| U5 `u5-landing-page` | The static landing page in `RaadWeb`. | U1 (enforced by team practice) |

The dependency graph means: after U1, we can build U2, U4 and U5 at the same time (or in any order).
U3 can only start once U2 **and** U4 are both done.

---

## Strategic Questions

**Q1 — What to build first**

Your team has already affirmed a walking-skeleton-first practice: U1 goes first, is built through all its Construction stages, and the full slice is verified on `dev` before anything else begins. After that, what guides the order of U2 through U5?

A. **Risk-first** — tackle the hardest or most uncertain pieces next (money service with its TDD and concurrency requirements)
B. **Value-first** — ship the highest user-facing value next (mobile app would follow the skeleton, but it depends on U2 and U4 being done)
C. **Parallel where possible** — build U2, U4 and U5 together after the skeleton, then U3 (fastest total calendar time, needs attention split across multiple fronts)
D. **Sequential, risk-first** — U1, then U2 (riskiest: TDD + concurrency + idempotency), then U4, then U5, then U3
E. Other (please specify)

[Answer]: D

---

**Q2 — Formal scoring**

Should we score the Bolt sequence with a formal model (Weighted Shortest Job First: a score of user-business value + time criticality + risk-reduction divided by size, so the highest-scoring piece ships first)?

A. Yes — score each proposed Bolt and document the rationale in the sequencing artifact
B. No — the DAG topology plus the team's risk and value judgment is enough; keep the rationale qualitative
C. Other (please specify)

[Answer]: B

---

**Q3 — Bolt size**

How should we bundle the work into Bolts?

A. **One unit per Bolt** — 5 Bolts total, each unit as its own independent build pass. Clearest boundaries; each Bolt has its own Definition of Done.
B. **Bundle related units** — group U2+U4 into one Bolt (both backend/platform pieces that mature after the skeleton); then U1, Bolt-2 (U2+U4 together), U3, U5 as 4 Bolts. Saves some coordination overhead; U3 unblocks earlier.
C. **Minimal slices** — each unit stays its own Bolt but U5 is bundled with U1 since it's tiny (S) and has no technical dependency on U1's code. 4 Bolts: U1+U5 together, U2, U4, U3.
D. Other (please specify)

[Answer]: A

---

**Q4 — Parallel Bolts**

After the skeleton, can U2, U4 (and U5) be built at the same time by working across those repos in parallel, or should they go one after the other?

A. **Serial** — one Bolt at a time; full attention, simpler to track
B. **Parallel** — build U2, U4 (and optionally U5) simultaneously; faster calendar time
C. Other (please specify)

[Answer]: A

---

**Q5 — External dependencies and blockers**

Is anything outside this team going to hold up the build? For example:
- AWS account and IAM permissions: set up before U1's CDK deploys
- Apple Developer account and TestFlight access: needed before U3's iOS builds reach testers
- Google Play internal testing setup: needed before U3's Android builds reach testers
- RAAD logo file: needed before U3 can be completed (`mockups.md`, Open Questions)
- Test-access email address for the landing page: needed before U5 is complete
- Native Arabic review: needed before `prd` release

For each one that applies, say who owns it, how long it takes, which Bolt it blocks, and what the fallback is.

A. All of these are already in hand or can be resolved before the Bolt that needs them — no blockers to plan around
B. Some of these are blockers — list them below
C. Other (please specify)

[Answer]: B — The logo file and test-access email are outstanding (noted in unit-of-work.md Open Questions). Apple Developer account and Google Play internal testing setup are assumed in progress but not yet confirmed. All four are tracked in the external dependency map; none block U1 or U2.

---

**Q6 — Biggest worry**

What worries you most about this build, so we tackle it early or flag it as a risk?

(Free text — write anything, or "None" if nothing stands out)

[Answer]: The money-movement correctness under concurrency (simultaneous transfers, idempotency replay) is the highest technical risk. Getting the TDD discipline right for the Ledger core in U1 and U2 is where most defects are likely to hide. The iOS build pipeline (macOS runner or laptop) is the highest operational risk — it must be confirmed before Bolt 5 starts.

---

## Per-Bolt Questions

These are asked per proposed Bolt. The proposals below follow the team's walking-skeleton-first practice and the dependency graph. Answer each one, or say "adjust" and tell us how.

### Bolt 1 — U1 (Walking skeleton)

**B1a — Definition of Done**
What has to be true for this Bolt to count as done?

A. The proposed verification: API smoke script passes against the deployed `dev` API, and the Flutter integration test passes on a simulator against `dev`. Both test users can sign in, one can send a transfer, and the history shows it.
B. Same as above, plus the other engineer has reviewed and approved the pull request to `main` in each of the three repos.
C. Other (please specify)

[Answer]: B

**B1b — What will shipping this Bolt prove?**

A. That the three repos connect end-to-end on real AWS infrastructure: sign-in, money API, and app all work together on `dev`, and the deploy pipelines reach `dev`.
B. Other (please specify)

[Answer]: A

---

### Bolt 2 — U2 (Money service completion) *(adjust if Q3 changes the grouping)*

**B2a — Definition of Done**

A. All `RaadMoneyService` checks pass (unit, integration, Hypothesis property tests, replay and concurrency tests), ≥95% line+branch on the money-movement core, ≥80% overall, cdk-nag clean; the full API description is committed; the service deploys to `dev`, `stg` and `prd` and passes its smoke test on each.
B. Other (please specify)

[Answer]: A

**B2b — What will shipping this Bolt prove?**

A. That the money service is production-complete and correct under concurrency and replay, so U3 can generate its API client from a finished spec, and U4 can wire the account-confirmed entry point.
B. Other (please specify)

[Answer]: A

---

### Bolt 3 — U4 (Platform completion) *(adjust if Q3 changes the grouping)*

**B3a — Definition of Done**

A. All `Raad` checks pass (CDK stack tests, cdk-nag clean); sign-in settings, rate limits, firewall rules and account-confirmed signal are all in `dev`, `stg` and `prd`; the platform smoke test passes in each environment (API domain answers, test user can sign in).
B. Other (please specify)

[Answer]: A

**B3b — What will shipping this Bolt prove?**

A. That the full shared platform is in production: rate limits, firewall, resend and password-reset rules, and the account-confirmed signal path are all live and tested.
B. Other (please specify)

[Answer]: A

---

### Bolt 4 — U5 (Landing page) *(adjust if Q3 changes the grouping)*

**B4a — Definition of Done**

A. The page is deployed to `dev`, `stg` and `prd` and the smoke test fetches it successfully in each environment.
B. Other (please specify)

[Answer]: A

**B4b — What will shipping this Bolt prove?**

A. That the landing page is live and reachable in every environment before U3 brings testers on board.
B. Other (please specify)

[Answer]: A

---

### Bolt 5 — U3 (Mobile app completion) *(always last; depends on U2 and U4)*

**B5a — Definition of Done**

A. All `RaadMobile` checks pass (`flutter test`, `flutter analyze`, `integration_test` on iOS simulator and Android emulator against `dev`), ≥80% line coverage; builds for all three environments are on TestFlight (iOS) and Google Play internal testing (Android); accessibility checklist passed; Arabic and English layouts correct.
B. Other (please specify)

[Answer]: A

**B5b — What will shipping this Bolt prove?**

A. That the full app is in testers' hands and all acceptance criteria are verifiable end-to-end against `dev`.
B. Other (please specify)

[Answer]: A

---

## Repo Ownership

The team has two engineers. Delivery planning is the place to agree who owns which repo.

**Q7 — Who owns which repo?**

For each repo, say which engineer is primarily responsible for its work during Construction. "Primarily responsible" means they lead the code and reviews for that repo; either engineer can send pull requests to any repo.

(Free text — for example: "Engineer 1: Raad, RaadMoneyService. Engineer 2: RaadMobile, RaadWeb.")

[Answer]: Recommended split based on skills implied by the stack — Engineer 1: Raad (CDK/Python platform), RaadMoneyService (Python/AWS). Engineer 2: RaadMobile (Flutter/Dart), RaadWeb (static HTML/CSS). Either engineer can open pull requests in the other's repos.

---

## Assumptions & Open Questions

- U3's integration tests require a simulator (Xcode) and an emulator (Android SDK). These are assumed available on a development machine or a macOS GitHub Actions runner.
- The RAAD logo file and the test-access email address are still outstanding (`unit-of-work.md`, Open Questions); U3 and U5 respectively are blocked on these before `prd`.
- The Apple Developer account and Google Play setup are assumed in progress; U3's tester builds need them.

## Sources

- `unit-of-work.md` and `unit-of-work-dependency.md` in `inception/units-generation/`
- `contract-summary.md` in `inception/contract-design/`
- `team-practices.md` in `inception/practices-discovery/`
- `requirements.md` in `inception/requirements-analysis/`
