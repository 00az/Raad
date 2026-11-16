AIDLC-UNIT: u1-walking-skeleton
AIDLC-TESTING-CONTRACT: sha256:7d7f077a74e1c8ed59b1ec6ddd9f041d8db0c6a93d62e46cc8c573d062f59d5e

## Files and commands

Write and edit files yourself with your file tools, never through the shell (no heredoc, no `echo`, `printf`, or `python3` writing a file, no `sed -i`, no `mkdir`; the file-write tool creates any missing folder). A command the person asks for, or one the plan names (a package install, a build, a scaffolder, a migration, a formatter, a code generator, even a `mkdir`), still runs as written. Do not stash, reset, check out over, restore or clean the person's working tree, and do not install what the plan does not name: for a before-and-after comparison, run the check on the unchanged tree before you edit. Every file you make on your own, a scratch file, a helper script, a command's output, stays inside the project (nothing in /tmp or any folder outside it), and a command's output is read from the tool result, never sent to a file; a file the person asks for, or one the plan names, goes where they say. Quote a pattern meant for the program, not the shell (`--include='*.ts'`), and never start an argument with `=`: zsh, the macOS default shell, stops on both. Read, list, and search (your own knowledge files included) with your file tools where you have them; where the shell is your only way to read, use one plain read command (no `cd` before it, no pipe or second command after it). Run every AI-DLC command exactly as written, as a command of its own (no `cd` before it, no pipe or second command after it), keeping its path as written (never a full path): a shell line can stop and ask the person to approve it.

## The plan file

Tick each step's box in `aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u1-walking-skeleton/code-generation/code-generation-plan.md` as you finish the step. That is the only change you make to that file.

## Approved plan

# Code Generation Plan — U1 Walking Skeleton

Conversation language: English.

## Summary

- Builds: local U1 code repairs for secure external-DNS/custom-certificate configuration, matching Lambda packaging and infrastructure security findings; preserves the existing atomic wallet slice.
- Touches: platform/service CDK, configuration, CI and tests in `Raad` and `RaadMoneyService`; mobile source remains Engineer 2-owned.
- Tests: local platform/service suites, real DynamoDB Local integration, independent Ledger coverage, lint/types/audit, real Docker packaging and cdk-nag. AWS deployment and live verification are explicitly deferred.

## Scope and Boundaries

Implement US1.2's authenticated wallet safety net, US1.3's sign-in check, US2.1's balance screen, US3.1/US3.2/US3.4's recipient review and one transfer, US4.1/US4.2's first history page, and US6.1/US6.4's opening-balance and dev walking-skeleton checks. Keep whole-halalas accounting, atomic wallet creation and transfer, verified caller identity, C1 wire shapes, and the approved privacy boundaries.

The unit definition identifies `Raad` as the shared platform repo, `RaadMoneyService` as the money service repo, and `RaadMobile` as the Flutter repo. Their local folders are this workspace, `../money-service`, and `../mobile`. Platform and service source, test/configuration files and lockfiles already exist; the mobile folder currently contains its handoff README. Confirm registered repo identities and current branch/worktree status before source edits. Work in those checkouts and preserve existing edits and history.

The open steps below are the revised work and re-verification required against the approved designs. Earlier source changes and test evidence remain recorded in the existing source manifest and code summary; they do not establish that the new transaction schema or telemetry is implemented. Capture the unchanged-tree test baseline after plan approval and before editing application code. Update the source manifest with every created/modified/deleted path, retaining paths from earlier attempts.

## Current Repair Scope and Explicit Live Deferral

The person clarified that only AWS deployment and live checks should be skipped; Code Generation continues (message fcf6b4bc). Repair the local implementation and do not mark failed local security/build checks deferred merely because cloud execution is deferred. Earlier implementation and evidence are retained, with fresh checks for changed code.

