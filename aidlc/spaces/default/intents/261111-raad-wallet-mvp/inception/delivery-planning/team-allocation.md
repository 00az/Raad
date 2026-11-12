# Team Allocation: RAAD Digital Wallet MVP

Conversation language: English.

The classic scope does not run a team-formation stage. All Bolts are executed by **aidlc-developer-agent** (the AI developer), which acts as the sole builder across all repos. The two engineers own review and approval across the repos as agreed below.

## Repo Ownership

The team has two engineers. Ownership means leading the code and pull-request reviews for that repo. Either engineer may open pull requests in any repo.

| Engineer | Repos | Notes |
|---|---|---|
| Engineer 1 | `Raad`, `RaadMoneyService` | Python/CDK platform and money service. Leads Bolts 2 and 3. Co-owns Bolt 1. |
| Engineer 2 | `RaadMobile`, `RaadWeb` | Flutter app and static landing page. Leads Bolts 4 and 5. Co-owns Bolt 1. |

Bolt 1 (the walking skeleton) spans `Raad`, `RaadMoneyService` and `RaadMobile`, so both engineers are involved in reviewing its three pull requests.

## Bolt-to-Owner Map

| Bolt | Unit | Primary repo owner | Reviewer |
|---|---|---|---|
| 1 | U1 Walking skeleton | Both (see above) | Both |
| 2 | U2 Money service | Engineer 1 | Engineer 2 |
| 3 | U4 Platform | Engineer 1 | Engineer 2 |
| 4 | U5 Landing page | Engineer 2 | Engineer 1 |
| 5 | U3 Mobile app | Engineer 2 | Engineer 1 |

## AI Builder

aidlc-developer-agent runs all Construction stages for every Bolt. It works in a short-lived branch off `main` in the relevant repo, opens a pull request, and the owning engineer reviews and merges it. The engineer's PR approval is part of each Bolt's Definition of Done (bolt-plan.md).

## Sources

- `delivery-planning-questions.md` in this directory: Q7
- `team-practices.md` in `inception/practices-discovery/`: Way of Working, repo table
- `bolt-plan.md` in this directory
