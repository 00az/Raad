# Units Generation: Questions

Conversation language: English.

Units Generation groups the building blocks in `components.md` (MobileApp, MoneyApi, Ledger, WalletDirectory, LandingPage) and the shared platform into units of work, and says which unit depends on which. Construction then builds the units one at a time, each from functional design to tested code. Which unit is built first, and who builds what, is decided in Delivery Planning, not here.

The practices already settle the repos, that each repo deploys on its own, and that a walking skeleton comes first: a test user signs in on the phone, sees the SAR balance, sends one transfer to another RAAD wallet and sees it in the history, against `dev`, across `Raad`, `RaadMoneyService` and `RaadMobile`, approved before any other work starts. The classic plan turns the framework's own skeleton ceremony off, so the units below carry that practice themselves. None of this is asked again.

Each question suggests an answer marked "(Recommended)". The trade in brackets only says whose call it usually is; anyone can answer any question.

## Q1. [Architect] How should the work be split into units?

Construction builds one unit fully before starting the next. So the split decides whether the skeleton can run end to end before the rest is built.

A. Five units: a skeleton unit first that cuts across `Raad`, `RaadMoneyService` and `RaadMobile`, then one unit per repo to finish each: the money service, the mobile app, the platform and the landing page. Every other unit depends on the skeleton. (Recommended: the slice is proven first, and each repo then has one unit an engineer can own.)
B. Four units, one per repo, with no separate skeleton unit; Delivery Planning makes the skeleton the first slice. (Because each unit is built in full before the next, the end-to-end slice could not run until the app unit was done, which breaks the practice that the skeleton is approved before other work.)
C. A skeleton unit first, then feature units that each cut across the repos: safe transfers, accounts, history, language and accessibility, and the landing page (about six units). (Each feature lands whole, but most units touch two or three repos and need a pull request in each.)
X. Other (please specify)

[Answer]: A (**Mode:** chat)

## Q2. [Architect] After the skeleton, can the money service and the app be built at the same time?

Contract Design, the next stage, writes the complete description of the money API. If the skeleton commits that description to `RaadMoneyService`, the app can generate its client from it and test against a fake server without waiting for the real service.

A. Yes. The skeleton commits the complete API description; the money service and the app are then built in parallel and meet in the end-to-end tests at Build and Test. (Recommended: the two engineers can work at the same time.)
B. No. The app unit waits for the money service unit and tests against the real service.
X. Other (please specify)

[Answer]: B (**Mode:** chat)

## Q3. [Architect] How do the skeleton's test users get their accounts?

The skeleton only needs two users who can sign in. Sign-up and email confirmation would add two screens and email sending to the thinnest slice.

A. A setup script creates two confirmed test users in each environment, with their passwords kept in a secrets store, never in a repo. The sign-up and confirmation screens come in the app unit, and the confirmation signal (Q1 B of Domain Design) in the money service and platform units. The skeleton's wallets open through the safety net at first sign-in. (Recommended: keeps the slice thin.)
B. The sign-up and confirmation screens, and the confirmation signal, are part of the skeleton, so it also proves that path.
X. Other (please specify)

[Answer]: A (**Mode:** chat)

## Plan Approval

The decomposition plan, from the answers above (Q1 A, Q2 B, Q3 A):

| Unit | Directory | Repos | Kind | What it builds | Size |
|---|---|---|---|---|---|
| U1 | `u1-walking-skeleton` | `Raad`, `RaadMoneyService`, `RaadMobile` | none (the full design set) | The thinnest slice on `dev`: the shared sign-in pool and the public API address with `/money`; MoneyApi with the sign-in check, wallet setup through the safety net, balance, recipient lookup, one transfer and the first history page; the Ledger core (opening balance, all-or-nothing transfer with the balance check, whole halalas, built test-first); WalletDirectory (register, find by email, names); the app's sign-in, wallet, send (form, review, result) and history screens; a script that creates two confirmed test users per environment, with passwords in a secrets store; the `dev` deploy path of the three repos; the API smoke script and the app's integration test. | L |
| U2 | `u2-money-service` | `RaadMoneyService` | service | The rest of the money service: amount limits, own-wallet and unknown-recipient refusals, request keys and replay, simultaneous transfers, history paging, the account-confirmed entry point, safe errors and logs, and the complete API description. | L |
| U3 | `u3-mobile-app` | `RaadMobile` | ui | The rest of the app: sign-up, confirmation code and resend, password reset, staying signed in, sign-out, the out-of-date balance, the lost-answer and offline rules, empty and error views, Arabic and right-to-left, and accessibility. | L |
| U4 | `u4-platform` | `Raad` | packaging | The rest of the shared platform: the sign-in settings (one account per email ignoring capitals and spaces, the same refusal for a wrong password or an unconfirmed account, code resend, password reset, password rule, session lengths), rate limits and firewall, the wiring of the account-confirmed signal, and per-environment setup. | M |
| U5 | `u5-landing-page` | `RaadWeb` | ui | The static Arabic and English page with the "Request test access" button. | S |

Dependencies:

- U2, U4 and U5 depend on U1.
- U3 depends on U1, on U2 (Q2 B: the app tests against the real money service) and on U4 (its account screens test against the real sign-in settings).
- U5's dependency on U1 is a practice dependency, not a code one: the skeleton is approved before any other work starts.
- After U1, U2, U4 and U5 have no dependency between them.

Notes:

- `packaging` is the closest kind for U4, which is infrastructure code with no business logic: it receives the infrastructure, monitoring and pipeline designs, and no business-logic model. U1 has no kind, so it receives the full design set, because it spans all three layers.
- US6.2 (every environment) and US6.4 (acceptance on `prd`) are traced to the Operation stages (environment provisioning and deployment execution), not to a unit.
- Delivery Planning confirms how the skeleton is demonstrated and approved, and the order of U2 to U5.
- Before Code Generation, `RaadMoneyService`, `RaadMobile` and `RaadWeb` join this work, because the units change them.

Approve Plan / Revise Plan

[Answer]: Approve Plan (**Mode:** chat)
