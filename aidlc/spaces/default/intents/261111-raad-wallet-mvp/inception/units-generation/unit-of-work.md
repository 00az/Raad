# Units of Work: RAAD Digital Wallet MVP

Conversation language: English.

This document groups the building blocks in `components.md` (MobileApp, MoneyApi, Ledger, WalletDirectory and LandingPage) and the shared platform into five units of work. It follows the plan approved in `units-generation-questions.md` (Q1 A, Q2 B, Q3 A and Plan Approval) and keeps to the boundary decisions in `decisions.md` (ADR-001 to ADR-008), the requirements in `requirements.md`, the stories in `stories.md` and the practices in `team-practices.md`.

The dependencies between units are in `unit-of-work-dependency.md`, and the stories each unit implements are in `unit-of-work-story-map.md`. This document does not choose which unit is built after the skeleton, or who builds it: Delivery Planning decides both.

## Units

| Unit ID | Directory | Kind | Repos | Deployment model | Size |
|---|---|---|---|---|---|
| U1 | `u1-walking-skeleton` | none (the full design set) | `Raad`, `RaadMoneyService`, `RaadMobile` | Each repo's part deploys on its own, through that repo's pipeline | L |
| U2 | `u2-money-service` | `service` | `RaadMoneyService` | Standalone: the money service's own stacks | L |
| U3 | `u3-mobile-app` | `ui` | `RaadMobile` | Standalone: one app build per environment, given to testers | L |
| U4 | `u4-platform` | `packaging` | `Raad` | Shared: the platform every service uses, deployed first in each environment | M |
| U5 | `u5-landing-page` | `ui` | `RaadWeb` | Standalone: one static site per environment | S |

Sizes compare the units with each other only (S, M, L, XL).

**Why these kinds.** U1 cuts across infrastructure, service and app, so it has no kind and receives every design artifact in Construction. U2 is a deployed service with business rules. U3 and U5 are front ends. U4 is infrastructure code with no business logic; `packaging` is the closest kind, and it receives the infrastructure, monitoring and pipeline designs but no business-logic model.

## Components and Units

| Component or piece | U1 | U2 | U3 | U4 | U5 |
|---|---|---|---|---|---|
| MobileApp | Sign-in, wallet, send (form, review, result) and history screens, in English | | Every other screen and state | | |
| MoneyApi | Sign-in check, wallet setup on the first request (safety net), balance, recipient lookup, one transfer, first history page | Remaining operations and refusals, account-confirmed entry point, safe errors | | | |
| Ledger | Open a wallet, balance, provision the dedicated `Transactions` table keyed by `transferId`, atomic transfer row and wallet balance writes, first history page | Amount limits, own-wallet refusal, request keys and replay, simultaneous-transfer tests, sender/recipient wallet history indexes on the same table and history paging | | | |
| WalletDirectory | Register a holder, find by email, names for a history page | Refusal of an address already held by another user | | | |
| LandingPage | | | | | The whole page |
| Shared platform (infrastructure) | Sign-in pool with email and password, public API address with `/money`, a basic firewall | | | Remaining sign-in settings, rate limits, firewall rules, signal wiring, `stg` and `prd` setup | |

## Entities and Units

| Entity | Owning component | Introduced in | Extended in |
|---|---|---|---|
| Wallet | Ledger | U1, including one wallet per owner when two first requests arrive together | none |
| Transfer | Ledger | U1: one immutable row per completed transfer in the dedicated `Transactions` table, keyed by `transferId` | U2: sender/recipient wallet history indexes and paging on the same table |
| TransferRequest | Ledger | U2 | none |
| WalletHolder | WalletDirectory | U1 | U2 (refusal of a taken address) |
| PendingTransfer | MobileApp | U3 | none |
| BalanceSnapshot | MobileApp | U3 | none |
| LanguageSetting | MobileApp | U3 | none |

---

## U1 `u1-walking-skeleton`

**Description.** The thinnest slice that runs the whole way through on `dev`, built first to prove the pieces connect (team practices, Walking Skeleton). A test user signs in on the phone, sees the SAR balance, sends one simulated transfer to another RAAD wallet and sees it in the history. It goes through the real sign-in, API, data store and each repo's deploy path. The landing page is not part of it.

**Boundaries.** In: the pieces listed below. Out: everything in U2 to U5, including sign-up and confirmation screens, code resend, password reset, amount limits, request-key replay, history paging, Arabic and accessibility.

**Responsibilities.**