- **In scope:** local source/configuration/CI repairs, unit and real local-database tests, packaging and synthesized-template security verification. Preserve coverage floors, independent identity verification, origin credentials and integer money invariants.
- **Deferred by the person:** AWS resource creation/deployment, asset publication, real DNS reservation/certificate issuance, provider capability execution, deployed migration/activation, real dev API/device journeys, alarm delivery, live load and public timing probes. Keep these as release gates and trace rows marked Deferred with the person's reason, not OK.
- **No spending authorization:** no paid domain, Route53 hosted zone, paid Cognito tier, new subscription, store enrollment, pipeline push/merge or remote workflow execution. Local configuration may name synthetic fixture inputs for tests/synth, explicitly labelled as such.
- **Secure public configuration:** implement the latest controlled-free-subdomain design: domain plus custom ACM certificate required for a deployable TLS>=1.2 configuration; existing hosted-zone ID optional for explicitly selected existing-zone integration. Support external DNS with no Route53 resources. The default cloudfront.net certificate remains unsuitable for the required TLS minimum and must not become a deployable compliant mode.
- **Portable packages:** use an explicit matching Lambda architecture and Docker platform in both backend repos. Prefer X86_64 with linux/amd64 to match the current x86 GitHub runners without assuming ARM emulation; the Mac must bundle for that declared target. Check native ELF architecture and add regressions. A failing package build remains a local failure.
- **Security repairs:** resolve actual cdk-nag findings COG8, SMG4, SNS3, L1, IAM4/IAM5, CFR3/CFR4, APIG1/APIG4 by correcting applicable configuration and least-privilege permissions. A narrowly scoped documented exception is allowed only by the affirmed team policy when an AWS API limitation or an explicit design control makes a check inapplicable; place its technical reason beside the resource and verify the compensating control. Do not globally disable checks, lower targets, suppress the TLS requirement or enable billed features. If a finding needs a new business/security decision, leave it visibly blocking.
- **Provider capabilities:** implement/retain the local capability harness and safe failures, but P7 code invalidation and actual P1–P13 results are deferred live evidence. Never invent a pre-confirmation trigger.
- **Scope boundary:** do not implement later U2 replay/paging, U4 C2 resources or U5 content inside this U1 repair. All frontend ar/en requirements remain recorded for their owning units.

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
- Require a custom certificate and controlled hostname for deployable public API configuration, with explicit TLS>=1.2 policy. Support domain/certificate without a hosted-zone ID for external free DNS; reject incomplete configuration. Do not create a hosted zone or register a domain. Publish the actual configured public URL through SSM/output, with no client-secret exposure. Retain WAF, origin protection, disabled caching and telemetry. Use jjii0@hotmail.com as supplied deployment configuration; no subscription or delivery test runs in this local repair.
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

