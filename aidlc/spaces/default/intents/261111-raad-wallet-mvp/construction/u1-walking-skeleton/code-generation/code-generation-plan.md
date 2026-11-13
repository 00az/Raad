# Code Generation Plan — U1 Walking Skeleton

Conversation language: English.

## Summary

- Builds: the first integrated RAAD wallet slice across platform, money service and Flutter app, with repo work split between both engineers.
- Touches: Engineer 1 / AI developer on `Raad` and `RaadMoneyService`; Engineer 2 (co-engineer) on `RaadMobile` at `../mobile`.
- Tests: at least 40 unit/widget cases, local-store/API integration tests, and dev smoke and Flutter integration checks.

## Scope and Boundaries

Implement US1.2's authenticated wallet safety net, US1.3's sign-in check, US2.1's balance screen, US3.1/US3.2/US3.4's recipient review and one transfer, US4.1/US4.2's first history page, and US6.1/US6.4's opening-balance and dev walking-skeleton checks. Keep whole-halalas accounting, atomic wallet creation and transfer, verified caller identity, C1 wire shapes, and the approved privacy boundaries.

The unit definition identifies `Raad` as the shared platform repo, `RaadMoneyService` as the money service repo, and `RaadMobile` as the Flutter repo. Their current local folders are `Raad` (this workspace), `../money-service`, and `../mobile`; the latter two are empty checkouts with their expected GitHub remotes. The implementation first confirms the registered repo mapping and works within those checkouts. It does not add a duplicate checkout or overwrite user-authored files.

## Parallel Work Split

Follow the approved delivery allocation so both engineers can work side by side without editing the same repository:

| Workstream | Owner | Repository ownership | Work |
|---|---|---|---|
| Platform and money service | Engineer 1 leads; the AI developer agent builds alongside that owner | `Raad` and `RaadMoneyService` | CDK platform/edge, MoneyApi, Ledger, WalletDirectory, setup utility, backend tests and dev integration endpoint. |
| Mobile app | Engineer 2 (co-engineer) leads | `RaadMobile` | Flutter client/screens, widget and integration tests, and mobile dev configuration. |
| Integration | Both engineers review; Engineer 1 owns the API/config handoff | All three repos | Freeze the pinned C1 contract and environment config shape first. Then the two workstreams proceed in parallel using the contract stub/fake server; integrate and verify against dev when both are ready. |

Use separate short-lived branches in each repository, commit only within that repo, and open the three pull requests for the walking skeleton. Engineer 1 reviews `Raad` and `RaadMoneyService`; Engineer 2 reviews `RaadMobile`; both review the integrated U1 behavior. The AI developer agent must not edit `RaadMobile` while Engineer 2 owns that workstream. This is the U1 implementation split; it does not change the later Bolt sequence or repo ownership in `team-allocation.md`.

U1 does not implement sign-up/resend/reset screens, U2's complete request-key replay and amount limits, U3's full app/session behavior, U4's event-confirmation signal and C2 dead-letter resources, U5's landing page, or production provisioning. Keep the accepted Functional Design concerns visible in code and tests: missing holder setup/repair details, GET-versus-PUT mismatch, public field mapping, missing displayed values, fixture readiness, history tie order, and amount-text conversion. Do not silently claim those concerns are resolved by this plan.

### Proposed Implementation Boundaries

- Keep the platform edge adapter behind API Gateway HTTP API and the C1 path. The MoneyApi integration remains behind a narrow forwarding interface. Propose an IAM-authenticated Lambda Function URL for MoneyApi, with the URL published by the service deployment in an environment-scoped SSM parameter and read by the platform deployment. Use SigV4 from the edge adapter. This keeps the C1 request over HTTPS and restricts invocation to the platform role. Confirm the exact output/permission wiring during implementation; fail closed when the parameter or target is missing. This addresses the open edge-to-service integration review concern without changing the approved infrastructure artifact.
- Parameterize the public domain, Route 53 hosted-zone ID and certificate configuration. Provision the CloudFront viewer certificate in `us-east-1`, create the DNS alias in the supplied hosted zone, and keep the stack blocked until environment values are supplied. Do not invent a public hostname.
- Keep the U1 dead-letter email parameter for the three U1 operational alarms. C2's `UserConfirmed` bus, retry/dead-letter resources and alarm are owned by U4/U2; carry the same email parameter and an explicit handoff there. U1 creates no account-confirmation event resource.

