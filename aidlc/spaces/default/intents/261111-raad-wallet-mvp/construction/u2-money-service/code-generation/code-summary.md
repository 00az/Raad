# U2 Money Service — Code Summary

Conversation language: English.

All application changes are in `RaadMoneyService` (registered checkout `RaadMoneyService@checkout`, branch `aidlc/u1-money-service`, base `bf7b19b`), left uncommitted in the working tree for review. The C2 event contract lives in `Raad` and is owned by U4; this unit only pins a copy of it (see "Revision after review 1"). Nothing was deployed, no AWS API was called, and the only data store touched was DynamoDB Local in Docker. All money is whole halalas; no float or decimal arithmetic was introduced.

## Result at a glance

| Measure | Result |
|---|---|
| Tests | 436 passed after the review 1 revision: 329 unit, 107 integration against DynamoDB Local (427 at the end of the stage; U1 baseline 133 unit) |
| Repository coverage, `pytest tests/unit tests/integration` | 95.53% combined line and branch after the review 1 revision; 96.67% line only (1,441 statements, 48 missed). Floor 80%. U1 baseline 89.35%. Run-to-run spread comes from race-only branches in `storage.py` (see "Revision after review 1") |
| Money core, `raad_money/ledger.py` | 100.00% line, 100.00% branch (floor 95% each) |
| Money core, `raad_money/transfers.py` | 100.00% line, 100.00% branch (floor 95% each) |
| Ruff format, Ruff lint, strict mypy | clean |
| pip-audit | no known vulnerabilities |
| OpenAPI | `openapi/raad-money-v1.yaml: OK` |
| cdk-nag, real `app.py` for `dev` and `prd` | 0 errors, 0 warnings; every suppression carries its reason in code |
| Docker asset bundling in `cdk synth` | **passed after the stage** (row 30): the 403 was a stale `public.ecr.aws` login in Docker's credential store; after `docker logout public.ecr.aws` the full bundling synth with cdk-nag passed for `dev`, `stg` and `prd` |

## Approved design reconciliation (verified)

- **Request keys: no durable reservation.** `functional-design/functional-spec.md` (Workflow step 3: "There is no separately durable reserved/pending row"; State Transitions: `absent -> completed(result) | refused(...)`, `absent -> absent (pre-commit failure; no durable reservation)`), `rules.md` BR2.8 ("never leaving a durable pending reservation") and `nfr-design/reliability-design.md` ("No separately durable reserved/pending key") agree. The plan's step 5 sentence about a `reserved` state is historical; there is no remaining conflict. The code creates the `(sender, key)` outcome only with its final result, conditionally, and atomically with the money movement on success.
- **Three tables, not two.** `logical-components.md`, `infrastructure-specification.md` and `reliability-design.md` name Ledger, canonical Transactions and WalletDirectory. The plan's step 14 "two tables" is historical; the stack keeps all three with their existing logical IDs.
- Replays return the saved business fields and status with the current request's fresh correlation ID; no correlation ID is stored in an outcome.

## What was built

