# Code Generation Plan — U1 Walking Skeleton

Conversation language: English.

## Summary

- Builds: the U1 wallet slice with one canonical Transactions row per transfer, atomic balances, public-boundary latency monitoring and separate backend/mobile work tracks.
- Touches: Engineer 1 / AI developer on `Raad` and `RaadMoneyService`; Engineer 2 (co-engineer) on `RaadMobile` at `../mobile`.
- Tests: at least 60 unit/widget cases with 5–8 per component, real DynamoDB transaction/migration integration, public-latency fault checks and API/iOS/Android dev verification.

## Scope and Boundaries

Implement US1.2's authenticated wallet safety net, US1.3's sign-in check, US2.1's balance screen, US3.1/US3.2/US3.4's recipient review and one transfer, US4.1/US4.2's first history page, and US6.1/US6.4's opening-balance and dev walking-skeleton checks. Keep whole-halalas accounting, atomic wallet creation and transfer, verified caller identity, C1 wire shapes, and the approved privacy boundaries.

The unit definition identifies `Raad` as the shared platform repo, `RaadMoneyService` as the money service repo, and `RaadMobile` as the Flutter repo. Their local folders are this workspace, `../money-service`, and `../mobile`. Platform and service source, test/configuration files and lockfiles already exist; the mobile folder currently contains its handoff README. Confirm registered repo identities and current branch/worktree status before source edits. Work in those checkouts and preserve existing edits and history.

The open steps below are the revised work and re-verification required against the approved designs. Earlier source changes and test evidence remain recorded in the existing source manifest and code summary; they do not establish that the new transaction schema or telemetry is implemented. Capture the unchanged-tree test baseline after plan approval and before editing application code. Update the source manifest with every created/modified/deleted path, retaining paths from earlier attempts.

## Parallel Work Split

Follow the approved delivery allocation so both engineers can work side by side without editing the same repository:

| Workstream | Owner | Repository ownership | Work |
|---|---|---|---|
| Platform and money service | Engineer 1 leads; the AI developer agent builds alongside that owner | `Raad` and `RaadMoneyService` | CDK platform/edge, MoneyApi, Ledger, WalletDirectory, setup utility, backend tests and dev integration endpoint. |
| Mobile app | Engineer 2 (co-engineer) leads | `RaadMobile` | Flutter client/screens, widget and integration tests, and mobile dev configuration. |
| Integration | Both engineers review; Engineer 1 owns the API/config handoff | All three repos | Freeze the pinned C1 contract and environment config shape first. Then the two workstreams proceed in parallel using the contract stub/fake server; integrate and verify against dev when both are ready. |

Use separate short-lived branches in each repository, commit only within that repo, and open the three pull requests. Engineer 2 reviews Engineer 1's platform/service PRs; Engineer 1 reviews Engineer 2's mobile PR. Both review the integrated result. Engineer 1 maintains the shared design record and handoff; the AI developer in this checkout writes only platform/service code and the integration wrapper. Engineer 2 owns all mobile source, generated client and mobile test edits in their checkout. This split does not change the later unit order.

U1 does not implement sign-up/resend/reset screens, U2's saved request outcomes/replay and complete amount limits, U3's full app/session behavior, U4's confirmation-event resources, U5's landing page or production provisioning. The current Functional Design fixes setup repair, GET/PUT behavior, C1 shapes, displayed reference/email, fixture readiness, deterministic history order and integer-text conversion; implement and verify those requirements. U1 validates Idempotency-Key syntax but stores no TransferRequest outcome. An uncertain transfer cannot be resubmitted automatically or manually; reconcile through balance/history. U2 adds outcomes and history indexes, starts fresh intents/keys and fabricates no replay records for historical U1 transfers.

### Proposed Implementation Boundaries

