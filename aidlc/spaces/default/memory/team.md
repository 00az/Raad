# Team-Level Rules

> This team's affirmed practices and corrections. Loaded after `org.md` as
> strict-additive guidance; contradictions with broader policy are rejected.
> Populated by the practices-discovery affirmation gate. Edit at the gate,
> not directly.

## Way of Working

Two engineers work on RAAD, and each of us uses AI-DLC. Who owns which repo is agreed in delivery planning.

RAAD has one repo per service. Every repo is private, under the `00az` account on GitHub, and has `main` as its default branch.

| Repo | What it holds | When |
|---|---|---|
| `Raad` (this repo) | The platform (described below) and the planning and design record (`aidlc/`). | MVP |
| `RaadMoneyService` | The money core: accounts, wallets, wallet-to-wallet transfers and transfer history, in Python on AWS. It is the only service that changes wallet balances; any other service that needs money moved asks it to. | MVP |
| `RaadMobile` | The Flutter app for iOS and Android. | MVP |
| `RaadWeb` | The landing page, a static site on S3 and CloudFront. | MVP |
| `RaadAiService` | The AI assistant that summarises a user's transaction history and gives recommendations. | After the MVP |
| Qattah (repo not created yet) | Group money pooling, modelled on how the Barq app does it, in its own service repo set up the same way as the others. It moves money only by asking `RaadMoneyService`. | After the MVP |

`Raad`'s platform is the set of shared pieces every service relies on: the public API domain and its certificate, with API mappings that send each path prefix to the service that owns it (for example `/money` to the money service, and later `/ai` and `/qattah`), so each service keeps its own API and endpoints without changing `Raad`; user sign-in through one shared user pool; the shared event bus; and the API firewall and rate limits. This is the repo's intended responsibility, and domain design confirms the final design.

In every repo:

- We use trunk-based development on `main`. Each change is made on its own short-lived branch from `main` that lives a day or two at most. We keep no long-lived `develop`, `release/*` or per-environment branches: each repo's pipeline promotes a commit from `dev` to `stg` to `prd`, so environments never need branches of their own.
- Every change reaches `main` through a pull request. A pull request merges only when the repo's CI checks pass and the other engineer has approved it.
- `main` is protected: nobody pushes to it directly, and nobody force-pushes it.
- Pull requests are squash-merged, so each change lands on `main` as one commit.
- Before a pull request is opened, the repo's full check suite passes on the branch locally. GitHub Actions runs the same commands on the pull request and again on every push to `main`, so a green local run and a green CI run mean the same thing. The run on `main` starts that repo's deploy pipeline, described under Deployment.
- If a repo's `main` goes red, we fix it or revert it before anything else lands in that repo.

## Walking Skeleton

We build a walking skeleton first on every greenfield project: the thinnest slice that runs the whole way through, built first to prove the pieces connect before the real features go in. For RAAD the first slice spans three repos and runs against `dev` on AWS: `Raad` provides sign-in and the API domain, `RaadMoneyService` provides the balance and one transfer, and `RaadMobile` provides the screens. A test user signs in on the phone, sees their SAR balance, sends one simulated transfer to another RAAD wallet, and sees that transfer in their history. The slice goes through the real sign-in, API, data store and each repo's deployment path; the landing page in `RaadWeb` is not part of it. Our proposed verification is an API smoke script run against the deployed `dev` API plus a Flutter integration test run on a simulator against `dev`; it becomes the Construction Verification Command only once the person authorises it at Construction. The skeleton is approved before any other work starts, and later work adds features on top of the proven path.

## Testing Posture

- **Methodology**: custom
- **Methodology evidence**: We chose this mixed cadence at the practices interview. RAAD's central risk is money movement: balances must be right after every transfer, and a repeated request must never move money twice. In that small core of `RaadMoneyService` the tests are the specification, so writing them first costs little and catches the defects that matter most. Everywhere else, the org default cadence (test-after) keeps us on the short timeline. This posture differs from the org default only for the money-movement core.
- **Ordering**: For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.
- **Coverage**: Each backend repo (`Raad`, `RaadMoneyService` and later `RaadAiService`) and the mobile repo (`RaadMobile`) holds at least 80% line coverage on its own. The money-movement core in `RaadMoneyService` also holds at least 95% line and branch coverage. We never lower a floor to make a step pass, and coverage on `main` never decreases in any repo. `RaadWeb` is static HTML and CSS with no code to measure; its smoke test checks it after every deploy.
- **Money-movement checks** (in `RaadMoneyService`, required in addition to coverage):
  - Property-based tests with Hypothesis show that, for any sequence of transfers, the total money across all wallets stays the same and no balance goes below zero.
  - A replay test shows that sending the same transfer request again returns the original result and moves money exactly once.
  - A concurrency test shows that simultaneous transfers out of one wallet can never overdraw it. It runs against a real local container of the data store in Docker, not a mock.
  - Rejection tests cover insufficient funds; a zero, negative or over-precise amount; an unknown recipient; a transfer to oneself; an unauthenticated caller; and access to another user's wallet.
- **Test types** (Standard test strategy):
  - Service repos (`RaadMoneyService`, and later `RaadAiService`): unit tests with pytest and Hypothesis, and integration tests against local containers in Docker.
  - Infrastructure (`Raad`'s platform stacks and each service's own stacks): pytest tests of the CDK stacks, alongside the cdk-nag checks that run on every synth.
  - `RaadMobile`: unit and widget tests with `flutter test`, and end-to-end tests with `integration_test` on an iOS simulator and an Android emulator.
  - Deployed environments: each deployable repo's pipeline runs a smoke test against the environment after every deploy. A service's smoke test calls its deployed API, `RaadWeb`'s fetches the landing page, and `Raad`'s checks the shared pieces it deployed (for example that the API domain answers and a test user can sign in).
