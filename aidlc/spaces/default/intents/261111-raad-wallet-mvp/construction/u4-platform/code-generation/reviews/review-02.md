## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-18T02:14:48Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | infrastructure/raad_platform/stacks.py > `_account_firewall` (regional WAF on the user pool) and the AwsSolutions-COG1 exception reason | The regional WAF rules match the `x-amzn-cognito-operation-name` header, and the code summary lists that header's real value as an open check. Every test is a synth-time assertion, so a wrong header name or value would deploy a WAF that never matches, and nothing local would fail. The new COG1 exception names this WAF as a compensating control for the missing symbol rule, so the exception's justification currently rests on an unverified control. | Before dev is called done, make the dev check for the WAF an explicit gate: send a real sign-up or sign-in burst and confirm a block. Until then, soften the COG1 reason to say the WAF is unverified, or drop the WAF from the list of controls. | Accepted risk |
| R-02 | Minor | infrastructure/raad_platform/stacks.py > `_restrict_bus_publishers` | The three Deny statements bind every principal, including operators, and nothing allows a controlled path to replay or hand-send a C2 event. The deploy-time dependency ordering of the three policy writes is only synth-tested. The first dev deploy may hit a concurrent-modification failure or lock out the publisher. | In the dev runbook, say that C2 test events must come from a real confirmation. Watch the first deploy of the three bus-policy resources, and confirm the publisher's PutEvents succeeds in dev (P12). | Accepted risk |
| R-03 | Minor | infrastructure/raad_platform/edge/rate_store.py > `WINDOW_SECONDS`, `consume` | Counters are fixed one-minute windows with the minute in the key. A caller can spend a full budget at the end of one minute and again at the start of the next, so up to 2x of the stated limit (20 sends, 60 lookups) can land within a few seconds. The code summary and docstring do not say this. | Record the fixed-window burst as an accepted property in C5 or the code summary, or say whether the limits are meant as per-minute approximations. | Accepted risk |
| R-04 | Minor | infrastructure/raad_platform/stacks.py > `reserved_concurrent_executions` (edge 20 in dev only; publisher, processor and stub 2 each) | The reserved concurrency for dev (20 + 2 + 2 + 2) is already listed as an open prerequisite. The edge has no reservation in stg and prd, so a Lambda throttle there is limited only by the account pool shared with U2, and no check shows that headroom. | Before the first deploy, confirm the account's unreserved concurrency stays at or above 100 after these reservations. Record the answer in the deployment prerequisites. | Accepted risk |
| R-05 | Minor | .github/workflows/ci.yml and the Gitleaks, synth and integration steps | The new CI workflow, including the Gitleaks step, the three-environment synth loop and the DynamoDB Local integration step, has never run. Only the equivalent local commands were run. | Treat the first PR run as an owed check and fix any difference between CI and local before merging. | Accepted risk |
| R-06 | Minor | infrastructure/raad_platform/stacks.py > cdk-nag warnings CFR1 and COG2 | The two warnings are reported and not suppressed, with no decision recorded. MFA is not in C3. | Have the person decide at the gate to accept or schedule both warnings, and record the decision next to the warnings in the code summary. | Accepted risk |
| R-07 | Minor | infrastructure/raad_platform/stacks.py > AwsSolutions-COG8 exception reason (IdentityStack nag suppressions) | The COG8 reason still says the regional WAF is one of the "tested" compensating controls. Step 16 made the WAF an unverified control and fixed this for COG1 only, so one exception now says the WAF is unverified and the next says it is tested. The code summary admits this and leaves it to the person. | Reword COG8 the same way as COG1 (WAF not relied on until the dev P10 burst observes a refusal), or have the person accept the wording explicitly at the gate. | New |
| R-08 | Minor | infrastructure/README.md > "Dev gate: C3 P10"; scripts/verify-dev.sh; .github/workflows/deploy-dev.yml | "Dev is not done until P10 passes, and a failed or pending P10 blocks release to stg" is a procedure only. Nothing runs `--burst`, and `verify-dev.sh` and `deploy-dev.yml` do not look at P10 evidence. The README also says the burst is dev only, while the tool accepts `stg` as well as `dev`. | Add the burst and the `secondCallerUnaffected` record to the dev runbook or `verify-dev.sh`, and make any later stg promotion step read the P10 evidence. Align the README wording with the tool (dev only, or dev and stg). | New |
| R-09 | Minor | scripts/verify-dev.sh (Construction Verification Command) | I could not run the command. It needs a deployed dev environment, simulator and emulator IDs, a fixture secret ARN and the sibling `money-service` and `mobile` checkouts. No AWS call is authorized, so the end-to-end result is unverified here. The Step 16 claims rest on offline tests only. | Run it once dev exists. Treat the P10 burst result as owed evidence at that point, since the WAF header value has still never been observed on a real pool. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| pytest (16-file U4 selection, `--cov=raad_platform --cov=../scripts`) | 420 passed; total coverage 90.90%, 80% floor met. `check_identity_capabilities.py` 95%, `stacks.py` 99% | Matches the summary's "420 passed; 90.90%" and the 95% figure for the capabilities script. Uncovered lines in the capabilities script are 173, 185, 335-336, 397-399, 406 and 414. |
| ruff check | All checks passed | Clean. |
| mypy (strict, 17 source files) | Success: no issues found | Clean. |
| `scripts/verify-dev.sh` | Not run | Needs deployed dev and AWS. Recorded as a finding above. |

### Summary

Step 16 does what the summary says. The COG1 reason no longer relies on the unverified WAF, and the opt-in `--burst` probe runs only after the scope checks pass. It refuses prd, counts only admitted requests against a 200 budget, and fails safe when the result is inconclusive. All 420 tests, ruff and strict mypy are clean. The remaining gaps are small: COG8 still calls the WAF a tested control, and the P10 gate is a written procedure that no script or pipeline step enforces.