- The shared sign-in pool (email and password) and the public API address with the `/money` path, in `Raad`, deployed to `dev`.
- MoneyApi: a sign-in check on every request, with the caller taken from the verified sign-in; wallet setup through the safety net (ADR-003), using the email and display name from the verified sign-in; the balance; recipient lookup by email; one transfer; and the first page of the history with names.
- Ledger, built test-first:
  - opens a wallet with 100,000 halalas once per owner, also when two first requests arrive together;
  - reads the balance;
  - makes a transfer as one all-or-nothing change with the balance check, so a balance never goes below zero;
  - provisions the dedicated `Transactions` table and records each completed Transfer as one immutable row keyed by `transferId`, with its reference, sender and recipient wallet IDs, whole-halalah amount and completion time, atomically with both wallet balance changes (ADR-008); current balances remain on Wallet records;
  - lists completed transfers newest first.
- WalletDirectory: registers a holder; finds one by the whole email address, ignoring surrounding spaces and capitals; returns names for a list of user ids.
- The app's sign-in, wallet, send (form, review, result) and history screens, in English, against `dev`.
- A setup script that creates two confirmed test users in an environment, reading their passwords from a secrets store (Q3 A).
- The `dev` deploy path of the three repos.
- The checks that prove the slice: an API smoke script against the deployed `dev` API, and a Flutter integration test on a simulator against `dev`. This is the team's proposed verification; it becomes the Construction Verification Command only when the person authorises it at Construction.

**Deployment model.** Each repo's part deploys on its own; `Raad`'s part goes first. U1 provisions the dedicated `Transactions` table in the money service's own stacks; the Ledger owns its writes.

**Implementation notes.**

- The money-movement core (amount validation, balance arithmetic, transfer rules) is written test-first, with at least 95% line and branch coverage and the property test that the total money never changes (team practices).
- The API description written in Contract Design is the source of truth. U1 builds its balance, recipient lookup, transfer and first-history-page operations as a partial pre-release. It accepts and validates the request key but stores no `TransferRequest` or key-to-transfer outcome; U2 introduces that record and the replay rules. U1's atomic write covers the completed transfer row and both balances only.
- The send button turns off after one tap, so the skeleton cannot send twice by accident. Full duplicate protection comes in U2 and U3.
- Until U2 provides replay protection, the skeleton client must not resubmit a transfer after an uncertain result; it refreshes balance and history to reconcile. The transition to U2 starts fresh transfer intents and keys, and never invents replay outcomes for historical U1 transfers without saved keys and fingerprints.
- Test-user passwords never enter a repo or a log (project rules).

## U2 `u2-money-service`

**Description.** Completes the money service in `RaadMoneyService` on top of the skeleton.

**Responsibilities.**

- Ledger:
  - amount limits of 100 to 50,000 halalas;
  - refusal of a transfer to one's own wallet;
  - introduces `TransferRequest` and the complete C1 idempotency guarantee: the first outcome of each sender and request key is kept, a repeat returns it, a repeat with different details is refused, and only one record exists per sender and key, even under simultaneous requests; a successful outcome is written atomically with the existing `Transactions` row and both wallet balances, while refused outcomes change no balances and create no completed transfer;
  - tests of simultaneous transfers against a real data-store container;
  - adds the sender-wallet and recipient-wallet history indexes to U1's existing `Transactions` table and implements history pages from a position marker; both histories refer to the same immutable row and `transferId`, with no second transfer-history store.
- MoneyApi:
  - the refusal for an unknown recipient, and every other refusal, each with a stable code and a safe message;
  - the account-confirmed entry point (ADR-003), callable only by the same environment's sign-in service, with nothing personal written to logs;
  - logs that carry only opaque ids and correlation ids.
- WalletDirectory: refuses and reports an address already held by another user id.
- The complete API description committed to `RaadMoneyService`, which the app generates its client from.
- The money service's stacks for `dev`, `stg` and `prd`.

**Deployment model.** Standalone; the service's own stacks, after the platform in each environment. U2 extends U1's existing `Transactions` table with the sender/recipient history indexes through those stacks and preserves its transfer rows and wallet balances.

**Implementation notes.** The replay test, the concurrency test and the rejection tests required by the practices are written here, test-first for the money core. This unit builds the account-confirmed entry point and tests it directly; how the sign-in service's signal reaches it is decided in infrastructure design, together with U4 (domain-design finding R-02).

## U3 `u3-mobile-app`

**Description.** Completes the Flutter app in `RaadMobile`.

**Responsibilities.**

- Account screens: sign-up, the confirmation code with **Send the code again**, the **Have a confirmation code?** link on sign-in, password reset, sign-out, staying signed in, and the "We could not set up your wallet" screen.
- Money screens: the amount hint and messages; every refusal message, with the typed values kept; the **Try again** rules and the PendingTransfer after a lost answer; the offline rules; the BalanceSnapshot and its out-of-date mark; **Load more** for the history; the **Refresh** button and pull to refresh; and the empty and error views.
- Arabic and English, with the right-to-left layout and the mixed-direction rules in `mockups.md`.
- Accessibility to the checklist in `accessibility-checklist.md`.
- The Dart API client generated from U2's API description.
- Build flavours for `dev`, `stg` and `prd`.

