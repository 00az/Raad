# Team Allocation: RAAD Digital Wallet MVP

Conversation language: English.

The classic scope does not run a team-formation stage. A **Bolt** is one build pass over a unit, ending in something that runs. Each engineer works with **aidlc-developer-agent** (the AI developer) in their own session and repo; the two engineers own implementation, review and approval as agreed below.

## Repo Ownership

The team has two engineers. Ownership means leading the code and pull-request reviews for that repo. Either engineer may open pull requests in any repo.

| Engineer | Repos | Notes |
|---|---|---|
| Engineer 1 | `Raad`, `RaadMoneyService` | Python/CDK platform and money service. Leads Bolts 2 and 3. Co-owns Bolt 1. |
| Engineer 2 | `RaadMobile`, `RaadWeb` | Flutter app and static landing page. Leads Bolts 4 and 5. Co-owns Bolt 1. |

Bolt 1 (the walking skeleton) spans `Raad`, `RaadMoneyService` and `RaadMobile`, so both engineers are involved in reviewing its three pull requests.

## Separate U1 Work Tracks

The walking skeleton is the first thin slice that proves sign-in, money movement and the app together on `dev`. Its two work tracks can run side by side without claiming separate units:

| Track | Owner | Writes | Handoff |
|---|---|---|---|
| Backend and platform | Engineer 1 | `Raad` platform and shared design record; `RaadMoneyService` API, Ledger, stacks and tests | Publishes the pinned C1 pre-release and environment configuration; provisions `Transactions` and atomically writes transfer plus balances; supplies the real `dev` API for integration. U2 later adds saved idempotency outcomes and history indexes. |
| Mobile | Engineer 2 | `RaadMobile` screens, generated client, client tests and mobile build configuration | Pins that exact C1 revision, builds against a contract-based fake server while the backend is unavailable, then proves sign-in/balance/send/history against the real `dev` backend. Uncertain U1 transfer results are reconciled without resubmission. |

Each track uses its own checkout and short-lived branch. Neither engineer edits the other track's files without coordination. Engineer 1 maintains the shared `aidlc/` record; Engineer 2 reports mobile progress with its PR and pinned contract revision so the record can be updated without competing edits. Contract changes are agreed through the owning repo's PR and then explicitly re-pinned by the mobile track. Both engineers review the other track's PRs. A fake-server result supports development but does not complete U1; both tracks join for the real `dev` check.

## Bolt-to-Owner Map

| Bolt | Unit | Primary repo owner | Reviewer |
|---|---|---|---|
| 1 | U1 Walking skeleton | Both (see above) | Both |
| 2 | U2 Money service | Engineer 1 | Engineer 2 |
| 3 | U4 Platform | Engineer 1 | Engineer 2 |
| 4 | U5 Landing page | Engineer 2 | Engineer 1 |
| 5 | U3 Mobile app | Engineer 2 | Engineer 1 |

## AI Builder

Each engineer's aidlc-developer-agent session builds only its assigned track in a short-lived branch off `main` in the relevant repo. It opens a pull request for the other engineer's review; merge follows the team's protected-main rules. PR approval is part of each Bolt's Definition of Done (`bolt-plan.md`). Later units retain the recorded serial order; separate U1 work tracks do not change the unit dependency graph.

## Sources

- `delivery-planning-questions.md` in this directory: Q7
- `team-practices.md` in `inception/practices-discovery/`: Way of Working, repo table
- `bolt-plan.md` in this directory
