## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-17T20:56:03Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | infrastructure/raad_platform/stacks.py > `_account_firewall` (regional WAF on the user pool) and the AwsSolutions-COG1 exception reason | The regional WAF rules match the `x-amzn-cognito-operation-name` header, and the code summary lists that header's real value as an open check. Every test is a synth-time assertion, so a wrong header name or value would deploy a WAF that never matches, and nothing local would fail. The new COG1 exception names this WAF as a compensating control for the missing symbol rule, so the exception's justification currently rests on an unverified control. | Before dev is called done, make the dev check for the WAF an explicit gate: send a real sign-up or sign-in burst and confirm a block. Until then, soften the COG1 reason to say the WAF is unverified, or drop the WAF from the list of controls. | New |
| R-02 | Minor | infrastructure/raad_platform/stacks.py > `_restrict_bus_publishers` | The three Deny statements bind every principal, including operators, and nothing allows a controlled path to replay or hand-send a C2 event. The deploy-time dependency ordering of the three policy writes is only synth-tested. The first dev deploy may hit a concurrent-modification failure or lock out the publisher. | In the dev runbook, say that C2 test events must come from a real confirmation. Watch the first deploy of the three bus-policy resources, and confirm the publisher's PutEvents succeeds in dev (P12). | New |
| R-03 | Minor | infrastructure/raad_platform/edge/rate_store.py > `WINDOW_SECONDS`, `consume` | Counters are fixed one-minute windows with the minute in the key. A caller can spend a full budget at the end of one minute and again at the start of the next, so up to 2x of the stated limit (20 sends, 60 lookups) can land within a few seconds. The code summary and docstring do not say this. | Record the fixed-window burst as an accepted property in C5 or the code summary, or say whether the limits are meant as per-minute approximations. | New |
| R-04 | Minor | infrastructure/raad_platform/stacks.py > `reserved_concurrent_executions` (edge 20 in dev only; publisher, processor and stub 2 each) | The reserved concurrency for dev (20 + 2 + 2 + 2) is already listed as an open prerequisite. The edge has no reservation in stg and prd, so a Lambda throttle there is limited only by the account pool shared with U2, and no check shows that headroom. | Before the first deploy, confirm the account's unreserved concurrency stays at or above 100 after these reservations. Record the answer in the deployment prerequisites. | New |
| R-05 | Minor | .github/workflows/ci.yml and the Gitleaks, synth and integration steps | The new CI workflow, including the Gitleaks step, the three-environment synth loop and the DynamoDB Local integration step, has never run. Only the equivalent local commands were run. | Treat the first PR run as an owed check and fix any difference between CI and local before merging. | New |
| R-06 | Minor | infrastructure/raad_platform/stacks.py > cdk-nag warnings CFR1 and COG2 | The two warnings are reported and not suppressed, with no decision recorded. MFA is not in C3. | Have the person decide at the gate to accept or schedule both warnings, and record the decision next to the warnings in the code summary. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `uv run pytest --cov=raad_platform --cov=../scripts` | PASS: 400 passed, 90.43% total (floor 80%) | Matches the code summary. The weakest modules are `telemetry/driver.py` at 83% and `platform_smoke.py` at 86%. Both are above the floor. |
| `uv run ruff check raad_platform tests app.py ../scripts` | PASS | Clean. |
| `uv run mypy raad_platform app.py ../scripts` | PASS: no issues in 17 source files | Strict mode is clean. |
| `RAAD_RATE_DYNAMODB_ENDPOINT=http://127.0.0.1:8002 uv run pytest tests/integration/test_platform_rate_limits.py --no-cov -q` | PASS: 8 passed | Counter admission and refusal are checked against a real DynamoDB Local. |

### Summary

The local code is sound. Every gate I ran was green and matches the summary's figures. The edge, the C2 exclusivity policy and the rate counters hold up when traced end to end. The builder's flagged deviations (COG1 exception, narrowed C5 correlation pattern, HMAC rate keys, 404 on unknown paths, topic policy) are reasonable and documented. The one significant gap is the unverified WAF operation-name header. Nothing local can prove it, and the new COG1 exception leans on it, so I recommend a hard dev check before relying on either.
