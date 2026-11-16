# Unit Test Instructions — U2 Money Service

## Repository and Runner

Repository: `RaadMoneyService` (`00az/RaadMoneyService`). Use the repository's existing `uv` environment, pinned Python 3.12 and committed lockfile. Confirm the current pytest command and test directory from the repository configuration before editing this file; the unit-scoped runner must include both pytest and coverage reporting. Bootstrap runner/configuration before the first planned test. Do not invent a path or dependency version if the repository already specifies it.

## Required Test Coverage

- Keep Standard strategy volume: five to eight focused unit tests per affected component and integration tests for key boundaries.
- Money core uses TDD: write each failing test before its implementation, capture the failing result, then implement and refactor with tests green.
- Other layers (HTTP handlers, persistence adapters, event consumer, CDK infrastructure and CI configuration) use test-after: implement the layer, then add and run its tests.
- Use pytest and Hypothesis for arithmetic invariants, replay and validation. Test that total halalas are conserved and no wallet balance becomes negative.
- Concurrency and transactional integration cases run against a real Docker local data-store container, never only a mock.
- Preserve at least 80% line coverage for the backend repository and at least 95% line and branch coverage for the money-movement core. Do not lower thresholds to make a run pass.

## Required Commands and Reporting

Read `pyproject.toml`, `uv.lock`, and CI workflow before fixing exact commands. Run the repository's documented lint, strict type check, unit-test/coverage, integration-test, dependency-audit, CDK synth/assertions/`cdk-nag`, and OpenAPI validation commands. Integration checks requiring Docker must be reported as not run if Docker is unavailable, with the reason. Record every command actually run and its result in `code-summary.md`; distinguish unavailable checks from failures and from unrun checks.

## Exact Commands (fixed at Code Generation from `pyproject.toml`, `uv.lock` and `.github/workflows/ci.yml`)

Run from the `RaadMoneyService` checkout with the locked environment (`uv sync --locked --all-groups`). Integration tests need DynamoDB Local on `127.0.0.1:8000`: `docker compose up -d dynamodb-local` (the compose healthcheck probes `/shell/`, which this image answers with 400, so do not wait on `--wait`; the endpoint is ready when it answers).

| Check | Command | Gate |
|---|---|---|
| Format | `uv run ruff format --check src tests scripts` | any change blocks |
| Lint | `uv run ruff check src tests scripts` | any finding blocks |
| Strict types | `uv run mypy src` | any error blocks |
| Full suite and repository floor | `uv run pytest tests/unit tests/integration` | `pyproject.toml` `--cov-fail-under=80` |
| Money-core floor (unit-scoped runner) | `uv run pytest tests/unit/test_ledger_rules.py tests/unit/test_u2_money_rules.py tests/unit/test_u2_money_core.py tests/unit/test_u2_transfer_service.py --cov-reset --cov=raad_money.ledger --cov=raad_money.transfers --cov-branch --cov-report=json:artifacts/coverage/money-core.json --cov-report=term-missing --cov-fail-under=95` | 95% combined |
| Money-core line and branch, per module | `uv run python scripts/check_ledger_coverage.py artifacts/coverage/money-core.json` | each of `ledger.py` and `transfers.py` >=95% line AND >=95% branch |
| Dependency audit | `uv run pip-audit` | any finding blocks |
| Contract | `uv run openapi-spec-validator openapi/raad-money-v1.yaml` (also inside the suite) | invalid document blocks |
| CDK synth, bundling and cdk-nag | `uv run cdk synth` with the CI fixture inputs `RAAD_EDGE_ROLE_ARN`, `RAAD_CORRELATION_SECRET_ARN`, `RAAD_EVENT_BUS_ARN`, `RAAD_ALARM_TOPIC_ARN` | any unsuppressed AwsSolutions finding blocks |

The money-movement core measured for the 95% floors is `raad_money.ledger` (amount validation, balance arithmetic, transfer rules, outcomes and fingerprints) and `raad_money.transfers` (duplicate-request handling). No coverage-ignore pragma is used anywhere in the repository.

## Test Matrix

| Area | Cases |
|---|---|
| Ledger transfer rules | Minimum/maximum amount, out-of-range and over-precision values, self-transfer, insufficient funds, atomic debit/credit, unique reference |
| Idempotency | Matching request replay, mismatched fingerprint, concurrent duplicate, persisted refusal replay, lost-response recovery and crash boundary per the human-approved state model |
| History | Sent/received merge ordering, tie-break, page limits, snapshot stability, cursor integrity/expiry/bindings, no duplicate or skipped entries |
| WalletDirectory | Normalization, exact lookup, email ownership collision, unknown recipient, privacy-safe responses |
| C1 API | Authentication, owner derivation, request validation, status/error schema, safe internal failures, cursor and replay behavior, OpenAPI conformance |
| C2 consumer | Valid event, duplicate event, duplicate user under a different event ID, wrong environment/source, malformed input, transient persistence failure, retry and DLQ route |
| Storage integration | Wallet setup transaction, transfer transaction, concurrency against local container, consistency after injected failures |
| CDK infrastructure | Environment isolation, table PITR/retention/deletion protection, least-privilege role grants, IAM-only Function URL, C2 retries/DLQ, alarm/dashboard configuration, cdk-nag |
