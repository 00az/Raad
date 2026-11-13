# Unit Test Instructions — U1 Walking Skeleton

Conversation language: English.

## Scope and Ordering

Run tests only after the runner/configuration for that repository is ready. Use the team's custom Testing Contract exactly: Ledger money-movement core tests are written first, then the implementation, then refactored while passing. For every other layer, implement the layer first, then write and run its tests before the work lands. Do not convert the custom mixed ordering into layer-local TDD.

## Commands

Run each command from the listed repository directory after installing from its lockfile:

| Repository | Command | Purpose |
|---|---|---|
| `Raad` (`infrastructure/`) | `cd infrastructure && uv sync --locked --all-groups && uv run pytest` | Python CDK stack tests and synthesis/security assertions. |
| `RaadMoneyService` (`../money-service/`) | `uv sync --locked --all-groups && uv run pytest tests/unit` | Service unit tests, Hypothesis money properties and the unit-scoped 80% line floor. Run from `../money-service`. |
| `RaadMoneyService` (`../money-service/`) | `docker compose up -d dynamodb-local` then `uv run pytest tests/integration` | Real local DynamoDB transaction, uniqueness, query and API-boundary checks. Run both commands from `../money-service`; stop the disposable container after integration checks. |
| `RaadMoneyService` (`../money-service/`) | `uv run pytest tests/unit/test_ledger_rules.py --cov=src/raad_money/ledger --cov-branch --cov-fail-under=95` | Ledger-specific line and branch coverage floor. Run from `../money-service`. |
| `RaadMobile` (`../mobile/`) | `flutter pub get && flutter test --coverage` | Widget/unit checks and the mobile 80% line floor. Run from `../mobile`. |
| `RaadMobile` (`../mobile/`) | `flutter test integration_test` | Walking-skeleton integration flow on a running iOS simulator or Android emulator configured for dev. Run from `../mobile`. |
| Workspace | `./scripts/verify-dev.sh` | Authorized integrated smoke and simulator verification against dev after all three repos are deployed and both users/wallets are ready. |

The actual Python module path and local DynamoDB Compose service name are finalized when the greenfield project skeleton is created; the plan preserves the exact command shape and test grouping. Do not put credentials in command arguments. Setup obtains them at runtime from the dev Secrets Manager secret. Never insert fixture rows directly into a deployed store.

## Required Coverage and Evidence

- Keep at least 80% line coverage independently in `Raad`, `RaadMoneyService` and `RaadMobile`.
- Keep at least 95% line and branch coverage in the `RaadMoneyService` Ledger money-movement core.
- Use 5–8 cases per logical component under the Standard strategy, plus integration tests at the DynamoDB transaction, C1 API, edge forwarding and Flutter/dev boundaries.
- Property-based checks prove transfer conservation and non-negative balances. The transaction/concurrency checks use the real local DynamoDB container, not a mock.
- Record the test command, tool/runtime versions, fixture IDs and result. Keep API, mobile and performance fixtures independent or record starting balances and assert deltas.
- Do not count fast refusals, technical failures or unknown outcomes as successful transfers or as latency passes. Do not claim any test or deployed result until it has actually run.