1. [ ] **Inspect existing work and establish the baseline.** Confirm repo identities, branches and work ownership. Preserve existing edits; inspect the current source manifest and earlier evidence. After approval, run the existing applicable suites before source changes and record failures/tool gaps. Verify registered sibling paths; request any required write access rather than copying code to another checkout.
2. [ ] **Make runners and pins ready.** Reuse the existing Python projects, pytest/Hypothesis/CDK configuration and lockfiles; bootstrap only missing configuration. Engineer 2 bootstraps Flutter and its test runner. Use the exact file-scoped commands in unit-test-instructions.md before each test-first cycle. Pin the current partial C1 release and C4 environment schema through their owning repos; preserve the rendered Testing Contract below.
3. [ ] **Reconcile the money core with TDD.** Write failing tests for positive integer money, exact-balance/insufficient-funds behavior, one opening credit, atomic transfer identity and conservation/non-negative balances. Make the smallest passing domain changes and refactor green. Include the one immutable transfer record in the money boundary. Persist no U1 request-key outcome.
4. [ ] **Implement the canonical table and adapters test-after.** Define three tables and the transferId primary key. Implement the five-action cross-table transaction with guarded wallet updates and conditional insert, reference-only lookup entries, unique wallet owners and directory emails. Strongly query the bounded caller page, batch-read canonical rows, restore ordering and reject missing/unprocessed/unauthorized rows safely. Add and run repository tests and real DynamoDB Local transaction/concurrency checks, including repeated distinct transfers between the same wallets and fault injection with no partial balances/rows/references.
5. [ ] **Verify migration code locally.** Reuse the additive dry-run/migration/readiness implementation and local conflict/rerun/count/balance tests. Deployed schema inspection, migration, activation and rollback execution are Deferred by the person's request; do not run them or invent a successful cutover.
6. [ ] **Align MoneyApi test-after.** Use explicit PUT /wallet setup and wallet-then-holder repair; GET returns WALLET_NOT_FOUND without creation. Preserve verified sub/profile source, exact C1 names/nesting, the Idempotency-Key header, safe errors, normalization, deterministic first-page history and bounded dependencies. Test directory failure after wallet commit, recovery without another credit, wrong-environment/spoofed identity, failed/uncertain outcomes and no backend transfer retry. Emit no saved U1 replay outcome or replay guarantee.
7. [ ] **Repair secure platform/service configuration test-after.** Implement the custom-domain/certificate pair with optional existing hosted zone and external-DNS mode. Refuse incomplete/unsupported deployable TLS configuration. Preserve native GetUser compatibility, independent bearer/SigV4/origin checks. Correct applicable cdk-nag findings with scoped IAM/logging/HTTPS/secret controls and documented policy-permitted exceptions only; no paid feature activation or blanket suppression. Test all configuration modes, headers, outputs and safe failures.
8. [ ] **Implement the approved public-latency pipeline test-after.** Configure the seven-field 100%-sampling CloudFront real-time log path, encrypted telemetry Kinesis stream, separate no-money-access processor, ingestion log group and scheduled event-window aggregation. Deduplicate native request IDs; compute unique counts/slow fractions; handle delayed/malformed/missing data, query limits and retries without false healthy results. Use native time-taken for public latency and handler timers only for diagnosis. Add 5–8 processor/stack cases each, privacy scans and duplicate-window tests.
9. [ ] **Reconcile Engineer 2's existing mobile track test-after.** Pin/generate the C1 client, then implement sign-in, explicit PUT setup, balance, send/review/result and first history with the recorded Arabic/English requirement; full frontend localization remains U3-owned. Parse SAR text using integer digits, display reference separately from transferId and show counterparty email. An uncertain U1 result blocks automatic/manual resubmit and reconciles with reads. Add stable widget keys, 5–8 cases per component and the mobile coverage checker. Work against a contract fake server until the real dev handoff; Engineer 1 does not edit mobile source.
10. [ ] **Verify fixture/host wrapper locally.** Run offline setup/runner/privacy/preflight tests and inspect the existing independent API/iOS/Android fixture handoff. Actual account creation, secret mutation, real dev fixture preparation and scripts/verify-dev.sh execution are Deferred. Missing real config remains a release blocker, not a local placeholder to deploy.
11. [ ] **Repair portable packaging and CI definitions test-after.** Align explicit Lambda X86_64 and linux/amd64 Docker bundling in platform/service, verify actual native assets and add CDK assertions. Update local/CI synth fixtures for secure external-DNS configuration; retain all coverage/lint/type/audit/security checks. Scope roles and permissions. Do not trigger workflows, push, merge, upload or deploy.
12. [ ] **Record the authorized live-work deferral.** Preserve the public timing/load/API/iOS/Android/alarm/migration/provider verification procedures for later. Record each as Deferred with message fcf6b4bc and unmet prerequisites; run none against AWS. This step records the deferral only and never establishes a working or release-ready walking skeleton.
13. [ ] **Finish current evidence, source accounting and traceability.** Retain earlier source claims, add every repair path and report exact local checks and unresolved findings. Distinguish OK local implementation, Deferred live execution and genuine unbuilt/failed GAP items. Prepare the co-engineer handoff without external messaging. U1 is not a verified deployed skeleton.

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
- The earlier default-hostname implementation is historical. This repair requires secure domain/certificate configuration with external DNS support and no hosted-zone purchase. Actual free hostname control, certificate issuance, protocol probes and environment outputs are Deferred live prerequisites. Local fixtures are never real ownership or deployment evidence.
- The exact Git workspace registration names for the sibling repo folders are confirmed before source edits. If they are not registered, use the supported repo-add command rather than creating a second checkout.
- The approved monitoring design intentionally uses best-effort CloudFront logs. Even at 100% sampling, missing records block acceptance rather than being dropped. Telemetry runtime/shard/query costs and deployed capability evidence must be recorded before claiming monitoring works.
- U2's saved replay outcomes, sender/recipient history indexes and paging are later-unit work. Preserve transfer IDs and data during that extension; use the current approved Functional Design and Infrastructure Design as the implementation baseline.

## Approved unit-test instructions

# Unit Test Instructions — U1 Walking Skeleton

Conversation language: English.

## Scope, Ordering and Ownership

These are planned commands, not execution evidence. No application tests run during plan revision. Verify each repository's runner/configuration before its first test. Preserve the Testing Contract: Ledger money-movement core tests are written first, then implementation, then refactoring while passing. For every other layer, implement first, then write and run tests before the work lands. Recheck existing implementation and historical results against the revised designs.

Engineer 1 owns platform and money-service source and tests. Engineer 2 owns all mobile source, generated client, configuration and tests in ../mobile. The mobile commands are Engineer 2's handoff; Engineer 1 does not edit mobile source. Each engineer reviews the other's pull request.

## Current Local Repair and Live Deferral

