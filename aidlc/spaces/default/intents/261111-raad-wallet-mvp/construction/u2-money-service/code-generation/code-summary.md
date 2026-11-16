# U2 implementation evidence

## Runner readiness and unchanged-tree baseline

2026-11-16: `uv run pytest tests/unit` in registered `money-service@checkout` passed **133 tests**, repository combined coverage **89.35%**. Python 3.12.4, pytest 9.2.0; existing locked environment needs no dependency/configuration change.

Before the first U2 Red, the exact scoped command is `uv run pytest tests/unit/test_ledger_rules.py tests/unit/test_u2_money_rules.py --cov-reset --cov=raad_money.ledger --cov-report=term-missing --cov-fail-under=95`. This narrows the measured source to the money core rather than weakening the repository-wide floor. The full repository command remains `uv run pytest tests/unit tests/integration` with its existing 80% floor. Final core evidence must separately show line and branch percentages.

An earlier narrow baseline `uv run pytest tests/unit/test_ledger_rules.py` passed 25 tests and 100% core coverage but exited 1 because its default repository-wide coverage was 10.23%; this is retained as a command failure, not a failed money test or accepted coverage result.

## Approved design reconciliation

The plan's reservation-conflict sentence is historical: current approved functional/reliability designs require absent → final outcome only, without durable pending reservations. Its “two tables” phrase is historical: preserve Ledger, canonical Transactions and WalletDirectory. Replays retain original business fields and status, with the current request's fresh transport correlation ID; never store caller correlation IDs in outcomes. Deployment/live execution alone is person-deferred by `fcf6b4bc`; unimplemented local checks remain gaps.

## Progress

Source implementation and U2 Red/Green evidence pending. No U2 deployment or live verification performed.
