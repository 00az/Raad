## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-16T19:44:12Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Open points 1; RaadMoneyService src/raad_money/consumer.py | The account-confirmed event (C2) has no pinned EventBridge `source` or `detail-type`. contract-summary.md defines only the channel name. U2 chose `raad.identity` / `raad.identity.user-confirmed.v1` itself, and the EventBridge rule and consumer both depend on it. If U4 emits anything else, wallets are never created from confirmed accounts and the failure is silent: the rule never matches, so nothing reaches the consumer or its DLQ. There is also no C2 pin file in the service repo. | Before approval, patch C2 in the shared contracts to name this source and detail-type (or get U4's agreement), and add a C2 pin in RaadMoneyService. Add a deployed check that a real U4 event creates a wallet. | New |
| R-02 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Decisions 8, 9 and Open point 2; RaadMoneyService .github/workflows/deploy-dev.yml | A merge to `main` cannot deploy cleanly to `dev` without manual steps outside the pipeline. (a) The existing `dev` Transactions table needs a one-time `-c historyIndexes=1` deploy first, because the routine deploy would delete the second index. (b) The deploy fails closed until U4 publishes `/raad/<env>/event-bus/arn` and `/raad/<env>/alarm-topic/arn`. (c) U1 wallets return 503 for transfers and history until `migrate_transactions.py --seed-ordinals --apply --writes-quiesced` is run. This conflicts with the team rule that every merge to `main` deploys to `dev` and then runs the smoke test. | Document the one-time cutover as an ordered runbook in the repo, with a guard in `deploy-dev.yml` that fails with a clear message if the index or seed step is not done. Confirm the U4 SSM parameters exist before merge. | New |
| R-03 | Minor | RaadMoneyService artifacts/coverage/money-core.json (untracked, listed in source-manifest.json) | A generated coverage report is listed as a source deliverable, and `.gitignore` does not exclude `artifacts/`. A CI run regenerates it with each run's data, so it would be committed as noise or drift. | Add `artifacts/coverage/` to `.gitignore` and remove it from the source manifest. | New |
| R-04 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Decisions 11; Checks not run | The design's "three consecutive healthy windows" alarm recovery cannot be done with native CloudWatch alarms, so alarms recover on a single evaluation. The `dev` smoke test, latency load evidence, alarm delivery and the restore drill are deferred. NFR5, NFR6 and NFR7 targets are therefore unproven. | Record the alarm-recovery deviation as accepted in the NFR record. Keep the deferred deployed checks as a gate before `stg` and `prd`. | New |
| R-05 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Open points 4 | The README is unchanged, though the team practice requires one documented setup command and one test command per repo. The `stg` and `prd` pipelines from `cicd-pipeline.md` are out of this plan. | Update the README with the setup and test commands and the new U2 cutover steps. Track the `stg` and `prd` pipelines as follow-up work before any `prd` deploy. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `uv run ruff format --check src tests scripts` | PASS: 43 files already formatted | Clean. |
| `uv run ruff check src tests scripts` | PASS: All checks passed | Clean. |
| `uv run mypy src` | PASS: no issues found in 13 source files | Strict typing is clean. |
| `uv run pytest tests/unit tests/integration -p no:cacheprovider` | PASS: 427 passed; total coverage 95.79% (floor 80%) | Meets the repository floor. The lowest modules are api.py at 92%, storage.py at 93% and identity.py at 85%, and all stay above the 80% repository floor. |
| money-core pytest with `--cov-fail-under=95` | PASS: 95 passed; 100.00% | Meets the floor. |
| `scripts/check_ledger_coverage.py` | PASS: ledger.py line 100.00% branch 100.00%; transfers.py line 100.00% branch 100.00% | Both money-core modules exceed 95% line and branch. |
| `uv run openapi-spec-validator openapi/raad-money-v1.yaml` | PASS: OK | The contract is valid. |

The validation tools were run by me. I did not run `cdk synth`, `cdk-nag`, `pip-audit` or `cdk deploy`. The cdk-nag and pip-audit results come from code-summary.md rows 23 and 30 and are not independently verified here.

### Summary

The money core is sound. Whole-halala integer arithmetic, atomic seven-item commit, replay and key-reuse handling, and the Hypothesis conservation and overdraw concurrency tests against DynamoDB Local all check out. Every check I ran passed, and the money core is at 100% line and branch coverage. The two Major items are integration and rollout risks (the unpinned C2 event mapping and the manual dev cutover), not defects in the code, so the verdict is READY, and the human should weigh both before approving.