- Keep the platform edge adapter behind API Gateway HTTP API and the C1 path. The MoneyApi integration remains behind a narrow forwarding interface. Propose an IAM-authenticated Lambda Function URL for MoneyApi, with the URL published by the service deployment in an environment-scoped SSM parameter and read by the platform deployment. Use SigV4 from the edge adapter. This keeps the C1 request over HTTPS and restricts invocation to the platform role. Confirm the exact output/permission wiring during implementation; fail closed when the parameter or target is missing. This addresses the open edge-to-service integration review concern without changing the approved infrastructure artifact.
- Parameterize the public domain, Route 53 hosted-zone ID and certificate configuration. Provision the CloudFront viewer certificate in `us-east-1`, create the DNS alias in the supplied hosted zone, and keep the stack blocked until environment values are supplied. Do not invent a public hostname.
- Keep the U1 dead-letter email parameter for the three U1 operational alarms. C2's `UserConfirmed` bus, retry/dead-letter resources and alarm are owned by U4/U2; carry the same email parameter and an explicit handoff there. U1 creates no account-confirmation event resource.
- Preserve the original C1 request/token when using the proposed SigV4 integration: sign the outer IAM-authorized Function URL invocation and carry the original method/path/query/body and bearer Authorization in a constructed forwarding envelope. The receiving adapter restores the C1 request before MoneyApi independently verifies the original token. It must not confuse SigV4 Authorization with bearer authorization or trust caller-supplied identity fields. Integration tests cover preservation, unauthorized direct invocation and unavailable configuration.
- Provision Ledger, dedicated Transactions and WalletDirectory tables. Transactions has transferId as its sole primary key and one immutable completed-transfer payload. Ledger contains wallet balances, owner keys and reference-only history lookup entries. One five-action transaction commits both balance updates, the canonical transfer row and both lookup references. Query only the caller's bounded lookup page and strongly batch-read canonical rows, restoring timestamp/transfer-ID order and failing safely on missing/unprocessed records.
- Use the approved CloudFront real-time time-taken measurement through an encrypted telemetry-only Kinesis stream and platform-owned Lambda ingestion/scheduled aggregation. Capture exactly the seven approved safe fields, deduplicate native request IDs, aggregate event windows, and require a complete one-to-one join with load-harness responses before a passing latency result. Lambda handler timing remains diagnostic. Include the initialization-delay proof, missing-data checks and explicit telemetry cost inputs from Infrastructure Design.

## Planned Source Ownership

| Owner/repo | Existing paths to reconcile or modify | New paths planned |
|---|---|---|
| Engineer 1 — Raad | `infrastructure/raad_platform/stacks.py`, `edge/handler.py`, infrastructure tests/configuration, `.github/workflows/ci.yml`, `.github/workflows/deploy-dev.yml`, `scripts/verify-dev.sh` | `infrastructure/raad_platform/telemetry/__init__.py`, `telemetry/handler.py`, `infrastructure/tests/test_public_latency_processor.py`, `test_public_latency_stack.py` |
| Engineer 1 — RaadMoneyService | `src/raad_money/{ledger,storage,api,identity,infrastructure}.py`, `openapi/raad-money-v1.yaml`, unit/integration tests, `scripts/setup_dev_users.py`, `scripts/verify_dev.py`, project/Compose/CI configuration | `scripts/migrate_transactions.py`, `scripts/check_ledger_coverage.py`, `tests/unit/test_transactions_migration.py`, `tests/integration/test_transactions_migration.py` |
| Engineer 2 — RaadMobile | Existing handoff README and the pinned contract handoff are inputs for that engineer | Flutter project/client/screens; `config/dev.json`; four named widget-test files, `test/check_u1_coverage.dart`, and `integration_test/walking_skeleton_test.dart` as listed below |

Paths grouped above are relative to each repo; platform edge/telemetry modules are beneath `infrastructure/raad_platform/`. Shared runtime/package pins are validated against the supported services during implementation, then committed through their owning repo's lockfile. Existing user-authored root README, AGENTS.md and .gitignore have no new edit planned.

## Implementation Steps