| Area | Files | What it does |
|---|---|---|
| Money core (TDD) | `src/raad_money/ledger.py`, `src/raad_money/email_address.py` | `TransferRequest` (C1 normalization, int64 whole-halala amounts), `business_refusal` in C1 order (unknown recipient, 100–50,000 range, self, funds), `new_reference` (`R-` and 12 characters from `23456789ABCDEFGHJKMNPQRSTUVWXYZ`), one-way fingerprint, immutable `TransferOutcome` with no personal fields, `match_existing_outcome`, `plan_completion` (completion key strictly after both wallets' last keys; waits briefly or fails, never invents a time) |
| Duplicate-request handling (TDD) | `src/raad_money/transfers.py`, `src/raad_money/store_errors.py` | `TransferService.submit`: wallet check (no key consumed), strong outcome reread, replay or `IDEMPOTENCY_KEY_REUSED`, refusal persisted conditionally (low balance guarded by the observed wallet state), profile version ensured before commit, one atomic commit, bounded retries on conflicts, lost-response recovery by strong reread only |
| Ledger persistence | `src/raad_money/storage.py` | Seven-item commit: both wallets (balance, `transfer_sequence`, `last_completed_sort_key`, conditioned on balance and sequence), canonical Transactions row with `completedSortKey` and both role ordinals, the two U1 reference rows, the outcome, the unique reference marker. Cancellation reasons map to replay, re-evaluate, new reference or safe 503; timeouts are uncertain. Event receipts. New wallets start at sequence 0 |
| History (TDD) | `src/raad_money/history.py`, `src/raad_money/cursor.py` | Two KEYS_ONLY role indexes queried at or below the snapshot, merged newest first, canonical rows read strongly, ordinals verified N, N−1, …; one bounded reread, then a safe 503. HMAC cursor bound to caller, environment, limit, sort, snapshot, next ordinal and 24-hour expiry; key rotation overlap; no caller, wallet or profile data in clear |
| WalletDirectory (TDD) | `src/raad_money/storage.py` | Display spelling kept beside the normalized key, immutable profile versions (created at registration; one is attached to a U1 holder exactly once), `HolderExists` and `EmailConflict` instead of raw SDK errors, dangling email pointer never reveals another profile |
| C1 API (test-after) | `src/raad_money/api.py`, `src/raad_money/wallet_setup.py` | Full C1 v1: replay with `Idempotency-Replayed`, key reuse 409, each refusal with its status, recipient rebuilt only from the saved profile version (missing version is a 503, never recomputed), stable cursor paging, strict queries, an 8 KiB body bound. Only request parsing maps to 400; corrupt stored data is 503 |
| C2 consumer (test-after) | `src/raad_money/consumer.py` | Source, type and environment checked first; payload per C2 (any `1.x`, unknown fields ignored); same setup procedure as `PUT /wallet`; receipt recorded after setup; invalid, foreign and conflicting events quarantined at once; transient failures retried until `occurredAt` + 24 h, then copied to the processing DLQ and acknowledged; logs carry event ID and result only |
| Infrastructure (test-after) | `src/raad_money/infrastructure.py`, `app.py` | One stack per environment (`dev`, `stg`, `prd` only); stg/prd tables retained, deletion-protected and PITR-enabled; two GSIs; least-privilege roles (no Scan, Delete or wildcard actions; Query only on the two indexes); IAM-only Function URL; reserved concurrency 20; service-owned cursor secret; EventBridge rule with SQS target (24 h, 185 retries, delivery DLQ); work queue (4 days, 90 s, redrive 1,000) and processing DLQ (14 days); consumer batch 1, two workers; nine alarms to the platform topic; dashboard |
| Migration | `scripts/migrate_transactions.py` | `--seed-ordinals` (dry run unless `--apply --writes-quiesced`) seeds U1 wallets and canonical rows in C1 order without touching balances, IDs or times; refuses any disagreement; `--check-ready` now also requires the U2 layout (`schemaVersion` 3) |
| Gates and smoke | `scripts/check_ledger_coverage.py`, `scripts/verify_dev.py`, `.github/workflows/ci.yml`, `.github/workflows/deploy-dev.yml` | Per-module 95% line and branch gate over both core modules; smoke adds same-key replay, range refusal and the `nextCursor` field; CI fixture values and SSM reads for the two new platform inputs |
| Contract | `openapi/raad-money-v1.yaml` | See C1 contract changes |

Tests added: `tests/unit/test_u2_money_core.py`, `test_u2_transfer_service.py`, `test_u2_history.py`, `test_consumer.py`, `test_smoke_script.py`; `tests/integration/test_u2_transfers.py`, `test_u2_history.py`, `test_u2_directory.py`, `test_u2_api.py`, `test_u2_consumer.py`. U1 tests updated where they pinned U1 internals this unit replaces: `test_money_api.py`, `test_edge_forwarding.py`, `test_ledger_repository.py`, `test_dynamodb_transactions.py`, `test_wallet_directory.py` (unit and integration), `test_service_stack.py`, `test_transactions_migration.py` (unit and integration), integration `conftest.py` (GSIs). `test_u2_money_rules.py` was only reformatted.

## TDD Red evidence (money core, replay, history, directory)

Each Red ran before any implementation of its behavior existed.

1. **Money core Red 1:** `uv run pytest tests/unit/test_ledger_rules.py tests/unit/test_u2_money_rules.py --cov-reset --cov=raad_money.ledger --cov-report=term-missing --cov-fail-under=95` → exit 2:
   `ERROR collecting tests/unit/test_u2_money_rules.py … ImportError: cannot import name 'TransferRequest' from 'raad_money.ledger'`. `test_u2_money_rules.py` was the started U2 Red from an earlier session with no recorded Red. Its assertions were checked against `rules.md` BR2.6 and the C1 refusal order before use.
2. **Money core Red 2** (adds `test_u2_money_core.py`): same command plus that file → exit 2: `ImportError: cannot import name 'TransferRequest'` and `ImportError: cannot import name 'MAX_TRANSFER_HALALAS' from 'raad_money.ledger'`.
3. **Replay Red:** `uv run pytest tests/unit/test_u2_transfer_service.py tests/integration/test_u2_transfers.py --no-cov -q` → exit 2: `ModuleNotFoundError: No module named 'raad_money.store_errors'` (both files).
4. **History Red:** `uv run pytest tests/unit/test_u2_history.py --no-cov -q` → exit 2: `ModuleNotFoundError: No module named 'raad_money.cursor'`; `uv run pytest tests/integration/test_u2_history.py --no-cov -q` → exit 2: `ModuleNotFoundError: No module named 'raad_money.history'`.
5. **Directory Red:** `uv run pytest tests/integration/test_u2_directory.py --no-cov -q` → exit 2: `ImportError: cannot import name 'HolderExists' from 'raad_money.storage'`.

Note on ordering: immutable profile versions are WalletDirectory behavior, but replay depends on them. They were therefore implemented in the replay Green and first exercised by the replay Red's DynamoDB Local tests. The directory Red then pinned them and drove the remaining new behavior (`HolderExists` and `EmailConflict` on registration).

## Commands run and results (chronological)

| # | Command (in `RaadMoneyService`) | Result |
|---|---|---|
| 1 | `uv run python --version` | created `.venv` from `uv.lock` (unchanged), Python 3.12.15 |
| 2 | Red 1 and Red 2 above | exit 2 as recorded |
| 3 | money-core run with `--cov-branch` | 65 passed; ledger 94%: defensive branches untested → tests added for refusal round-trip, corrupt stored outcomes, non-text email and missing sender → 71 passed, 100%/100% |
| 4 | `docker compose -f docker-compose.yml up -d --wait dynamodb-local` | container started and served on `:8000`; `--wait` exited 1 because the compose healthcheck (`curl -fsS …/shell/`) gets HTTP 400 from this image and never reports healthy (pre-existing) |
| 5 | Replay Red above | exit 2 as recorded |
| 6 | replay Green, unit + integration | first run 32 passed, 2 failed: a test passed the email as the amount; the contention test expected every request under 6-thread, 3-wallet contention to settle, but the design allows a safe bounded 503 → tests corrected to prove "no outcome persisted, same key settles on retry" → 34 passed |
| 7 | integration transfer file run 5 times | 12 passed each run |
| 8 | money core incl. `raad_money.transfers` | 97% → tests added for production defaults and "clock still ahead after waiting" → 95 passed, 100%/100% |
| 9 | History Red above, then Green | 39 passed (incl. 1,005-transfer paging, about 20 s); cursor 91%, history 93% → tests added for signed malformed payloads and corrupt ordinals → 46 unit passed |
| 10 | Directory Red above, then Green | 1 failure: a U1 unit fixture lacked `holder_id` on its fake profile → fixture fixed → 30 passed |
| 11 | U1 API tests on the new handler | 8 failed, each coupled to replaced U1 internals (`ledger.transfer`, list-shaped history, cursor rejected "until pagination unit") → rewritten against the new seams; the three in `test_edge_forwarding.py` now use real DynamoDB Local stores → 42 passed |
| 12 | `pytest tests/integration/test_u2_api.py` | 43 passed |
| 13 | consumer unit + integration | 37 passed; consumer 99% |
| 14 | repository unit, storage integration, migration (unit + integration) | 39, 10, 16, 17 passed |
| 15 | `pytest tests/unit/test_service_stack.py` | 26 passed after renaming an attribute that shadowed CDK's read-only `Stack.environment` |
| 16 | nag sanity check: stack plus one deliberately unsafe `sqs.Queue` | `has_no_error` failed with `AwsSolutions-SQS3`, `AwsSolutions-SQS4`, proving the nag test is effective |
| 17 | `uv run ruff format src tests scripts app.py` | 25 files reformatted |
| 18 | `uv run ruff check src tests scripts` | 14 findings → `ruff check --fix` (5 safe fixes) and hand fixes (TypeError for type checks, unused variables now asserted, redundant counter) → All checks passed |
| 19 | `uv run mypy src` | 37 errors in 2 files (untyped `int()` on an ordinal, over-narrow kwargs dict) → fixed → Success: no issues found in 13 source files |
| 20 | `uv run pytest tests/unit tests/integration` | **427 passed**, 95.79% total |
| 21 | money-core gate (exact CI command, see `unit-test-instructions.md`) | 95 passed, 100%; JSON at `artifacts/coverage/money-core.json` |
| 22 | `uv run python scripts/check_ledger_coverage.py artifacts/coverage/money-core.json` | `ledger.py line=100.00% branch=100.00%`, `transfers.py line=100.00% branch=100.00%` |
| 23 | `uv run pip-audit` | No known vulnerabilities found (local package skipped, not on PyPI) |
| 24 | `uv run openapi-spec-validator openapi/raad-money-v1.yaml` | OK |
| 25 | `uv run cdk synth --no-notices --quiet` with CI fixture inputs | **failed before stack code:** `docker: … public.ecr.aws/sam/build-python3.12:latest … 403 Forbidden`; image not cached locally |
| 26 | `cdk synth -c "aws:cdk:bundling-stacks=[]"` | refused by the CLI ("cannot use keys prefixed with 'aws:'") |
| 27 | `CDK_CONTEXT_JSON='{"aws:cdk:bundling-stacks":[]}' uv run python app.py` for `dev`, then `prd` | both synthesized; cloud assembly has 0 `aws:cdk:error` and 0 `aws:cdk:warning`; dev resources: 3 tables, 2 functions, 1 Function URL, 3 queues, 1 rule, 9 alarms, 1 dashboard, 1 secret |
| 28 | `command -v gitleaks` | not installed; credential-pattern grep over changed sources found only the existing DynamoDB Local dummy `"local"` |
| 29 | `docker compose -f docker-compose.yml stop dynamodb-local` | stopped |
| 30 | Conductor re-verification after the developer hand-back: `docker logout public.ecr.aws`, then `uv run cdk synth -q` with the CI fixture inputs for `RAAD_ENVIRONMENT=dev` and `stg` (the `prd` template from row 27 retained); full suite `uv run pytest tests/unit tests/integration` against DynamoDB Local; the money-core runner and `scripts/check_ledger_coverage.py` | bundling succeeded (three Lambda assets built in `public.ecr.aws/sam/build-python3.12`, linux/amd64); synth exit 0 with no cdk-nag error; 427 passed, 95.79% total; `ledger.py` and `transfers.py` 100% line and 100% branch; Ruff, mypy and pip-audit clean |

## Checks not run, and why

- **Real Docker asset bundling (`cdk synth`).** Resolved after the stage (row 30). During the build, public ECR refused the anonymous pull of `public.ecr.aws/sam/build-python3.12` with 403 because of a stale `public.ecr.aws` login in the local Docker credential store; after that login was removed, the full bundling synth passed. CI on `ubuntu-latest` also runs it.
- **gitleaks.** Not installed locally and not named in the plan; CI runs it.
- **Deployed checks.** Person-deferred (`fcf6b4bc`), with no AWS access in this stage: the `dev` smoke (`scripts/verify_dev.py`), stg/prd smokes, the public latency load evidence, alarm delivery to the confirmed subscription, and the timed three-table restore drill are all unrun.
- **CI itself.** The updated GitHub Actions workflows were not executed. The same commands were run locally.

No test was written and left unrun: all 427 ran and passed.

## Decisions and deviations

1. **The U1 writer `LedgerRepository.transfer()` was removed.** It wrote no outcome, sequences or ordinals, and `cicd-pipeline.md` forbids reactivating a legacy writer that lacks the U2 layout. Its tests now exercise the U2 commit.
2. **U1 reference rows are still written** inside the commit, as two of the seven items. They keep the strongly consistent U1 reference read for migration verification ("retain old reference reads until cutover verified") and keep `--check-ready` meaningful. They hold only `pk`, `sk` and `transferId`, never a payload copy.
3. **Fingerprint input** is length-prefixed and adds a domain tag and the sender's subject to the contract's major version, normalized recipient and amount. Comparisons are always within one sender, so semantics are unchanged; it only prevents cross-user precomputation.
4. **Error mapping narrowed.** Only request parsing returns 400; corrupt stored data or store failures return 503. U1 mapped every `ValueError` to 400.
5. **Directory refusals** raise `EmailConflict` and `HolderExists`, not a raw `ClientError`.
6. **`Recipient.email`** now returns the confirmed display spelling, as C1 states; U1-era holders, which kept only the normalized form, fall back to it.
7. **Reserved concurrency 20 in every environment**, per `infrastructure-specification.md`; U1 set it in `dev` only. This depends on the account's concurrency quota.
8. **Index staging.** CloudFormation adds one GSI per table update. A fresh environment gets both indexes at once. The existing `dev` Transactions table must take a one-time engineer deploy with `-c historyIndexes=1` before the normal deploy. This is deliberately not encoded in `deploy-dev.yml`, because a routine stage-1 deploy would delete the second index.
9. **U1 → U2 data step.** A U1 wallet without seeded ordinals fails closed (503) for transfers and history. `--check-ready` keeps the `dev` writer disabled until an engineer runs `migrate_transactions.py --seed-ordinals --apply --writes-quiesced` against the quiesced tables.
10. **EMF metrics.** Added an `Environment`-only dimension set and a `MoneyApiTechnicalFailures` count so the 5xx-rate alarm can use metric math. With fewer than 20 requests the alarm has no datapoint (INSUFFICIENT_DATA), never "healthy".
11. **Alarm recovery.** The design's "three consecutive complete healthy windows to recover" cannot be expressed in a native CloudWatch alarm; the alarms recover on their own evaluation. Public latency and heartbeat alarms are U4's.
12. **C2 retry deadline** uses the validated, offset-bearing payload `occurredAt` (at most 5 minutes in the future), not the EventBridge envelope time.
13. **Contention budget.** Four attempts with bounded jitter. Under extreme same-wallet contention a request can get a safe 503 with nothing persisted; a retry with the same key settles exactly once (tested).
14. **Cursor secret** is service-owned and rotated by a reviewed change that keeps `previousKey` for at least 24 hours (cdk-nag `AwsSolutions-SMG4` suppressed with that reason). `dev` tables suppress `AwsSolutions-DDB3` with the reason that they hold only simulated data; `stg` and `prd` enable PITR.

## C1 contract changes (`RaadMobile` must re-pin)

Rules followed: `contract-summary.md` "Contract Files, Releases and Pinning" and "Contract Ownership and Change Rules". No field was removed, renamed, narrowed or made required, and no enum changed, so this is not a breaking change in v1.

| Change | Kind |
|---|---|
| `info.version` `1.0.0-u1.2` → `1.0.0-u2.1`. It sorts above `1.0.0-u1.2` in semver, where `1.0.0-rc.1` would sort below. Promotion to `1.0.0` should follow the CI provider-test pass and is the person's decision | version |
| `info.description` rewritten: the U1 partial-release notes are replaced by the U2 behavior | wording |
| `x-u1-conformance` extension block removed. `RaadMobile` `test/contract_test.dart` asserts it on its pinned copy and must change at re-pin | extension |
| `TransferPage.hasMore` description now "true exactly when `nextCursor` is non-null"; the field is kept | wording |
| `TransferResult.reference` gains a description of the `R-` format; no `pattern` was added, so U1 `TXN-` references in history stay valid | wording |
| Behavior: `nextCursor` is non-null when more pages exist; `Idempotency-Replayed` is sent on persisted outcomes and key reuse; `X-U1-History-Truncated` is no longer sent (it was never a declared header; `RaadMobile`'s fake backend tests expect it); `AMOUNT_OUT_OF_RANGE` is enforced (U1 accepted 1–99 and above 50,000); saved outcomes replay | behavior within the documented v1 |

## Open points for the conductor and the person

1. **Resolved in the review 1 revision (R-01):** C2 is now pinned; see "Revision after review 1". Original note: **C2 EventBridge mapping is not pinned.** C2 defines the channel `raad.identity.user-confirmed.v1` but no EventBridge `source` or `detail-type`. The code uses source `raad.identity` and detail-type `raad.identity.user-confirmed.v1`, kept in one place (`consumer.py`) and used by both the rule and the consumer. U4 must emit exactly these, or C2 needs a patch. The C2 file does not exist yet in `Raad/contracts/`, so `RaadMoneyService` has no `contracts/pins.yaml` for C2 (C5 was already unpinned).
2. **New platform inputs.** U4 must publish `/raad/<env>/event-bus/arn` and `/raad/<env>/alarm-topic/arn`. Until then the `dev` deploy fails closed at its SSM read, consistent with "platform pieces reach the environment first".
3. **Bundling check:** resolved after the stage (row 30).
4. **Not in this plan:** stg and prd pipelines from `cicd-pipeline.md` (still not built). The team-practice README setup and test commands were added in the review 1 revision (R-05).
5. **Traceability:** `traceability.json` maps all 75 assigned IDs: 67 `OK` with one `RaadMoneyService@checkout/...` file each (the same labels as `source-manifest.json`), and 8 `N/A` for criteria that functional design assigned to U3 or U4. Every `OK` target was checked to exist in `RaadMoneyService`. The advisory traceability check reports those targets as missing because it resolves only paths inside the `Raad` project, not sibling-repo labels. Rows that need a deployed environment (NFR5.1, NFR5.2, NFR6.1, NFR6.2, NFR7.1, AC6.2.1) point to the code or script that implements them; their measurements are still the deployed checks listed above.

## Revision after review 1

`reviews/review-01.md` returned READY with five findings. The person asked to fix what can be fixed and continue. The approved plan is unchanged: this revision changes the built work only. Nothing was committed or deployed, and no AWS API was called.

### R-01: C2 event contract pinned

- **Where the contract lives.** The canonical C2 file is `contracts/c2-identity-events-v1.asyncapi.yaml` in `Raad`. It is owned by U4 and was created there for this revision (commit `36861cd7c7364aaee766fc7dc6e469d73460dc36`, `info.version: 1.0.0-rc.1`, SHA-256 `d244f8e585f907398a3d724dd4085501aee6929c9de38f39f07e8bbcb343c6b6`). Its channel's `x-eventbridge` fixes `source: raad.identity`, `detail-type: raad.identity.user-confirmed.v1` and `payload-location: detail`, which are the values the consumer already used. This unit only pins the contract; it does not own it or change it.
- **Pin.** `RaadMoneyService` now holds a byte-for-byte copy at `contracts/pinned/c2-identity-events/c2-identity-events-v1.asyncapi.yaml`, whose SHA-256 matches the given value and the file at that commit. `contracts/pins.yaml` follows the `RaadMobile` format, with `tag: null` because this is a development pin until U4's provider tests pass and a `contract/c2-identity-events` tag exists.
- **One place for C2 values.** `src/raad_money/consumer.py` keeps `EVENT_SOURCE` and `EVENT_DETAIL_TYPE` and adds `REQUIRED_PAYLOAD_FIELDS`, the seven fields of `UserConfirmedPayload.required`. The stack's EventBridge rule still imports the first two. `parse_event` now refuses an event that is missing any required field, right after the environment check, so source, type and environment are still checked first. Behavior is unchanged: each missing field was already refused by its own check, and the result is still `quarantined-invalid`.
- **Test (test-after).** The new file `tests/unit/test_c2_contract.py` has 9 tests. It reads only the pinned copy, with the YAML reader the C1 contract test already uses, so no dependency was added. The tests check that:
  - the copy's SHA-256 equals `pins.yaml`, and the copy is major version 1;
  - `EVENT_SOURCE` and `EVENT_DETAIL_TYPE` equal the pinned `x-eventbridge` values, and the payload is in `detail`;
  - the stack's only EventBridge rule has exactly the pinned source and detail-type plus the environment filter in `dev`, `stg` and `prd`, using the same `MoneyServiceStack` and `Template.from_stack` approach as `test_service_stack.py`;
  - `REQUIRED_PAYLOAD_FIELDS` equals the pinned schema's `required` list, resolved through the channel's message and payload `$ref`s;
  - the valid test payload matches the pinned required fields, the `specVersion` pattern and the `environment` enum, and parses;
  - an event missing any pinned required field is refused.
- **The tests can fail.** Three throwaway mutations were each run and reverted. A wrong `EVENT_DETAIL_TYPE` failed 4 tests (the mapping test and the rule in all three environments). One byte appended to the pinned copy failed the SHA-256 test. An extra required field in the consumer failed 2 tests.
- **Not done here.** The review also asks for a deployed check that a real U4 event creates a wallet. That needs U4's producer and a deployed `dev`, so it joins R-04's deployed checks below.

### R-03: generated coverage report

- `.gitignore` now ignores exactly `artifacts/coverage/money-core.json`. `git check-ignore` confirms this. The tracked U1 evidence file `artifacts/coverage/u1-ledger.json` is not ignored and was not changed.
- The report was removed from `source-manifest.json`. The money-core command in CI and in `unit-test-instructions.md` still writes it to the same path.

### R-05: README

`README.md` now has:
- the prerequisites: `uv`, Python 3.12 pinned in `pyproject.toml`, Node.js for the AWS CDK CLI, and Docker for DynamoDB Local and Lambda bundling;
- the setup command `uv sync --locked --all-groups`;
- the full-suite test command, run after `docker compose up -d dynamodb-local`;
- the two money-core coverage commands;
- the C1 consumer register row: `openapi/raad-money-v1.yaml`, contract ID `c1-money-api`, pinned by `RaadMobile`, and by `Raad` for the edge `Error` shape;
- the contracts this repo consumes: C2, pinned in `contracts/pins.yaml`, and C5, not pinned yet;
- one line saying that the `stg` and `prd` pipelines are not built yet.

It names no account ID, email address or secret. For the placeholder `cdk synth` inputs it points to `ci.yml` instead of repeating them.

### Commands run and results (revision)

| # | Command (in `RaadMoneyService` unless noted) | Result |
|---|---|---|
| R1 | `uv run pytest tests/unit tests/integration -q`, before any change (baseline) | 427 passed; 95.68% total |
| R2 | `shasum -a 256` of the `Raad` file, of the pinned copy, and of `git show 36861cd…:contracts/c2-identity-events-v1.asyncapi.yaml` (in `Raad`); `cmp` of the copy and the source | all three `d244f8e5…c6b6`; files identical |
| R3 | `uv run pytest tests/unit/test_c2_contract.py tests/unit/test_consumer.py tests/unit/test_service_stack.py --no-cov` | 68 passed |
| R4 | the three throwaway mutations above, each reverted | 4, 1 and 2 failures as intended; 9 passed after the restore, with the hash rechecked |
| R5 | `git check-ignore -v` on `money-core.json` and `u1-ledger.json` | the first is ignored by `.gitignore:15`; the second is not ignored and is still tracked |
| R6 | `uv run ruff format --check src tests scripts` | 44 files already formatted |
| R7 | `uv run ruff check src tests scripts` | All checks passed |
| R8 | `uv run mypy src` | Success: no issues found in 13 source files |
| R9 | `uv run openapi-spec-validator openapi/raad-money-v1.yaml` | OK |
| R10 | `uv run pytest tests/unit tests/integration`, with DynamoDB Local on 127.0.0.1:8000 | **436 passed** (329 unit, 107 integration) in 43 s; 95.53% total (floor 80%); `consumer.py` 99% |
| R11 | the money-core runner (exact command in `unit-test-instructions.md`) | 95 passed; 100.00% |
| R12 | `uv run python scripts/check_ledger_coverage.py artifacts/coverage/money-core.json` | `ledger.py line=100.00% branch=100.00%`, `transfers.py line=100.00% branch=100.00%` |
| R13 | `uv run pip-audit` | No known vulnerabilities found (the local package was skipped because it is not on PyPI) |
| R14 | `rm -rf cdk.out`, then `uv run cdk synth --no-notices -q` with `RAAD_ENVIRONMENT=dev`, the four CI fixture inputs from `.github/workflows/ci.yml` and `CDK_DEFAULT_REGION=us-east-1`. The AWS credential chain was blanked (`AWS_PROFILE` unset, config and credentials files set to `/dev/null`, instance metadata disabled), so the CLI could not look up an account through AWS | exit 0. One Lambda asset, shared by both functions, was bundled in `public.ecr.aws/sam/build-python3.12`, and its `consumer.py` includes `REQUIRED_PAYLOAD_FIELDS`. cdk-nag report: 0 non-compliant rows (14 compliant; 7 suppressed, each with its reason). Stack metadata: 0 `aws:cdk:error`, 0 `aws:cdk:warning`. Resources unchanged: 3 tables, 2 functions, 1 Function URL, 3 queues, 1 rule (`source: [raad.identity]`, `detail-type: [raad.identity.user-confirmed.v1]`, `detail.environment: [dev]`), 9 alarms, 1 dashboard and 1 secret |

**Coverage note.** Total coverage dropped 0.15 points from the baseline (95.68% to 95.53%). All of the drop is in `storage.py`, which this revision did not touch. The lines that change between runs (568 and 636–641) are branches taken only when two concurrent calls race, such as one wallet setup for the same holder winning or one caller attaching a profile version first. The concurrency tests reach them only when threads actually collide. The 95.79% recorded earlier came from another run of the same suite.

### Carried forward

- **R-02 (Major): `dev` cutover steps outside the pipeline.** Not changed. The one-time `-c historyIndexes=1` deploy, the U1 ordinal seeding with `migrate_transactions.py --seed-ordinals --apply --writes-quiesced`, and the SSM reads that fail closed (`/raad/<env>/event-bus/arn`, `/raad/<env>/alarm-topic/arn`) depend on three things this unit does not have: U4's platform parameters in `dev`, the pipeline stages, and a deployed environment to rehearse against. The review's ordered runbook and `deploy-dev.yml` guard were therefore not written. Decisions 8 and 9 and open point 2 still stand.
- **R-04 (Minor): deployed checks and alarm recovery.** Not changed. The `dev` smoke test, the latency load evidence, alarm delivery and the restore drill all need a deployed environment and U4's alarm topic. The design's "three healthy windows" recovery cannot be built with native CloudWatch alarms (decision 11). The NFR5, NFR6 and NFR7 targets stay unproven until these checks run, and the checks remain a gate before `stg` and `prd`. The deployed check from R-01, that a real U4 `UserConfirmed` event creates a wallet, is added to this list.
- **`stg` and `prd` pipelines** (the second half of R-05) stay outside this plan, and they must exist before any `prd` deploy.

### Files written in this revision

- `RaadMoneyService`: `.gitignore`, `README.md`, `contracts/pins.yaml`, `contracts/pinned/c2-identity-events/c2-identity-events-v1.asyncapi.yaml`, `src/raad_money/consumer.py` and `tests/unit/test_c2_contract.py`.
- Record: this file and `source-manifest.json`. The manifest drops `artifacts/coverage/money-core.json` and adds the new `RaadMoneyService@checkout/...` files, plus the `Raad` workspace path `contracts/c2-identity-events-v1.asyncapi.yaml`, which was created for this revision and was not edited by this unit.
- Unchanged: `unit-test-instructions.md`, because no command and no test-file list changed. `traceability.json`, because no row has a better target: BR2.2, BR2.11 and NFR5.5 still point to the consumer, and AC1.2.3 and AC1.2.5 to its integration tests. Every `RaadMoneyService@checkout/` target still exists.