The person requested continued coding with **only AWS deployment and live verification deferred** (message fcf6b4bc). Execute the local commands below after plan approval. Do not execute scripts/verify-dev.sh, real-dev mobile journeys, live setup/provider calls, deployed migration or load/alarm probes in this repair. Their procedures are retained for later release acceptance and are not deleted or counted as passed.

Local synth uses explicitly synthetic account/role/domain/certificate inputs with no lookups, credential reads, asset publication or resource creation. These fixtures do not establish hostname ownership or issued certificates. A secure configuration with domain+custom certificate and no hosted-zone ID must synthesize; incomplete deployable TLS settings must fail validation. Do not suppress CFR4/TLS findings.

Use X86_64 Lambda and linux/amd64 Docker bundling consistently in both backend repos, matching existing x86 CI runners. Inspect a built native ELF asset and assert both Lambda Architecture and bundling platform; local ARM-native success does not prove this target.

## Prerequisites

Run each command separately from the stated working directory. In infrastructure/ and ../money-service/, install pinned Python 3.12 dependencies with `uv sync --locked --all-groups`; retain uv.lock. Have Node.js/CDK and Docker available. From ../money-service/, run `docker compose up -d dynamodb-local` and verify readiness before integration tests; stop the disposable service afterward with `docker compose stop dynamodb-local`.

Engineer 2 installs the pinned Flutter SDK, Xcode/CocoaPods and Android SDK, then runs `flutter pub get` in ../mobile. Set actual nonsecret RAAD_IOS_DEVICE_ID and RAAD_ANDROID_DEVICE_ID values before device verification. Generated C4 config/dev.json contains nonsecret dev configuration and must match the runtime pool/client/API outputs. The host runner resolves its path and creates private temporary per-device fixture files automatically from the approved runtime secret; never put credentials in command arguments or committed files.

## Commands

Run only after implementation approval and after the named files exist. Each row is a separate invocation; record every result even if an earlier coverage exit is nonzero.

| Repository | Command | Purpose |
|---|---|---|
| ../money-service/ | `uv run pytest tests/unit/test_ledger_rules.py` | First runner-ready command and TDD red/green/refactor cycle. |
| infrastructure/ | `uv run pytest --cov=raad_platform --cov=../scripts --cov-report=term-missing` | Full platform, edge, telemetry and host mobile-runner suite with scripts included in the configured whole-package 80% coverage floor. |
| ../money-service/ | `uv run pytest tests/unit/test_service_stack.py tests/unit/test_c1_contract.py tests/unit/test_ledger_rules.py tests/unit/test_ledger_repository.py tests/unit/test_money_api.py tests/unit/test_identity.py tests/unit/test_wallet_directory.py tests/unit/test_transactions_migration.py` | Explicit U1 units and properties. |
| ../money-service/ | `uv run pytest tests/integration/test_c1_api.py tests/integration/test_dynamodb_transactions.py tests/integration/test_edge_forwarding.py tests/integration/test_wallet_directory.py tests/integration/test_transactions_migration.py` | Real local DynamoDB atomicity, concurrency, migration and API boundaries. |
| ../money-service/ | `uv run pytest tests/unit/test_ledger_rules.py --cov-reset --cov=raad_money.ledger --cov-branch --cov-report=json:artifacts/coverage/u1-ledger.json --cov-report=term-missing` | Ledger-only evidence using the actual importable module. |
| ../money-service/ | `uv run python scripts/check_ledger_coverage.py artifacts/coverage/u1-ledger.json` | Planned checker enforces 95% line AND 95% branch independently; rejects missing/malformed/unmeasurable evidence. |
| ../mobile/ — Engineer 2 | `flutter test --coverage test/sign_in_test.dart test/wallet_screen_test.dart test/transfer_flow_test.dart test/history_screen_test.dart` | Explicit U1 unit/widget files. |
| ../mobile/ — Engineer 2 | `flutter test --coverage` | Full mobile unit/widget/contract suite before its coverage check. |
| ../mobile/ — Engineer 2 | `dart run tool/check_coverage.dart` | Engineer 2's implemented 80% mobile line-coverage checker; rejects missing evidence. |
| ../mobile/ — Engineer 2 | `flutter test integration_test/walking_skeleton_test.dart -d "$RAAD_IOS_DEVICE_ID" --dart-define-from-file=config/dev.json` | **Deferred: do not run** — real-dev iOS journey. |
| ../mobile/ — Engineer 2 | `flutter test integration_test/walking_skeleton_test.dart -d "$RAAD_ANDROID_DEVICE_ID" --dart-define-from-file=config/dev.json` | **Deferred: do not run** — real-dev Android journey. |
| Raad workspace root | `scripts/verify-dev.sh` | **Deferred: do not run** — integrated real-dev API/device verification. |

