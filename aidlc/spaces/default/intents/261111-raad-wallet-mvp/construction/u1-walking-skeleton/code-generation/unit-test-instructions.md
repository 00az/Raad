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