## Implementation Steps

1. [ ] **Establish the repo and project skeletons.** Both engineers confirm the `Raad`, `RaadMoneyService`, and `RaadMobile` paths and repository identities. Engineer 1 adds Python `uv` project/lock files and pytest configuration to the two Python repos; Engineer 2 adds the minimum Flutter package and test setup to the mobile repo. Add only new files or files named below; leave existing README, `.gitignore`, `AGENTS.md`, and user configuration unchanged.
2. [ ] **Make test runners ready before the first test.** Add test dependencies/configuration: pytest, pytest-cov and Hypothesis for Python; CDK assertion support and cdk-nag checks for platform infrastructure; Flutter `flutter_test` and `integration_test`. Record the commands in `unit-test-instructions.md`. Do not run an executable test before its runner is ready.
3. [ ] **Implement the Ledger money rules test-first (TDD).** Engineer 1 and the AI developer agent work in `RaadMoneyService`: write failing unit tests for positive whole-halalas arithmetic, exact-balance debit, insufficient balance, one 100,000-halala opening credit, all-or-nothing transfer, and conservation/non-negative balances; then implement the smallest passing Ledger domain logic and refactor while green. This unit does not implement durable request-key replay; that belongs to U2.
4. [ ] **Implement the DynamoDB data layer test-after.** Engineer 1 and the AI developer agent add Ledger and WalletDirectory table definitions/adapters with conditional wallet-owner/email uniqueness, transactional wallet opening and transfer writes, strongly consistent bounded first-page history query, exact email normalization and batched counterparty lookup. Add a local DynamoDB container configuration, then write and run 5–8 repository/integration cases per data component. Use isolated tables and fixture data; never insert user fixtures directly into dev tables.
5. [ ] **Implement MoneyApi and C1 adapters test-after.** Engineer 1 and the AI developer agent add bearer-token verification from immutable environment C5 configuration, profile lookup from the configured Cognito source with subject matching, setup safety net, balance, recipient lookup, one transfer and first-page history handlers. Validate input/output against the pinned C1 OpenAPI contract; ignore caller-selected wallet identity; preserve bounded timeouts and no transfer-write retry. Write and run 5–8 handler cases per component, including safe errors, wrong-environment tokens, header spoofing, and unknown transfer outcomes.
6. [ ] **Implement the shared platform infrastructure and edge test-after.** Engineer 1 and the AI developer agent work in `Raad`: add Python CDK app/stacks for Cognito, CloudFront, WAF, API Gateway HTTP API, the edge adapter, environment-specific verifier configuration, Secrets Manager correlation HMAC profile, CloudWatch log groups/metrics/alarms/dashboard, SNS email subscription, DNS alias and CloudFront certificate configuration. Add the IAM-authenticated MoneyApi Function URL integration, SigV4 forwarding, environment SSM output/parameter, and fail-closed unavailable-target behavior. Add CDK assertions and 5–8 tests per stack, plus cdk-nag on every synth. Accept environment parameters for hostnames, hosted-zone ID and notification email.
7. [ ] **Implement the Flutter skeleton test-after in parallel.** Engineer 2 (co-engineer) works in `RaadMobile`: generate the Dart client from the pinned C1 contract and add sign-in, wallet, send form/review/result and first-history screens in English. Store tokens only in phone secure storage, render whole halalas as SAR, disable duplicate confirmation while a transfer is in flight, and show safe errors. Add stable `ValueKey`/`data-testid` equivalents for interactive widgets and 5–8 widget/unit cases per screen component. Start after the C1 contract and environment config shape are frozen; use a contract fake server while the backend is in progress.
8. [ ] **Add the two-user setup and integrated checks.** Engineer 1 adds a setup utility that obtains test-user passwords from Secrets Manager at runtime, provisions confirmed dev users through supported Cognito operations, and initializes both wallets through C1. Engineer 2 adds Flutter `integration_test` coverage for sign-in, balance, recipient review, one 100-SAR transfer and sent/received history. Run MoneyApi local-container integration checks and connect both app and API paths to dev after the parallel workstreams reach the C1/config handoff. Use isolated run-labelled fixtures and verify readiness before timing.
9. [ ] **Add dev deployment and observability checks.** Add GitHub Actions workflows with repository/environment-scoped OIDC roles, dev-first deployment order (`Raad`, then `RaadMoneyService`, then mobile environment config), secret/dependency scanning, coverage gates and post-deploy smoke checks. Include alarm injection, safe log scans, edge/service HMAC correlation matching and the accepted 100-user/10-active-user performance command. Keep `scripts/verify-dev.sh` as the designated integrated verification command; run it only when the Construction verification step is authorized.
10. [ ] **Complete docs and traceability.** Add project-specific setup/test commands in each repo's own notes only if the repo has no user-authored README; otherwise keep all run instructions in `code-summary.md` and `unit-test-instructions.md`. Record every source path in `source-manifest.json`, map every assigned AC/NFR/business rule to an existing implementation or test file, and state tests not run with their reason.

