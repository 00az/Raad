# Practices Discovery: Questions

These questions settle how RAAD will be built, tested and deployed. The release
engineer's draft in `team-practices.md` suggests an answer for each one, marked
"(Recommended)". Anyone can answer any question; the trade in brackets only
says whose call it usually is.

## Q1. [Release engineer] How should finished work reach `main` and GitHub?

Each piece of work is built on its own short-lived branch. This decides how it
lands back on `main`.

A. Squash each piece into one commit on `main` locally, then push. No pull requests while you're the only developer; add them when a second person joins. (Recommended)
B. Open a pull request on GitHub for each piece and merge it once CI passes.
C. Commit straight to `main` with no branches.
X. Other (please specify)

[Answer]: A (left to the conductor: "your recommendionts"; 2026-11-11T16:22:53Z; **Mode:** chat)

## Q2. [Release engineer] Which AWS environments do you want, and what triggers a deploy to each?

A. Two environments, `dev` and `prod`. `dev` deploys automatically on every push to `main`; `prod` deploys only after you approve it, and only a version that already passed on `dev`. (Recommended)
B. One environment (`dev`), deployed automatically on every push to `main`.
C. One environment, deployed by hand from your laptop (`cdk deploy`) when you choose.
D. Two environments (`dev` and `prod`), both deployed by hand.
X. Other (please specify)

[Answer]: X. Three environments: `dev`, `stg` and `prd` ("for the envs we want 3: prd, stg and dev"). Triggers are settled in Q10. (2026-11-11T16:22:53Z; **Mode:** chat)

## Q3. [Release engineer] The current plan stops after build and test. Where should the CI and deployment work get built?

The classic plan you picked skips the CI pipeline and all deployment stages, but
your request and the SOW both require the app to run on AWS, and the SOW asks
for basic monitoring.

A. Add the CI and deployment stages to the plan: CI pipeline, deployment pipeline, environment provisioning and deployment execution. (Recommended)
B. Same as A, and also add observability setup to cover the SOW's "basic monitoring".
C. Keep the plan as it is and build the deploy scripts and GitHub Actions workflow as part of code generation.
D. No deploy automation for the MVP: you deploy by hand outside this workflow.
X. Other (please specify)

[Answer]: A (left to the conductor: "your recommendionts"; 2026-11-11T16:22:53Z; **Mode:** chat)

## Q4. [Release engineer] Build a thin end-to-end slice first?

A walking skeleton is a minimal version that runs the whole way through, built
first to prove the pieces connect before the real features go in.

A. Yes, on AWS: a test user signs in, sees their SAR balance, sends one transfer and sees it in their history, deployed to `dev` and checked by a smoke script. You approve it before other work starts. (Recommended)
B. Yes, but on your machine only at first; AWS comes later.
C. No. Build the features one at a time.
X. Other (please specify)

[Answer]: A, in the mobile app: a test user signs in on the phone, sees their SAR balance, sends one transfer and sees it in their history, against the `dev` backend on AWS (left to the conductor: "your recommendionts"; 2026-11-11T16:22:53Z; **Mode:** chat)

## Q5. [Quality engineer] Should tests come before the code or after it?

The SOW's biggest risks are wrong balances and transfers that go through twice.
Writing those tests first makes them the specification.

A. Tests first (TDD) for the money logic: amounts, balances, transfer rules and duplicate handling. Tests right after the code for everything else. (Recommended)
B. Tests right after the code everywhere (the framework default).
C. Tests first (TDD) everywhere.
X. Other (please specify)

[Answer]: A (left to the conductor: "your recommendionts"; 2026-11-11T16:22:53Z; **Mode:** chat)

## Q6. [Quality engineer] How strict should the test bar be?

A. At least 80% line coverage overall, at least 95% line and branch coverage on the money logic, plus dedicated tests: balances always add up and never go negative, a repeated request moves money only once, simultaneous transfers can't overdraw a wallet, and every rejection case is covered. (Recommended)
B. At least 80% line coverage overall, plus the repeated-request and rejection tests only.
C. At least 80% line coverage overall, nothing extra.
X. Other (please specify)

