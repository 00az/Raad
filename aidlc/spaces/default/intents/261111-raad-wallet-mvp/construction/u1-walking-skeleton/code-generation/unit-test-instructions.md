# Unit Test Instructions — U1 Walking Skeleton

Conversation language: English.

## Scope, Ordering and Ownership

These are planned commands, not execution evidence. No application tests run during plan revision. Verify each repository's runner/configuration before its first test. Preserve the Testing Contract: Ledger money-movement core tests are written first, then implementation, then refactoring while passing. For every other layer, implement first, then write and run tests before the work lands. Recheck existing implementation and historical results against the revised designs.

Engineer 1 owns platform and money-service source and tests. Engineer 2 owns all mobile source, generated client, configuration and tests in ../mobile. The mobile commands are Engineer 2's handoff; Engineer 1 does not edit mobile source. Each engineer reviews the other's pull request.

## Prerequisites

Run each command separately from the stated working directory. In infrastructure/ and ../money-service/, install pinned Python 3.12 dependencies with `uv sync --locked --all-groups`; retain uv.lock. Have Node.js/CDK and Docker available. From ../money-service/, run `docker compose up -d dynamodb-local` and verify readiness before integration tests; stop the disposable service afterward with `docker compose stop dynamodb-local`.

Engineer 2 installs the pinned Flutter SDK, Xcode/CocoaPods and Android SDK, then runs `flutter pub get` in ../mobile. Set actual nonsecret RAAD_IOS_DEVICE_ID and RAAD_ANDROID_DEVICE_ID values before device verification. Generated C4 config/dev.json contains nonsecret dev configuration. Obtain credentials at runtime through the approved dev secret; never put them in command arguments or committed files.

## Commands

Run only after implementation approval and after the named files exist. Each row is a separate invocation; record every result even if an earlier coverage exit is nonzero.

| Repository | Command | Purpose |
|---|---|---|
| ../money-service/ | `uv run pytest tests/unit/test_ledger_rules.py` | First runner-ready command and TDD red/green/refactor cycle. |
| infrastructure/ | `uv run pytest tests/test_identity_stack.py tests/test_public_edge_stack.py tests/test_monitoring_stack.py tests/test_edge_adapter.py tests/test_public_latency_processor.py tests/test_public_latency_stack.py` | U1 platform, edge and telemetry checks. |
| ../money-service/ | `uv run pytest tests/unit/test_service_stack.py tests/unit/test_c1_contract.py tests/unit/test_ledger_rules.py tests/unit/test_ledger_repository.py tests/unit/test_money_api.py tests/unit/test_identity.py tests/unit/test_wallet_directory.py tests/unit/test_transactions_migration.py` | Explicit U1 units and properties. |
| ../money-service/ | `uv run pytest tests/integration/test_c1_api.py tests/integration/test_dynamodb_transactions.py tests/integration/test_edge_forwarding.py tests/integration/test_wallet_directory.py tests/integration/test_transactions_migration.py` | Real local DynamoDB atomicity, concurrency, migration and API boundaries. |
| ../money-service/ | `uv run pytest tests/unit/test_ledger_rules.py --cov-reset --cov=raad_money.ledger --cov-branch --cov-report=json:artifacts/coverage/u1-ledger.json --cov-report=term-missing` | Ledger-only evidence using the actual importable module. |
| ../money-service/ | `uv run python scripts/check_ledger_coverage.py artifacts/coverage/u1-ledger.json` | Planned checker enforces 95% line AND 95% branch independently; rejects missing/malformed/unmeasurable evidence. |
| ../mobile/ — Engineer 2 | `flutter test --coverage test/sign_in_test.dart test/wallet_screen_test.dart test/transfer_flow_test.dart test/history_screen_test.dart` | Explicit U1 unit/widget files. |
| ../mobile/ — Engineer 2 | `dart run test/check_u1_coverage.dart coverage/lcov.info` | Planned explicit 80% mobile line-coverage check; reject missing evidence. |
| ../mobile/ — Engineer 2 | `flutter test integration_test/walking_skeleton_test.dart -d "$RAAD_IOS_DEVICE_ID" --dart-define-from-file=config/dev.json` | iOS simulator journey. |
| ../mobile/ — Engineer 2 | `flutter test integration_test/walking_skeleton_test.dart -d "$RAAD_ANDROID_DEVICE_ID" --dart-define-from-file=config/dev.json` | Android emulator journey with separate fixtures. |
| Raad workspace root | `scripts/verify-dev.sh` | Agreed integrated verification entry point: API and both device journeys. |

The existing verify-dev.sh currently invokes only the API verifier. Implementation must extend it to the agreed iOS and Android checks and propagate their failures. Missing mobile implementation, runtime, devices or configuration cannot yield an API-only integrated U1 pass. Individual API results may be reported as partial evidence.

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

## Fixtures and Deployed Acceptance

Local integration uses isolated UUID-named Ledger and WalletDirectory tables with pk/sk keys, plus a Transactions table keyed by transferId. DYNAMODB_ENDPOINT defaults to http://127.0.0.1:8000 with local test credentials. Guard against using an AWS endpoint as the disposable local store. Direct seeding/deletion is limited to these isolated local tables.

In deployed dev, create approved identities through Cognito and establish wallets through PUT. Use separate fresh sender/recipient pairs for API, iOS, Android and load phases with known opening balances. Never directly seed deployed tables, reset real users or reuse a depleted pair to manufacture a pass. Failed/unknown attempts remain in the evidence; never resend them to clean the result.

Public latency uses CloudFront real-time time-taken in milliseconds and completion timestamps; handler duration is diagnostic. Record safe run/phase/UTC/outcome/client elapsed data and each response's native x-amz-cf-id. Reconcile every response one-to-one with deduplicated logs. No response is a technical failure; missing/conflicting/unclassifiable records make acceptance incomplete. Wait at most two minutes after the run, then fail or mark incomplete without resubmission.

Use at least 200 funded attempts, 100 registered users and 10 active users across the approved ten-minute sustained shape, retaining idle-start samples. Every valid funded attempt must succeed. Nearest-rank p95 for both combined idle/sustained and sustained-only samples must be at most 2000 ms. Keep client/network timing separate. At the real public URL prove a fresh adapter version's initialization delay above two seconds and a pre-handler origin delay appear in CloudFront duration while omitted handler timing demonstrates its limitation. Exercise two eligible slow windows, recovery windows and missing delivery; remove injections before ordinary verification. Logs remain best effort even at 100% sampling; unknown delivery coverage cannot establish complete-population health.

Record stream/runtime/query cost estimates, deployed prerequisites, fault-proof evidence and ordinary verification separately. Approving these instructions does not assert a deployment or acceptance result.