1. [x] **Inspect existing work and establish the baseline.** Confirm repo identities, branches and work ownership. Preserve existing edits; inspect the current source manifest and earlier evidence. After approval, run the existing applicable suites before source changes and record failures/tool gaps. Verify registered sibling paths; request any required write access rather than copying code to another checkout.
2. [ ] **Make runners and pins ready.** Reuse the existing Python projects, pytest/Hypothesis/CDK configuration and lockfiles; bootstrap only missing configuration. Engineer 2 bootstraps Flutter and its test runner. Use the exact file-scoped commands in unit-test-instructions.md before each test-first cycle. Pin the current partial C1 release and C4 environment schema through their owning repos; preserve the rendered Testing Contract below.
3. [x] **Reconcile the money core with TDD.** Write failing tests for positive integer money, exact-balance/insufficient-funds behavior, one opening credit, atomic transfer identity and conservation/non-negative balances. Make the smallest passing domain changes and refactor green. Include the one immutable transfer record in the money boundary. Persist no U1 request-key outcome.
4. [x] **Implement the canonical table and adapters test-after.** Define three tables and the transferId primary key. Implement the five-action cross-table transaction with guarded wallet updates and conditional insert, reference-only lookup entries, unique wallet owners and directory emails. Strongly query the bounded caller page, batch-read canonical rows, restore ordering and reject missing/unprocessed/unauthorized rows safely. Add and run repository tests and real DynamoDB Local transaction/concurrency checks, including repeated distinct transfers between the same wallets and fault injection with no partial balances/rows/references.
5. [ ] **Implement an additive migration and safe cutover.** Inspect the deployed schema before activating a new writer. If legacy payloads exist, quiesce writes, validate paired old entries by transferId, conditionally create one canonical row and convert entries to references without changing balances. Reject conflicts/unmatched records for investigation. Test rerun safety, counts, amounts, unchanged balances and both history views. Rollback after cutover must use a version that understands the canonical layout; a reset or legacy writer is not a fallback. No migration or deployment runs during planning.
6. [ ] **Align MoneyApi test-after.** Use explicit PUT /wallet setup and wallet-then-holder repair; GET returns WALLET_NOT_FOUND without creation. Preserve verified sub/profile source, exact C1 names/nesting, the Idempotency-Key header, safe errors, normalization, deterministic first-page history and bounded dependencies. Test directory failure after wallet commit, recovery without another credit, wrong-environment/spoofed identity, failed/uncertain outcomes and no backend transfer retry. Emit no saved U1 replay outcome or replay guarantee.
7. [ ] **Reconcile platform/edge infrastructure test-after.** Implement Cognito capability checks, HTTP API/CloudFront/CLOUDFRONT-scope WAF, safe forwarding with independent verification, the proposed IAM integration/config publication, DNS/certificate configuration, Secrets Manager and the approved correlation profile. Add CDK assertions, edge tests and cdk-nag on every synth. Missing target/configuration fails safely. Supply real environment inputs through approved configuration, not invented values.
8. [x] **Implement the approved public-latency pipeline test-after.** Configure the seven-field 100%-sampling CloudFront real-time log path, encrypted telemetry Kinesis stream, separate no-money-access processor, ingestion log group and scheduled event-window aggregation. Deduplicate native request IDs; compute unique counts/slow fractions; handle delayed/malformed/missing data, query limits and retries without false healthy results. Use native time-taken for public latency and handler timers only for diagnosis. Add 5–8 processor/stack cases each, privacy scans and duplicate-window tests.
9. [ ] **Engineer 2 builds the mobile track test-after.** Pin/generate the C1 client, then implement sign-in, explicit PUT setup, balance, send/review/result and first history in English. Parse SAR text using integer digits, display reference separately from transferId and show counterparty email. An uncertain U1 result blocks automatic/manual resubmit and reconciles with reads. Add stable widget keys, 5–8 cases per component and the mobile coverage checker. Work against a contract fake server until the real dev handoff; Engineer 1 does not edit mobile source.
10. [ ] **Prepare independent fixtures and complete the verification wrapper.** Engineer 1 obtains credentials at runtime and prepares fresh confirmed API/iOS/Android account pairs, ensuring both wallets and holder entries through PUT before each journey. Engineer 2 supplies the named Flutter integration test and dev configuration. Extend scripts/verify-dev.sh, which currently calls only the API smoke script, to run the scoped API and both named simulator/emulator journeys with their independent fixtures. Missing Flutter, Docker, device or configuration fails visibly; do not record partial API-only execution as full skeleton verification.
11. [ ] **Implement the delivery and migration gates test-after.** Update existing CI/deploy workflows for exact pins, lint/type/security checks, preserved repo/core coverage floors, new table/resource assertions and real local-store tests. Keep other-engineer PR review, short-lived OIDC and platform-first deployment/config wiring. Record migration readiness and prevent an incompatible rollback; each repo retains its independent pipeline.
12. [ ] **Prove public timing and deployed behavior.** In controlled dev fixtures inject adapter initialization and pre-handler origin delays above two seconds and prove CloudFront records include them. Test two eligible slow/recovery windows, telemetry loss and acceptance blocking on missing/conflicting records. Remove injections, then run the approved 100-user/10-active-user load shape with at least 200 funded attempts, complete per-response reconciliation and separate combined/sustained p95. Run scripts/verify-dev.sh at the authorized verification step and capture the three repo commits, actual devices and real results. Do not resubmit an uncertain financial attempt to improve evidence.
13. [x] **Finish current evidence, docs and traceability.** Update code-summary.md, source-manifest.json and AC/NFR/business-rule mappings from actual changed files/tests. Retain earlier claimed paths and distinguish current results from earlier attempts. Record blocked checks honestly. Supply the co-engineer the exact contract revision, non-secret configuration and expected commands through the handoff. Keep user-authored root files unless an approved plan explicitly names a required edit.

