## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-16T20:19:03Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Open points 1; RaadMoneyService src/raad_money/consumer.py | The account-confirmed event (C2) has no pinned EventBridge `source` or `detail-type`. contract-summary.md defines only the channel name. U2 chose `raad.identity` / `raad.identity.user-confirmed.v1` itself, and the EventBridge rule and consumer both depend on it. If U4 emits anything else, wallets are never created from confirmed accounts and the failure is silent: the rule never matches, so nothing reaches the consumer or its DLQ. There is also no C2 pin file in the service repo. | Before approval, patch C2 in the shared contracts to name this source and detail-type (or get U4's agreement), and add a C2 pin in RaadMoneyService. Add a deployed check that a real U4 event creates a wallet. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Decisions 8, 9 and Open point 2; RaadMoneyService .github/workflows/deploy-dev.yml | A merge to `main` cannot deploy cleanly to `dev` without manual steps outside the pipeline. (a) The existing `dev` Transactions table needs a one-time `-c historyIndexes=1` deploy first, because the routine deploy would delete the second index. (b) The deploy fails closed until U4 publishes `/raad/<env>/event-bus/arn` and `/raad/<env>/alarm-topic/arn`. (c) U1 wallets return 503 for transfers and history until `migrate_transactions.py --seed-ordinals --apply --writes-quiesced` is run. This conflicts with the team rule that every merge to `main` deploys to `dev` and then runs the smoke test. | Document the one-time cutover as an ordered runbook in the repo, with a guard in `deploy-dev.yml` that fails with a clear message if the index or seed step is not done. Confirm the U4 SSM parameters exist before merge. | Unresolved |
| R-03 | Minor | RaadMoneyService artifacts/coverage/money-core.json (untracked, listed in source-manifest.json) | A generated coverage report is listed as a source deliverable, and `.gitignore` does not exclude `artifacts/`. A CI run regenerates it with each run's data, so it would be committed as noise or drift. | Add `artifacts/coverage/` to `.gitignore` and remove it from the source manifest. | Resolved (reviewer) |
| R-04 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Decisions 11; Checks not run | The design's "three consecutive healthy windows" alarm recovery cannot be done with native CloudWatch alarms, so alarms recover on a single evaluation. The `dev` smoke test, latency load evidence, alarm delivery and the restore drill are deferred. NFR5, NFR6 and NFR7 targets are therefore unproven. | Record the alarm-recovery deviation as accepted in the NFR record. Keep the deferred deployed checks as a gate before `stg` and `prd`. | Unresolved |
| R-05 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/code-generation/code-summary.md > Open points 4 | The README is unchanged, though the team practice requires one documented setup command and one test command per repo. The `stg` and `prd` pipelines from `cicd-pipeline.md` are out of this plan. | Update the README with the setup and test commands and the new U2 cutover steps. Track the `stg` and `prd` pipelines as follow-up work before any `prd` deploy. | Resolved (reviewer) |
| R-06 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/inception/contract-design/contract-summary.md > C2 channel; RaadMoneyService contracts/pins.yaml | `contract-summary.md` still names only the channel address `raad.identity.user-confirmed.v1`. The EventBridge `source` and `detail-type` live only in the new Raad file, which is a development pin at `1.0.0-rc.1` with `tag: null`. It is committed on branch `aidlc/u1-money-service`, not on `main`, and U4's provider tests do not exist yet. A U4 emitter built from the summary alone could still diverge, and the rule would then silently never match. | Merge the C2 file to Raad `main` and tag it. Update `contract-summary.md` to reference the EventBridge mapping. Have U4 add a provider test against the file. Move the pin to the tag. Keep a deployed check that a real U4 event creates a wallet. | New |

> R-01 Reviewer note: The canonical C2 file exists at `contracts/c2-identity-events-v1.asyncapi.yaml` in Raad (commit 36861cd) with `x-eventbridge` source `raad.identity` and detail-type `raad.identity.user-confirmed.v1`. `contracts/pins.yaml` pins it and the byte copy has the same SHA-256 (d244f8e5...) as the canonical file. `consumer.py` enforces `REQUIRED_PAYLOAD_FIELDS`, and the 9 contract tests pass. Residual risk: U4 has not yet agreed to or implemented it (see the new findings).

> R-02 Reviewer note: No change to the cutover. The deploy workflow still reads the U4 SSM parameters `/raad/dev/event-bus/arn` and `/raad/dev/alarm-topic/arn`, and fails closed until they exist. The README has no ordered runbook for the one-time `-c historyIndexes=1` deploy or the `--seed-ordinals` migration, and `deploy-dev.yml` has no guard for those steps. The builder carried this forward.

> R-03 Reviewer note: `.gitignore` now excludes `artifacts/coverage/money-core.json` and `git status --ignored` shows it ignored. The path is not in the source manifest.

> R-04 Reviewer note: The alarm-recovery deviation, the dev smoke test, latency evidence, alarm delivery and the restore drill all remain deferred. The builder carried this forward.

> R-05 Reviewer note: The README now has Setup (`uv sync --locked --all-groups`), test commands and the money-core coverage command. The `stg` and `prd` pipelines remain out of scope and still need follow-up tracking.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `ruff format --check src tests scripts` | PASS: 44 files already formatted | Clean. |
| `ruff check src tests scripts` | PASS: all checks passed | Clean. |
| `mypy src` | PASS: no issues in 13 source files | Clean. |
| `pytest tests/unit tests/integration` | PASS: 436 passed, total coverage 95.80% | Above the 80% floor. `ledger.py` and `transfers.py` are at 100%. |
| `pytest tests/unit/test_c2_contract.py --no-cov -q` | PASS: 9 passed | The pin, the consumer constants, the CDK rule and the payload fields agree. |
| `openapi-spec-validator openapi/raad-money-v1.yaml` | PASS: OK | The spec is valid. |

### Summary

The revision fixes R-01, R-03 and R-05, and every local check is green. R-02 (the one-time dev cutover and the dependency on U4's SSM parameters) is still open and is the main thing to weigh. It blocks a clean merge-to-dev deploy and has no runbook or guard. The deployed proof for NFR5 to NFR7 is deferred, as R-04 records. One Minor item is new: the C2 pin is an unmerged development pin and U4 has not agreed to it. This is advisory, so I judge the code ready for approval with R-02 tracked to resolution before the first dev deploy.