## Story-to-Step Traceability

| Plan step | Stories and acceptance coverage |
|---|---|
| 1–2 | US6.1 and US6.4 — both owners prepare their repo runners before the integrated dev check; no acceptance result is claimed here. |
| 3–5 | US1.2, US1.3 — safe wallet opening and per-request verified sign-in; US2.1 — own balance; US3.1, US3.2, US3.4 — recipient review, one atomic send and balance check; US4.1, US4.2 — own first history page. |
| 6 | US1.2, US1.3, US6.1 — shared pool, public `/money` edge, basic firewall, environment token profile and monitoring infrastructure. |
| 7 | US1.3, US2.1, US3.1, US3.2, US3.4, US4.1, US4.2 — Engineer 2's sign-in, wallet, send/review/result and history user flows. |
| 8–9 | US1.2, US6.1, US6.4 — provision two supported test users/wallets and verify the integrated dev slice and opening balances. |
| 10 | All U1 stories above — source ownership and requirement/acceptance traceability. |

## Test Files and Coverage Plan

Standard strategy applies with the team's custom ordering. Plan at least 5–8 cases for each logical component: platform identity/edge stacks, platform monitoring stack, Ledger rules, Ledger repository, WalletDirectory repository, MoneyApi handlers, and the four Flutter screen components. Add integration coverage at the DynamoDB transaction, C1 API, platform-to-MoneyApi forwarding, and Flutter-to-dev boundaries. Keep 80% line coverage in each backend/mobile repo and 95% line and branch coverage for the Ledger money core. Add the property test for conservation/non-negative balances and the real local-container transaction/concurrency checks. Do not lower a floor to make a run pass.

Expected test files:

- `Raad/infrastructure/tests/test_identity_stack.py`, `test_public_edge_stack.py`, `test_monitoring_stack.py`.
- `RaadMoneyService/tests/unit/test_ledger_rules.py`, `test_ledger_repository.py`, `test_wallet_directory.py`, `test_money_api.py`; `tests/integration/test_dynamodb_transactions.py`, `test_c1_api.py`, `test_edge_forwarding.py`.
- `RaadMobile/test/sign_in_test.dart`, `wallet_screen_test.dart`, `transfer_flow_test.dart`, `history_screen_test.dart`; `integration_test/walking_skeleton_test.dart`.
- `RaadMoneyService/pyproject.toml`, `Raad/infrastructure/pyproject.toml`, and `RaadMobile/pubspec.yaml` carry the minimal runner/dependency configuration; Python coverage config retains both repo and Ledger-specific floors.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.",
  "scope": "classic",
  "test_strategy": "standard",
  "project_type": "greenfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Methodology evidence**: We chose this mixed cadence at the practices interview. RAAD's central risk is money movement: balances must be right after every transfer, and a repeated request must never move money twice. In that small core of `RaadMoneyService` the tests are the specification, so writing them first costs little and catches the defects that matter most. Everywhere else, the org default cadence (test-after) keeps us on the short timeline. This posture differs from the org default only for the money-movement core.\n- **Ordering**: For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.\n- **Coverage**: Each backend repo (`Raad`, `RaadMoneyService` and later `RaadAiService`) and the mobile repo (`RaadMobile`) holds at least 80% line coverage on its own. The money-movement core in `RaadMoneyService` also holds at least 95% line and branch coverage. We never lower a floor to make a step pass, and coverage on `main` never decreases in any repo. `RaadWeb` is static HTML and CSS with no code to measure; its smoke test checks it after every deploy.\n- **Money-movement checks** (in `RaadMoneyService`, required in addition to coverage):\n  - Property-based tests with Hypothesis show that, for any sequence of transfers, the total money across all wallets stays the same and no balance goes below zero.\n  - A replay test shows that sending the same transfer request again returns the original result and moves money exactly once.\n  - A concurrency test shows that simultaneous transfers out of one wallet can never overdraw it. It runs against a real local container of the data store in Docker, not a mock.\n  - Rejection tests cover insufficient funds; a zero, negative or over-precise amount; an unknown recipient; a transfer to oneself; an unauthenticated caller; and access to another user's wallet.\n- **Test types** (Standard test strategy):\n  - Service repos (`RaadMoneyService`, and later `RaadAiService`): unit tests with pytest and Hypothesis, and integration tests against local containers in Docker.\n  - Infrastructure (`Raad`'s platform stacks and each service's own stacks): pytest tests of the CDK stacks, alongside the cdk-nag checks that run on every synth.\n  - `RaadMobile`: unit and widget tests with `flutter test`, and end-to-end tests with `integration_test` on an iOS simulator and an Android emulator.\n  - Deployed environments: each deployable repo's pipeline runs a smoke test against the environment after every deploy. A service's smoke test calls its deployed API, `RaadWeb`'s fetches the landing page, and `Raad`'s checks the shared pieces it deployed (for example that the API domain answers and a test user can sign in).\n- **CI**: Each repo's full suite runs in GitHub Actions on every pull request, and a pull request merges only when the suite is green. The suite runs again on every push to `main`. Any failure blocks.\n- **Setup**: Each repo's README documents one setup command and one test command, and lists that repo's prerequisites: in the Python repos, `uv`, Node.js for the AWS CDK CLI, and Docker where the tests or builds need it; in `RaadMobile`, the pinned Flutter SDK and, for the simulator tests and app builds, Xcode with CocoaPods and the Android SDK."
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:67e5bbb80db5d51b2847a7275866f774aaee32fcb4f9b6c3ad6d429836b14ece",
  "contract_sha256": "sha256:7d7f077a74e1c8ed59b1ec6ddd9f041d8db0c6a93d62e46cc8c573d062f59d5e"
}
```

## Assumptions & Open Questions

- The plan proposes an IAM-authenticated MoneyApi Lambda Function URL and environment SSM parameter because the approved Infrastructure Design review left the edge-to-service integration open. The plan is not implementation authorization; Plan Approval is required.
- Public API domain, hosted-zone ID, certificate details and SNS email are deployment inputs that the team supplies. No public domain or live subscription is invented.
- The exact Git workspace registration names for the sibling repo folders are confirmed before source edits. If they are not registered, use the supported repo-add command rather than creating a second checkout.
- C1 field mapping, holder repair, amount conversion and history ordering remain accepted Functional Design risks. The plan tests the pinned contract and reports incompatibilities; it does not change approved design files without a request.