## Story-to-Step Traceability

| Plan step | Stories and acceptance coverage |
|---|---|
| 1–2 | US6.1, US6.4 — preserve baseline, runner readiness, contract pins and split work ownership. |
| 3–5 | US2.1, US3.1, US3.4, US4.1, US4.2 — canonical atomic transfer, unchanged balances during migration and correct shared history identity. |
| 6–7 | US1.2, US1.3, US2.1, US3.1, US4.1, US6.1 — setup repair, verified identity, exact C1 adaptation, platform path and safe failures. |
| 8, 12 | US6.1; NFR6.1, NFR8.1–8.3, NFR10.1–10.2 — public timing, honest sample coverage, private telemetry, controlled fault proof and dev load acceptance. |
| 9 | US1.3, US2.1, US3.1, US3.2, US3.4, US4.1, US4.2 — co-engineer's mobile screens, review/display and uncertain-result handling. |
| 10–11 | US1.2, US6.1, US6.4 — independent prepared fixtures, all three verification journeys and deployment/review gates. |
| 13 | All assigned U1 stories and detailed NFRs — current source/test evidence and co-engineer handoff. |

## Test Files and Coverage Plan

Standard strategy applies with the team's custom ordering. Plan at least 5–8 cases for each logical component: platform identity/edge stacks, platform monitoring stack, Ledger rules, Ledger repository, WalletDirectory repository, MoneyApi handlers, and the four Flutter screen components. Add integration coverage at the DynamoDB transaction, C1 API, platform-to-MoneyApi forwarding, and Flutter-to-dev boundaries. Keep 80% line coverage in each backend/mobile repo and 95% line and branch coverage for the Ledger money core. Add the property test for conservation/non-negative balances and the real local-container transaction/concurrency checks. Do not lower a floor to make a run pass.

Expected test files:

- `Raad/infrastructure/tests/test_identity_stack.py`, `test_public_edge_stack.py`, `test_monitoring_stack.py`.
- `RaadMoneyService/tests/unit/test_ledger_rules.py`, `test_ledger_repository.py`, `test_wallet_directory.py`, `test_money_api.py`; `tests/integration/test_dynamodb_transactions.py`, `test_c1_api.py`, `test_edge_forwarding.py`.
- `RaadMobile/test/sign_in_test.dart`, `wallet_screen_test.dart`, `transfer_flow_test.dart`, `history_screen_test.dart`; `integration_test/walking_skeleton_test.dart`.
- `RaadMoneyService/pyproject.toml`, `Raad/infrastructure/pyproject.toml`, and `RaadMobile/pubspec.yaml` carry the minimal runner/dependency configuration; Python coverage config retains both repo and Ledger-specific floors.
- Extend existing `RaadMoneyService/tests/unit/test_service_stack.py`, `test_identity.py`, `test_c1_contract.py` and `tests/integration/test_wallet_directory.py`. Add `tests/unit/test_transactions_migration.py` and `tests/integration/test_transactions_migration.py`.
- Add `Raad/infrastructure/tests/test_public_latency_processor.py` and `test_public_latency_stack.py` for safe-field selection, initialization-inclusive timing, deduplication, window eligibility, missing/late samples and no money permissions.
- Add a service coverage checker that independently enforces 95% line and 95% branch coverage for raad_money.ledger from the scoped JSON report; a combined coverage percentage alone is insufficient. Engineer 2 supplies the explicit 80% mobile line-coverage check.

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
- The approved monitoring design intentionally uses best-effort CloudFront logs. Even at 100% sampling, missing records block acceptance rather than being dropped. Telemetry runtime/shard/query costs and deployed capability evidence must be recorded before claiming monitoring works.
- U2's saved replay outcomes, sender/recipient history indexes and paging are later-unit work. Preserve transfer IDs and data during that extension; use the current approved Functional Design and Infrastructure Design as the implementation baseline.