The current verify-dev.sh preflights device/config prerequisites, captures setup's nonsecret result, runs the API smoke and invokes scripts/run_mobile_dev.py. That runner requires a matching runId from Secrets Manager, validates distinct fresh per-phase pairs and C4/runtime agreement, writes 0600 temporary fixture files under a 0700 directory, selects RAAD_E2E_TARGET=dev explicitly and runs iOS then Android. Its deployed run remains unverified. Missing runtime, devices or configuration cannot yield an API-only integrated U1 pass. Individual API results may be reported as partial evidence. The mobile skeleton now exists at commit 8ce7db6; device integration still requires execution. Flutter subprocess output is suppressed for privacy; safe failure status is reported and temporary files are cleaned on exceptions. Forced host termination may require private-file/build-artifact cleanup.

## Required Coverage and Evidence

- Keep at least 80% line coverage independently in Raad, RaadMoneyService and RaadMobile, and at least 95% line and 95% branch coverage independently in raad_money.ledger. A combined percentage of 95% does not establish both Ledger floors. Preserve existing thresholds and measured production files.
- Scoped assertions can pass while configured whole-package coverage causes a nonzero exit. Record both facts; the coverage exit remains a failure. Build and Test verifies each repository's assembled full suite and coverage. Never lower a floor to obtain a pass. Run separate checker commands even if an earlier command failed.
- Use 5–8 cases per component, at least 60 unit/widget cases across U1, and integration checks at key boundaries. Real local-store transaction/concurrency tests cannot be replaced with mocks.
- Record working directory, exact command, runtime/tool versions, source revision, fixture IDs, assertions, coverage and missing prerequisites. Label historical evidence. Never claim local, device, deployed or performance results before execution.

## Required Cases

- Money core: whole-halalas validation, conservation/nonnegative balances over generated sequences, insufficient funds, self-transfer and invalid recipients. U1 validates Idempotency-Key but has no saved replay outcome; U2 owns persistent replay. Reconcile uncertain U1 submissions by reads; never resubmit automatically or manually.
- Atomic storage: three local tables; one five-action transaction for conditional sender debit, recipient credit, canonical transfer insertion and two reference-only history insertions. Verify rollback for each failed condition, simultaneous debits without overdraft, repeated wallet pairs with distinct transfer IDs, and one immutable canonical payload per completed transfer.
- History: strongly consistent descending lookup reads with limit+1; canonical BatchGet batches no larger than 100; order restoration; ownership checks; bounded UnprocessedKeys backoff; missing/inconsistent records cause a safe page error rather than omissions.
- Migration: absent legacy data, matching/conflicting/unmatched pairs, interruption/rerun, conditional canonical insert and reference conversion, unchanged balances, quiesced cutover and validation of counts plus both history views. Never discard unresolved records, reset balances or fabricate replay outcomes. Rollback after cutover must understand the canonical layout.
- API/identity: independent C1 fixtures and exact headers/shapes/statuses; preserved bearer token through the outer SigV4 envelope; independent MoneyApi verification; unauthorized direct invocation; caller ownership; PUT wallet/directory repair after partial setup.
- Platform/telemetry: three-table least privilege; seven-field CloudFront allowlist, exact transfer behavior, caching disabled and 100% sampling; encrypted us-east-1 stream and separate telemetry role with no money access; native-ID deduplication; event-time windows, minimum counts, slow fraction, nearest-rank p95, repeated gauge publication and eligible recovery. Malformed/conflicting records, late/missing logs, bounded-query failure and insufficient windows cannot manufacture healthy results or leak personal data.
- Mobile — Engineer 2: sign-in, balances, recipient review, transfer outcome, history and uncertain-submission reconciliation. Verify each device independently, building against the agreed contract while backend work proceeds.

## Fixtures and Deployed Acceptance — Live Procedures Deferred

Local integration uses isolated UUID-named Ledger and WalletDirectory tables with pk/sk keys, plus a Transactions table keyed by transferId. DYNAMODB_ENDPOINT defaults to http://127.0.0.1:8000 with local test credentials. Guard against using an AWS endpoint as the disposable local store. Direct seeding/deletion is limited to these isolated local tables.