[Answer]: A (left to the conductor: "your recommendionts"; 2026-11-11T16:22:53Z; **Mode:** chat)

## Q7. [Developer] Which language and code tooling?

A. TypeScript everywhere (infrastructure, backend and web app) in strict mode, with Prettier and ESLint. Node.js pinned to the newest version AWS Lambda supports. (Recommended)
B. Python for the backend (Ruff, pytest) with TypeScript for the infrastructure and web app.
C. Python for the backend and the infrastructure, TypeScript for the web app only.
X. Other (please specify)

[Answer]: X. The mobile app is Flutter (Dart) on iOS and Android ("we want to use flutter both ios and andriod"); the backend is Python ("Python"); the web app is only a landing page and everything else is in the mobile app ("we want landing page in the web app and everything else will be in the mobile app"). (2026-11-11T16:22:53Z; **Mode:** chat)

## Q8. [Developer] Which tool should define the AWS infrastructure as code?

A. AWS CDK in TypeScript, with automatic security checks (cdk-nag) on every build. (Recommended)
B. AWS SAM templates.
C. Terraform.
X. Other (please specify)

[Answer]: X. AWS CDK in Python, with cdk-nag security checks on every build. Left to the conductor ("your recommendionts"); Python rather than TypeScript because the backend is Python, which keeps the project to two languages (Dart and Python). (2026-11-11T16:22:53Z; **Mode:** chat)

## Q9. [Security engineer] Which of these should be standing rules for the project? (select all that apply)

Anything you pick here is recorded as a hard rule that every later step must
follow.

A. Never commit secrets, passwords or AWS keys to the repo (use SSO on your laptop and short-lived credentials in CI).
B. Always store and calculate money as whole halalas (1 SAR = 100 halalas), never as decimals.
C. Never connect to real payment systems or accept real card or bank details; funds are simulated and SAR is the only currency.
D. Never write passwords, tokens or full personal details into logs.
E. Never deploy to `prod` a version that hasn't passed its checks and smoke test on `dev`.
F. None of these as rules; decide them in the design stages instead.
X. Other (please specify)

[Answer]: A, B, C, D, E ("with these rules", listing all five). (2026-11-11T16:22:53Z; **Mode:** chat)

## Q10. [Release engineer] With three environments (`dev`, `stg`, `prd`), what triggers a deploy to each?

Follow-up to Q2: you asked for three environments, `dev`, `stg` and `prd`.

A. `dev` deploys on every push to `main`; `stg` deploys automatically once `dev`'s smoke test passes; `prd` deploys only after you approve a version that passed on `stg`. (Recommended)
B. `dev` deploys on every push to `main`; `stg` deploys when you tag a release; `prd` deploys after you approve that tagged release.
C. `dev` deploys on every push to `main`; `stg` and `prd` each deploy only after your approval.
X. Other (please specify)

[Answer]: A ("Q10 yes"). (2026-11-11T16:22:53Z; **Mode:** chat)

## Q11. [Platform engineer] Should the three environments share one AWS account or each have their own?

A. One AWS account (the one you're signed in to), with each environment as its own separate set of stacks and data. Simplest for the MVP. (Recommended)
B. A separate AWS account per environment, for stronger isolation between `prd` and the rest.
C. Two accounts: one for `dev` and `stg`, one for `prd`.
X. Other (please specify)

[Answer]: A ("one account"). (2026-11-11T16:22:53Z; **Mode:** chat)

## Q12. [Product manager] Which phones does the mobile app need to run on, and how do people get it for the MVP?

A. iOS and Android, shared with testers through TestFlight and Google Play internal testing; no public store release yet. (Recommended)
B. iOS and Android, published to the public App Store and Google Play.
C. iOS only, through TestFlight.
D. Android only, through Google Play internal testing.
X. Other (please specify)

[Answer]: A ("both ios and andriod"; "TestFlight and Google Play internal"). (2026-11-11T16:22:53Z; **Mode:** chat)
