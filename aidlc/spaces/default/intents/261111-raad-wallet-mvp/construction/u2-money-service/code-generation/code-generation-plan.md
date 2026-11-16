# Code Generation Plan — U2 Money Service

Conversation language: English.

This plan builds only U2's remaining MoneyService behavior in the `RaadMoneyService` repository. Infrastructure resources are designed in the approved Infrastructure Design artifacts; this stage implements the service changes and their tests. No resources are deployed as part of code generation.

## Implementation Steps

- [x] Inspect the current `RaadMoneyService` source, OpenAPI, dependency lock, CI workflow, and tests. Preserve existing U1 behavior and enumerate changed source paths for the Unit manifest.
- [x] Establish/update the Python package and test runner configuration only where required; keep Python 3.12, `uv.lock`, Ruff, strict mypy, pytest, Hypothesis, Docker-backed integration testing, and the existing repository conventions.
- [x] **TDD — money core Red:** add failing tests for the inclusive 100–50,000 halala range, invalid amount precision, self-transfer refusal, insufficient funds, unique `R-` references, and deterministic first business outcome for a sender/request-key pair.
- [x] **TDD — money core Green/Refactor:** implement the domain and persistence operations that make those tests pass while preserving integer-halalas arithmetic and transactional balance invariants.
- [x] **TDD — request-key/replay Red:** add failing tests for matching-key replay, different-payload `IDEMPOTENCY_KEY_REUSED`, concurrent duplicate requests, lost-response retry, and retry after a process failure. Resolve the approved design conflict between Functional Design's `reserved` state and Reliability Design's no-durable-reservation model before finalizing assertions; do not silently choose one.
- [x] **TDD — request-key/replay Green/Refactor:** implement atomic conditional writes and replay behavior according to the human-resolved contract; keep outcomes immutable and avoid double movement.
- [x] **TDD — history Red:** add tests for sent/received merge ordering, timestamp/UUID tie-break, default and maximum page sizes, snapshot boundary, cursor binding/expiry/tampering, and no duplicate or skipped rows.
- [x] **TDD — history Green/Refactor:** implement bounded key queries, stable pagination and batched counterparty resolution without table scans.
- [x] **TDD — directory Red:** cover duplicate normalized email ownership, recipient not found, exact lookup, and no cross-user ownership leakage.
- [x] **TDD — directory Green/Refactor:** implement uniqueness conditions and safe refusal responses without personal data in logs.
- [x] **Test-after — API layer:** complete C1 operations and error mapping in the existing handler; add pytest API tests for each success/refusal/error response, authentication/authorization, request validation, cursor behavior and OpenAPI compatibility.
- [x] **Test-after — C2 consumer:** implement the account-confirmed handler and event validation/deduplication using the designed target contract; add consumer tests for valid, duplicate, wrong-environment, malformed and persistence-failure events, including retry/DLQ expectations.
- [x] **Test-after — storage integration:** add Docker-backed tests against the repository's supported local DynamoDB-compatible container for transaction atomicity, simultaneous wallet setup, duplicate transfers and concurrent withdrawals. Do not substitute an in-memory mock for the required concurrency test.
- [x] **Test-after — service infrastructure:** extend Python CDK stacks for `dev`, `stg` and `prd` with the two tables, Lambda/Function URL invocation boundary, scoped roles/configuration, C2 target and DLQ, monitoring and recovery settings from `infrastructure-specification.md`; add CDK assertions and `cdk-nag` checks.
- [x] Add or update API/contract fixtures and smoke-check configuration needed by U2, using only designated test identities and simulated SAR.
- [x] Run formatting, lint, strict type check, unit and available Docker-backed integration tests, coverage, dependency audit, CDK synth/assertions/`cdk-nag`, and OpenAPI checks. Preserve the 80% repo line floor and 95% line and branch floors for the money-movement core; report any unavailable check rather than lowering a threshold.
- [ ] Update source manifest, traceability, code summary and test instructions. Document any deviations and tests not run with reasons.

## Story and Requirement Traceability

| Plan area | Story / acceptance coverage |
|---|---|
| Amount rules, self-transfer, funds and keyed outcomes | US3.3, US3.5–US3.8; AC3.3.*, AC3.5.*, AC3.6.*, AC3.7.*, AC3.8.* |
| Stable history and continuation cursor | US4.3; AC4.3.* |
| Account-confirmed wallet setup and service environment behavior | US1.2, US6.2; AC1.2.*, AC6.2.* |
| Isolation, atomicity, replay and performance targets | NFR3, NFR4, NFR6; detailed IDs in NFR design and code-generation traceability |

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