- **CI**: Each repo's full suite runs in GitHub Actions on every pull request, and a pull request merges only when the suite is green. The suite runs again on every push to `main`. Any failure blocks.
- **Setup**: Each repo's README documents one setup command and one test command, and lists that repo's prerequisites: in the Python repos, `uv`, Node.js for the AWS CDK CLI, and Docker where the tests or builds need it; in `RaadMobile`, the pinned Flutter SDK and, for the simulator tests and app builds, Xcode with CocoaPods and the Android SDK.

## Guard Policy

<!-- Affirmed by the team. Mode: strict, relaxed, or off. Strict here holds for every intent, whatever one person asks in chat; relaxed or off here applies to every intent whose policy came from its scope, unless project.md or the person sets another; changing this line changes it. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

- All infrastructure is code, written with the AWS CDK in Python. Each repo keeps the infrastructure it deploys, versioned with its code: `Raad` holds the shared platform stacks, and each service repo holds its own stacks. Nothing is created or changed by hand in the AWS console.
- cdk-nag runs the AwsSolutions rules on every synth in every repo that has CDK code, and any finding blocks. A suppression is allowed only with its reason written next to it in the code.
- We run three environments named exactly `dev`, `stg` and `prd`, all in one AWS account, in `us-east-1` for now; the region is revisited in infrastructure design. Each environment is its own set of stacks with its own data and its own users, and each repo deploys its part into all three.
- Each deployable repo (`Raad`, `RaadMoneyService`, `RaadWeb` and `RaadMobile` in the MVP, and each later service repo) has its own pipeline in GitHub Actions, and every pipeline promotes a commit the same way:
  - Every merge to `main` deploys that commit to `dev` once the repo's check suite is green, then runs `dev`'s smoke test.
  - When `dev`'s smoke test passes, the same commit deploys to `stg` automatically, then runs `stg`'s smoke test.
  - `prd` deploys only after a person approves a version that has already passed on `stg`, as a step in that repo's pipeline. The `prd` smoke test then runs against it.
- `Raad`'s platform is deployed first in each environment, because the services depend on its sign-in, API domain and event bus. When a service needs a new platform piece, that piece reaches the environment through `Raad`'s pipeline before the service change that uses it.
- GitHub Actions reaches AWS through OpenID Connect with a short-lived role. We store no AWS access keys anywhere. On our laptops we use AWS SSO.
- `RaadWeb`'s pipeline deploys the landing page as a static site on S3 behind CloudFront, one per environment.
- `RaadMobile`'s pipeline builds the Flutter app (iOS and Android) once per environment, with a build flavour that points it at that environment's API. Testers get it through TestFlight on iOS and Google Play internal testing on Android; there is no public store release in the MVP. iOS builds need macOS with Xcode, either on a laptop or on a GitHub Actions macOS runner.
- To roll back, we redeploy the last known-good commit of the affected repo, either by re-running its deploy job or by reverting on `main` through a pull request and letting the pipeline redeploy. For the mobile app this means building the last known-good commit again with a new build number and sending it to testers the same way.
- In `prd`, data stores are kept when a stack is deleted and have point-in-time recovery turned on. Schema changes are additive: we expand first and contract in a later release.
- A deploy counts as done only when its smoke test passes. A failed smoke test stops the commit from going any further.

## Code Style

- We use two languages, Python and Dart, plus plain HTML and CSS for the landing page:
  - Python in `Raad` (the platform's CDK code), `RaadMoneyService` and later `RaadAiService`.
  - Dart (Flutter) in `RaadMobile`.
  - Plain static HTML and CSS in `RaadWeb`. Everything beyond the landing page lives in the mobile app.
- Python (in `Raad`, `RaadMoneyService` and later `RaadAiService`):
  - We pin one Python version across these repos, the newest runtime AWS Lambda supports, for local work, CI and Lambda. If a laptop's default Python is newer, the pinned version still wins.
  - `uv` manages environments and dependencies, with a committed `uv.lock` in each repo; CI installs from that lockfile.
  - Ruff formats and lints; CI checks both, and any error blocks.
  - mypy runs in strict mode, and any error blocks.
  - Tests use pytest and Hypothesis.
  - `pip-audit` checks dependencies, and a high or critical finding blocks.
  - Names follow PEP 8: snake_case for functions, variables and modules, and PascalCase for classes.
- Dart and Flutter (in `RaadMobile`):
  - We pin one Flutter version for local work and CI, with a committed `pubspec.lock`.
  - `dart format` formats the code, and CI checks it.
  - `flutter analyze` runs with the official `flutter_lints` rules, and warnings fail the check.
  - Names follow Dart idiom: lowerCamelCase for variables and functions, UpperCamelCase for types, and snake_case for file names.
- Each service's OpenAPI spec lives in that service's repo and is the single source of truth for its API. The service validates requests against it, and `RaadMobile` generates its Dart API client from it, so a change to an API starts in its spec.
- Agents read the formatter and linter configuration of the repo they work in first. They suggest style only where those tools do not already cover it.
## Forbidden

<!-- Team-specific forbidden patterns -->

## Mandated

<!-- Team-specific mandates -->

## Corrections

<!-- Self-learning loop appends here. -->