**Deployment model.** Standalone; one build per environment, given to testers through TestFlight and Google Play internal testing.

**Implementation notes.** Integration tests run against the real money service and the real sign-in settings in `dev` (Q2 B), which is why U3 depends on U2 and U4. The app trims the email address before sign-up and sign-in (domain-design finding R-03). The theme comes from the RAAD logo; the logo file is still to be supplied (`mockups.md`, Open Questions).

## U4 `u4-platform`

**Description.** Completes the shared platform in `Raad`.

**Responsibilities.**

- Sign-in settings:
  - one account per email address, ignoring capitals and surrounding spaces (FR1.6; finding R-03);
  - the same refusal for a wrong password and an unconfirmed account;
  - code resend, with a new code replacing the old one (AC1.2.6; finding R-04);
  - password reset, the password rule (A4) and the session lengths (A5);
  - only the email address and display name stored (AC1.1.4).
- Rate limits and firewall rules for sign-in, recipient lookups and transfers (AC1.3.5, AC3.5.4, NFR12; findings R-05 and R-06).
- The account-confirmed signal from the sign-in service to the money service's entry point, wired the way infrastructure design decides (finding R-02). The signal never delays or fails a confirmation.
- The platform's stacks for `stg` and `prd`, deployed before the services in each environment, and the platform smoke test: the API address answers and a test user can sign in.

**Deployment model.** Shared; deployed first in each environment (team practices).

## U5 `u5-landing-page`

**Description.** The static Arabic and English page in `RaadWeb` (screen S12).

**Responsibilities.** The page with the **Request test access** button, hosted on S3 and CloudFront in each environment, and its smoke test that fetches the page.

**Deployment model.** Standalone; one static site per environment.

**Implementation notes.** U5 needs no code from any other unit. It depends on U1 only so that the skeleton is approved before any other work starts (team practices). Its content follows assumption A9. The email address behind the button is still to be supplied.

---

## Walking Skeleton

U1 is the only unit with no dependency, and every other unit depends on it, so it is the first unit in the dependency order. It can run before the later units because it is deployed to `dev` through each repo's own deploy path and checked by its own smoke script and integration test.

The classic plan turns off the framework's own skeleton step, so this decomposition carries the team's practice. Delivery Planning confirms how the skeleton is demonstrated and approved before the other units start.

## Environments

Every unit's stacks and builds take the environment (`dev`, `stg` or `prd`) as a parameter, and each repo deploys its part into all three (team practices). The parts of US6.2 (every environment) and US6.4 (acceptance on `prd`) that are code belong to units: the per-environment stacks, builds and smoke tests to U2 to U5, the opening balance to U1 and the acceptance script to U3 (`unit-of-work-story-map.md`). The final proof runs in the Operation stages: environment provisioning and deployment execution.

## Repos Joining the Work

U1, U2, U3 and U5 change `RaadMoneyService`, `RaadMobile` and `RaadWeb`, so those repos join this work before Code Generation. `Raad` is this repo.

## Carried Into Construction

At the Domain Design gate, the person accepted the architecture review's open findings as risks. The units that will meet each one:

| Finding | What it asks | Units |
|---|---|---|
| R-01 | Uniqueness under simultaneous calls: one TransferRequest per sender and key, one wallet per owner, one holder per email | U1, U2 |
| R-02 | Wiring the account-confirmed signal from `Raad` to `RaadMoneyService` when `Raad` deploys first | U2, U4 (decided in infrastructure design) |
| R-03 | One account per email at sign-up, ignoring capitals and spaces | U3, U4 |
| R-04 | Code resend: the old code stops working, and every address gets the same message | U3, U4 |
| R-05 | Where the recipient-lookup limit is enforced, and that sends count as lookups | U2, U4 (sized in NFR design) |
| R-06 | Account actions do not pass the platform firewall | U4 (confirmed in infrastructure design) |
| R-07 | Only the same environment's sign-in service may call the entry point, and its contents are never logged | U2, U4 |
| R-08 | NFR13 and the AI assistant | None: outside the MVP |

## Assumptions & Open Questions

- The RAAD logo file and the test-access email address are still to be supplied (`mockups.md`).
- A native Arabic reader checks the app's and the page's Arabic wording before release (`requirements.md`).
- Whether the Ledger and WalletDirectory stores share one physical database is decided in infrastructure design (`components.md`).

## Sources

- `components.md` and `decisions.md` in `inception/domain-design/`: the building blocks, entities and ADR-001 to ADR-008, including the dedicated `Transactions` table.
- `requirements.md` in `inception/requirements-analysis/` and `stories.md` in `inception/user-stories/`.
- `team-practices.md` in `inception/practices-discovery/`: repos, walking skeleton, testing posture and deployment.
- `units-generation-questions.md` in this stage's directory: Q1 to Q3 and the approved plan.