In deployed dev, create approved identities through Cognito and establish wallets through PUT. Use separate fresh sender/recipient pairs for API, iOS, Android and load phases with known opening balances. Never directly seed deployed tables, reset real users or reuse a depleted pair to manufacture a pass. Failed/unknown attempts remain in the evidence; never resend them to clean the result.

Public latency uses CloudFront real-time time-taken in milliseconds and completion timestamps; handler duration is diagnostic. Record safe run/phase/UTC/outcome/client elapsed data and each response's native x-amz-cf-id. Reconcile every response one-to-one with deduplicated logs. No response is a technical failure; missing/conflicting/unclassifiable records make acceptance incomplete. Wait at most two minutes after the run, then fail or mark incomplete without resubmission.

Use at least 200 funded attempts, 100 registered users and 10 active users across the approved ten-minute sustained shape, retaining idle-start samples. Every valid funded attempt must succeed. Nearest-rank p95 for both combined idle/sustained and sustained-only samples must be at most 2000 ms. Keep client/network timing separate. At the real public URL prove a fresh adapter version's initialization delay above two seconds and a pre-handler origin delay appear in CloudFront duration while omitted handler timing demonstrates its limitation. Exercise two eligible slow windows, recovery windows and missing delivery; remove injections before ordinary verification. Logs remain best effort even at 100% sampling; unknown delivery coverage cannot establish complete-population health.

Record stream/runtime/query cost estimates, deployed prerequisites, fault-proof evidence and ordinary verification separately. Approving these instructions does not assert a deployment or acceptance result.

## Local Repair Validation Commands

Each command is a separate invocation in its named directory. Run affected suites after changes and the full applicable local checks before review; retain unchanged source's earlier evidence with its date. Run local integration with the approved disposable Docker store only. Existing coverage floors remain mandatory.

| Directory | Command | Evidence |
|---|---|---|
| infrastructure | `uv run ruff check raad_platform tests app.py ../scripts` | Lint includes host runner. |
| infrastructure | `uv run ruff format --check raad_platform tests app.py ../scripts` | Formatting. |
| infrastructure | `uv run mypy raad_platform app.py ../scripts` | Strict types. |
| infrastructure | `uv run pip-audit` | Dependency audit. |
| ../money-service | `uv run ruff check src tests scripts` | Service lint. |
| ../money-service | `uv run ruff format --check src tests scripts` | Service formatting. |
| ../money-service | `uv run mypy src` | Strict service types. |
| ../money-service | `uv run pip-audit` | Dependency audit. |
| infrastructure | `env -u RAAD_HOSTED_ZONE_ID CDK_DEFAULT_ACCOUNT=111111111111 CDK_DEFAULT_REGION=us-east-1 RAAD_DOMAIN_NAME=api.dev.raad.example.test RAAD_CERTIFICATE_ARN=arn:aws:acm:us-east-1:111111111111:certificate/00000000-0000-0000-0000-000000000000 RAAD_ALERT_EMAIL=build@example.test RAAD_COGNITO_DOMAIN_PREFIX=raad-build-example-test uv run cdk synth --all` | Explicit local external-DNS fixture only. Real Docker bundle and nag; no AWS lookup/upload/deploy. |
| ../money-service | `env CDK_DEFAULT_ACCOUNT=111111111111 CDK_DEFAULT_REGION=us-east-1 RAAD_EDGE_ROLE_ARN=arn:aws:iam::111111111111:role/raad-build-edge RAAD_CORRELATION_SECRET_ARN=arn:aws:secretsmanager:us-east-1:111111111111:secret:raad/dev/correlation-hmac-build uv run cdk synth --all` | Explicit service build fixtures only; actual native-package target and nag evidence. |

Add meaningful regressions in the existing platform/service stack tests for external DNS without Route53 resources, domain/certificate pair validation, explicit viewer TLS policy, correct public URL, origin protection/telemetry preservation, package architecture, narrowed IAM and any policy-permitted scoped security exceptions. Verify missing/incomplete deployment settings fail closed. Never turn an actual finding into an exception solely to obtain exit0; document the AWS limitation or explicit alternative control and test it.

Current reported nag categories requiring disposition are COG8, SMG4, SNS3, L1, IAM4/IAM5, CFR3/CFR4 and APIG1/APIG4. No paid feature activation, global suppression or weaker NFR is authorized. A decision-dependent unresolved finding stays a local GAP and is surfaced for the person.

Report code/local evidence separately from Deferred real DNS/ACM/provider/deployment/migration/dev API/device/alarms/load acceptance. Local repair completion does not establish a verified walking skeleton or release readiness.
