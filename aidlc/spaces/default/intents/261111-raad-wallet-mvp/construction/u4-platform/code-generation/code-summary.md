# Code Summary — u4-platform

Conversation language: English.

## Summary

U4 completes the shared platform in `Raad` as local, tested code. Nothing was deployed, no AWS API
was called, and nothing was committed or pushed. Plan Steps 1–16 are complete and ticked. On
17 November the person reopened U4 for review finding R-01 (message 3eb4ad2d), which added Step 16;
see "Step 16 rework (R-01)" below. Step 17 is not ticked: the requirement-level traceability, the
independent architecture review, the person's U4 checkpoint and `aidlc unit publish u4-platform`
belong to the conductor and the person.

Testing followed the approved Testing Contract (custom: test-after for every platform layer). Each
layer was implemented first, then its tests were written and run. No Red/Green evidence was
manufactured.

## What Was Built

| Step | Built |
|---|---|
| 1 | Baseline on the unchanged tree: 145 tests passed, 86.09% coverage. Ruff, format, strict mypy and pip-audit were clean. Logical IDs were recorded for all three stacks in dev, stg and prd. |
| 2 | Dev dependencies `jsonschema` and `pyyaml` (tests only, locked in `uv.lock`). `docker-compose.yml` defines a `rate-dynamodb` service on 127.0.0.1:8002. `tests/conftest.py` blanks the AWS credential chain for every test and loads canonical contracts. Integration tests run only by explicit path. |
| 3 | Canonical C3, C4 and C5 files plus `contracts/README.md` (consumer register and platform outputs). C2 is unchanged byte for byte, so U2's pin (`d244f8e5…`) stays valid. |
| 4 | Native Cognito identity, applied as described under Identity settings below. |
| 5 | C2 producer: the `raad-<env>-identity-events` bus and the `raad_platform/identity/publisher.py` post-confirmation trigger, with its own log group and a role scoped to the contract source and detail type. |
| 6 | Exclusive publishing and shared outputs. Three Deny statements on the bus (described under C2 producer below). `/raad/<env>/event-bus/arn` and `/raad/<env>/alarm-topic/arn` are published, and the existing edge-role, correlation-secret, verifier and public-URL parameters are preserved. The alarm topic now allows `cloudwatch.amazonaws.com` (this account's alarms only). |
| 7 | The `PlatformRateWindows` table (on-demand, `expiresAt` TTL two hours after the window ends, AWS-owned-key encryption, PITR) and `raad_platform/edge/rate_store.py`. The edge may call `dynamodb:UpdateItem` on this table only. |
| 8 | Edge enforcement of verified-caller limits, described under Edge rate limits below. |
| 9 | A regional WAF associated with each environment's user pool, described under Regional WAF on the user pool below. |
| 10 | Validated deployment inputs (`read_deployment_inputs`, described under Deployment inputs below). Logs keep 14 days in dev and 30 in stg/prd. `.env.example` and `infrastructure/README.md` now use placeholders and document the native flow. Root `.gitignore` ignores coverage, Hypothesis, mypy and ruff output. |
| 11 | `raad_platform/configuration.py` and `scripts/write_platform_config.py`. The writer turns one environment's `cdk deploy --outputs-file` document into `config/<env>.json` (C4) and `verifier/<env>.json` (C5) without calling AWS. Identity and edge stacks now emit the outputs it needs. |
| 12 | Alarm windows and observation health, described under Alarms below. |
| 13 | A dev-only stub: `GET /stub/v1/{proxy+}` routes to its own function, which can only write its logs and read the origin secret. stg and prd have no stub route or function. |
| 14 | `scripts/platform_smoke.py` and `scripts/check_identity_capabilities.py`, described under Smoke and capability tools below. |
| 15 | PR CI (`.github/workflows/ci.yml`) and all local gates, listed below. |
| 16 | R-01 rework: the AwsSolutions-COG1 reason no longer relies on the regional WAF; an opt-in `--burst` P10 probe in `scripts/check_identity_capabilities.py`; P10 made an explicit dev gate in `infrastructure/README.md`. Described under Step 16 rework below. |

### Step 16 rework (R-01)

- **COG1 reason.** It now reads: "Compensating controls: the approved A4 rule and Cognito's native sign-in lockout. The regional WAF on this pool is not relied on here: it is unverified until the dev P10 burst check (check_identity_capabilities.py --burst) observes a refusal." A new stack test checks, for dev, stg and prd, that the reason names A4 and native lockout and does not lean on the WAF.
- **Burst probe.** `--burst` works only with `--execute`, only after the existing outputs, environment, account and STS checks pass, and is refused for prd before any client call. From one caller it sends unauthenticated `InitiateAuth` (`USER_SRP_AUTH`) requests for a random `p10-probe-<uuid>@example.invalid` address, with `SRP_A` computed locally as g^a mod N from Cognito's 3072-bit group (checked equal to the RFC 3526 prime). The client is unsigned with one attempt per request, so counts are exact.
- **Budget and pacing.** 200 admitted requests, one every 1.2 seconds, so all fall within 240 seconds of the 300-second WAF window. 200 is above the 100 account-operation limit and below the 300 general limit, so only the account rule can refuse the burst. The script copies the three limits rather than importing CDK; a test keeps them equal to `stacks.py`.
- **Outcomes.** `ForbiddenException` (matched by error code only, because AWS documents both HTTP 400 and 403 for it) is a WAF refusal: the probe stops and records `operationClassificationObserved` and `burstRefusedForOneCaller` as true. A challenge, `NotAuthorizedException` or `UserNotFoundException` counts as admitted. Throttling, network and other errors count as neither. 200 admissions with no refusal record both as false, which fails P10. Five uncounted errors, or pacing that would leave the window, make the run inconclusive and record nothing, so P10 stays pending. `secondCallerUnaffected` stays operator-recorded.
- **Output.** Counts and the outcome only. A test asserts the address, `SRP_A`, pool ID, client ID, provider message text and any `@` never appear.
- **Sources.** [Cognito WAF guide](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html) (SDKs return `ForbiddenException` for a WAF Block); [InitiateAuth API reference](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_InitiateAuth.html); [WAF rate-based caveats](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-caveats.html) (blocking can lag "usually below 30 seconds", "up to several minutes"; the budget leaves about 120 seconds of margin after crossing 100, and a longer lag records false, which fails safe).

### Identity settings (Step 4)

- Email sign-in is case-insensitive. Only email and name are stored, both required and immutable.
- The password rule is exactly A4: 8 or more characters with lower, upper and digit, and no symbol requirement.
- Account recovery is by email only.
- The public client has no secret and no hosted UI or OAuth. `disable_o_auth` is set explicitly, because CDK otherwise enables OAuth flows with an example.com callback.
- Auth flows are SRP plus refresh. The IAM-only admin password flow is kept, because U2's dev fixture scripts use `AdminInitiateAuth`.
- User-existence errors are hidden and token revocation is on.
- Access and ID tokens last 60 minutes. Refresh tokens last a fixed 30 days.
- The hosted-UI domain and the `RAAD_COGNITO_DOMAIN_PREFIX` input are removed.
- There is no paid Plus plan in any environment.

### C2 producer (Steps 5–6)

The publisher publishes only for `PostConfirmation_ConfirmSignUp`, never for a password-reset confirmation. It emits exactly the seven C2 fields from trusted trigger attributes: a new UUID event ID and its own UTC clock. It distinguishes a thrown PutEvents error from a per-entry failure, and it always returns the original event. It logs and meters only the event ID, the environment and a fixed category.

Publishing is exclusive through three Deny statements on the bus, created one after another: every other principal (`aws:PrincipalArn`), every other `events:source` and every other `events:detail-type` is refused.

### Edge rate limits (Step 8)

- The edge authenticates the caller, then charges the verified `sub` before forwarding anything: 30 lookups a minute, 10 sends a minute (each send also uses one lookup), and 60 a minute shared by every other `/money/v1` request.
- A refusal is a flat C1 `429 RATE_LIMITED` with the whole seconds left in the window as Retry-After. A store failure is `503 SERVICE_UNAVAILABLE` with Retry-After. Refused requests never reach U2.
- Paths outside `/money/v1` get `404 NOT_FOUND`, which is outside C1.
- `Accept` is now forwarded, and 503 responses carry Retry-After.
- The Lambda bundle keeps the `raad_platform/edge` package layout. Its handler is `raad_platform.edge.handler.entry`.

### Regional WAF on the user pool (Step 9)

- Account operations (SignUp, ConfirmSignUp, ResendConfirmationCode, InitiateAuth, RespondToAuthChallenge, ForgotPassword, ConfirmForgotPassword) are limited to 100 per IP per 5 minutes.
- Every operation except GetUser is limited to 300 per IP per 5 minutes.
- Rules match the `x-amzn-cognito-operation-name` header, which AWS documents as the identifier, with the bare or service-prefixed name.
- Sampling and logging are off. The CloudFront ACL keeps its own 1000-per-IP rule.

### Deployment inputs (Step 10)

`read_deployment_inputs` checks:

- `RAAD_ENVIRONMENT` is one of dev, stg or prd, with no default.
- The region is us-east-1.
- The account is 12 digits, and matches `RAAD_EXPECTED_ACCOUNT` when that is set.
- The certificate belongs to that account.
- The zone ID format and the alert address are valid.

Errors never echo the alert address.

### Alarms (Step 12)

| Signal | Alarm condition |
|---|---|
| Technical 5xx | ≥1% with ≥20 requests, in two 5-minute windows |
| Transfer technical failures | ≥3 in each of two 5-minute windows |
| Throttles (edge, publisher, processor, rate table) and rate-store failures | ≥1 a minute in two consecutive windows |
| Publisher failures | Any |
| Collector heartbeat | Absent for 3 minutes, with a new one-minute heartbeat schedule |
| Collection failures | A metric separate from "insufficient" |

The public p95 pair alarm is unchanged. Every alarm notifies the topic and states the accepted native recovery deviation. The dashboard gains panels for rate decisions, the publisher and observation health.

### Smoke and capability tools (Step 14)

Both tools do nothing without `--execute`. The outputs must match the environment and account, and STS must report the expected account, before any request.

The smoke tool checks:

- anonymous 401
- direct-origin 403
- TLS 1.1 refused by the server and TLS 1.2 accepted (pending when this client cannot observe the refusal)
- SSM agrees with the outputs
- fixture sign-in reaches the edge
- the dev stub answers

The capability tool tracks P1–P13 from boolean-only evidence plus read-only settings probes. P7 stays pending until both codes and the generic acknowledgement are recorded.

## Files Created or Modified

All 39 paths are workspace-relative and listed in `source-manifest.json`.

| Area | Paths |
|---|---|
| Contracts (new) | `contracts/README.md`, `contracts/c3-sign-in-client-profile-v1.yaml`, `contracts/c4-mobile-environment-config-v1.schema.yaml`, `contracts/c5-money-edge-v1.yaml` |
| Platform source (new) | `infrastructure/raad_platform/configuration.py`, `infrastructure/raad_platform/edge/rate_store.py`, `infrastructure/raad_platform/edge/stub.py`, `infrastructure/raad_platform/identity/__init__.py`, `infrastructure/raad_platform/identity/publisher.py` |
| Platform source (modified) | `infrastructure/app.py`, `infrastructure/raad_platform/stacks.py`, `infrastructure/raad_platform/edge/handler.py`, `infrastructure/raad_platform/telemetry/handler.py` |
| Scripts (new) | `scripts/write_platform_config.py`, `scripts/platform_smoke.py`, `scripts/check_identity_capabilities.py` |
| Tests (new) | `test_identity_publisher.py`, `test_platform_contracts.py`, `test_platform_rate_store.py`, `test_platform_rate_limits.py`, `test_platform_config_writer.py`, `test_platform_mapping.py`, `test_platform_smoke.py`, `test_platform_capabilities.py`, `integration/test_platform_rate_limits.py` (all under `infrastructure/tests/`) |
| Tests (modified) | `conftest.py`, `test_identity_stack.py`, `test_monitoring_stack.py`, `test_public_edge_stack.py`, `test_edge_adapter.py`, `test_public_latency_processor.py`, `test_public_latency_stack.py` |
| Build and configuration | `infrastructure/pyproject.toml`, `infrastructure/uv.lock`, `infrastructure/docker-compose.yml`, `infrastructure/.env.example`, `infrastructure/README.md`, `.github/workflows/ci.yml`, `.gitignore` |

Existing tests changed only where behavior changed on purpose:

- the OAuth code-flow and 12-character-with-symbol assertions became native-flow and A4 assertions
- mocks of `_verify` now return a subject
- the HTTP API route count now includes the dev stub route
- alarm dimensions may include a platform `FunctionName`
- a failed collection also emits `PublicCollectionFailures`

`deploy-dev.yml`, the root `README.md`, `.mcp.json`, `scripts/run_mobile_dev.py`, `scripts/verify-dev.sh` and `.env.local` are unchanged. RaadMoneyService was read only.

Step 16 modified five paths that were already U4's: `infrastructure/raad_platform/stacks.py` (the COG1 reason text only), `scripts/check_identity_capabilities.py`, `infrastructure/tests/test_identity_stack.py`, `infrastructure/tests/test_platform_capabilities.py` and `infrastructure/README.md`. It created and deleted nothing, so the manifest's 39 paths are unchanged.

## Commands Run and Results

All commands ran from `infrastructure/`, synthetic values only, no AWS credentials. Coverage figures are coverage.py totals with `branch = true` (lines and branches combined).

| Command | Result |
|---|---|
| Baseline: the eight-file selection from the test instructions, with coverage | 145 passed; 86.09% |
| `uv run pytest tests/test_identity_stack.py --no-cov -q` (runner readiness, before new tests) | 7 passed |
| `uv run pytest --cov=raad_platform --cov=../scripts --cov-report=term-missing` (CI form) | Steps 1–15: 400 passed; 90.43%. **After Step 16: 420 passed; 90.90%**, floor 80% met (re-run on the unchanged tree first: 400 passed; 90.43%) |
| The complete sixteen-file U4 selection from `unit-test-instructions.md`, with coverage | **After Step 16: 420 passed; 90.90%** (run separately, not chained) |
| Step 16: `uv run pytest tests/test_platform_capabilities.py tests/test_identity_stack.py --no-cov -q` | 64 passed |
| `docker compose -f docker-compose.yml up -d --wait rate-dynamodb`, then `RAAD_RATE_DYNAMODB_ENDPOINT=http://127.0.0.1:8002 uv run pytest tests/integration/test_platform_rate_limits.py --no-cov -q` | Healthy; **8 passed**. Without the endpoint: 8 errors (fails, never skips). With a non-loopback endpoint: 8 errors. Default collection includes 0 integration tests. |
| Component commands from the test instructions (contracts; identity and publisher; rate store; edge; stacks; writer; alarms; mapping; tools) | 36; 54; 29; 51; 103 (with monitoring); 26; 85; 15; 48. All passed. |
| `uv run ruff check …` and `uv run ruff format --check …` (CI form and the instructions' explicit-file form) | All checks passed; 35 files formatted |
| `uv run mypy raad_platform app.py ../scripts` (and the explicit-file form) | No issues in 17 source files |
| `uv run pip-audit` | No known vulnerabilities |
| `cdk synth --all --output cdk.out/u4-dev`, `u4-stg`, `u4-prd` (the instructions' synthetic inputs; credential chain blanked; `AWS_REGION` and `AWS_DEFAULT_REGION` us-east-1; EC2 metadata disabled) | **Exit 0 in all three.** Real Docker linux/amd64 bundling. cdk-nag: **0 errors**, 2 warnings each (AwsSolutions-CFR1 geo restriction, AwsSolutions-COG2 MFA) |
| CI-form synth (external DNS, no zone) to `cdk.out/ci-dev` | Exit 0; same 2 warnings; 0 Route 53 records |
| Bundle inspection | Every function declares `x86_64` on python3.12. The edge bundle holds `raad_platform/edge/{handler,rate_store,stub}.py`. `_cffi_backend` and `cryptography` `_rust` are ELF x86-64. The edge, stub, rate store and publisher import inside `public.ecr.aws/sam/build-python3.12` (read-only, no network). |
| Logical IDs, compared with the Step 1 baseline (same stack IDs) | Every existing ID kept with the same type in dev, stg and prd, except the intentionally removed `UserPoolHostedUiDomain` and the hash-bearing `MoneyEdgeCurrentVersion…` |
| Gitleaks v8.24.2 (official image, no network, read-only, `--redact`), `git` mode with `.gitleaks.toml` and `.gitleaksignore` | 33 commits, about 44.55 MB: **no leaks** |
| Gitleaks v8.24.2 `dir` over a staged copy of the 39 U4 paths | **No leaks** |
| Step 16 re-run: ruff check, ruff format --check, strict mypy, pip-audit, the three synths, the integration file and Gitleaks `dir` over the five changed files | Ruff clean (after one fix to an unused return value in a new test); 35 files formatted; no mypy issues in 17 files; no known vulnerabilities; all three synths exit 0 with 0 nag errors and the same CFR1/COG2 warnings, and the new COG1 text is in the dev template; integration 8 passed; no leaks |
| Gitleaks v8.24.2 `dir` over the synthesized templates (generated output, classified separately) | 29 `generic-api-key` findings. Each was verified to be a CDK asset key (`S3Key`, `s3Key`, `objectKey`) holding a 64-hex content hash, not a credential. `cdk.out/` is gitignored. |
| grep of the U4 paths and templates for the real account IDs, hosted zone, certificate ID, domain and personal addresses | None found |

`docker compose stop rate-dynamodb` stopped only this unit's container; RaadMoneyService's DynamoDB Local was left running. The local CDK CLI is 2.1146.1 on Node v26.12.1, which jsii does not list as tested (its warning was silenced for the runs); CI uses Node 22.

## Test Coverage Summary

There are 255 new or extended unit cases plus 8 local-DynamoDB boundary cases, against the plan's estimate of 60–90, which was not a cap. Parametrized cases are counted individually.

| File | Cases |
|---|---|
| `test_platform_contracts.py` | 36 |
| `test_identity_publisher.py` | 24 |
| `test_platform_rate_store.py` | 29 |
| `test_platform_rate_limits.py` | 14 |
| `test_platform_config_writer.py` | 26 |
| `test_platform_mapping.py` | 15 |
| `test_platform_smoke.py` | 19 |
| `test_platform_capabilities.py` | 14 → 31 (Step 16 adds 17 burst cases) |
| `test_identity_stack.py` | 7 → 30 → 33 (Step 16 adds the COG1 reason check for three environments) |
| `test_monitoring_stack.py` | 9 → 17 |
| `test_public_edge_stack.py` | 25 → 56 |
| `test_edge_adapter.py` | 22 → 37 |
| `test_public_latency_processor.py` | 19 → 20 |

Coverage by module:

| Module | Coverage |
|---|---|
| `publisher.py` | 96% |
| `rate_store.py` | 98% |
| `configuration.py` | 90% |
| `stub.py` | 100% |
| `stacks.py` | 99% |
| `edge/handler.py` | 88% |
| `check_identity_capabilities.py` | 92% → 95% after Step 16 |
| `platform_smoke.py` | 86% (uncovered: the real TLS socket probe) |
| `write_platform_config.py` | 94% |

No coverage-ignore pragma was added, and no threshold was changed.

## Tests Written but Not Executed Here

- **GitHub Actions** (`ci.yml`, including Gitleaks, the integration step and the three-environment synth loop) was not run; only the equivalent local commands above were run. The first PR run is still owed.
- **Live tool runs.** `platform_smoke.py --execute`, `check_identity_capabilities.py --execute` and the C4/C5 writer against a real outputs file were not run, because there is no deployment and no AWS calls were authorized. Their offline tests use injected clients.

## Key Decisions and Deviations

1. **C5 correlation pattern.** The canonical pattern is `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`, the intersection of the design pattern and the one U2 accepts. A caller value outside it is replaced, so the edge never returns an ID that MoneyApi would change. This is documented in the C5 file and checked with a Hypothesis property test.
2. **Contract versions.** C3, C4 and C5 carry file version `1.0.0-rc.1`, matching C2's existing pre-release form. The data markers (`configVersion`) stay `1.0`, the shapes U2 and the mobile build already accept. C2 is unchanged; raising it to `1.0.0` and tagging any contract is a release step after this lands on `main`.
3. **COG1 nag exception.** cdk-nag's COG1 requires symbols in passwords, which would silently strengthen A4. COG1 therefore has a resource-specific exception with its reason, beside the COG8 (no paid Plus) exception the plan named. After Step 16 (R-01), COG1 relies on the approved A4 rule and native sign-in lockout; the regional WAF is unverified until dev P10 passes and is not cited as a control.
4. **Rate-key material.** Subject keys use a domain-separated HMAC derived from the existing correlation HMAC secret, which adds no new secret and no new cost. Rotation adds `previousVersion` and `previousKey` to that secret, and both keys are charged until the old one is removed. Remove the previous key at least one minute after the new one is active.
5. **PITR on the rate table.** It was added to follow the team's data-store practice and to avoid an unexplained DDB3 warning. The table holds a few KB, so the cost is negligible.
6. **Heartbeat schedule.** The collector now runs every minute, needed for the "absent 3 minutes" alarm. That adds about 43,800 small invocations and PutMetricData calls per environment per month, plus about 9 new alarms per environment. These costs are small but not zero, and they are not a spending approval.
7. **Edge handler path.** It moved to `raad_platform.edge.handler.entry`, with the package-layout bundle, so the rate-store module imports the same way in Lambda and in tests.
8. **Unknown routes.** Edge paths outside `/money/v1` now answer `404 NOT_FOUND` (C5 `no_matching_route`, outside C1), where they previously answered 500.
9. **Writer and CDK exports.** The writer ignores CDK's auto-generated `ExportsOutput…` cross-stack outputs, which would appear in any real outputs file, but still scans them for secret material.
10. **Stricter deployment inputs.** `RAAD_ENVIRONMENT` is now required, with no silent dev default. `CDK_DEFAULT_ACCOUNT` must be 12 digits, and the certificate must be in that account.
11. **Accepted deviations.** Native alarm recovery after one healthy evaluation was accepted in the handoff and is stated in every alarm description. The refresh lifetime is fixed at 30 days from sign-in; no 30-day idle guarantee is claimed, and the idle rule is U3's.
12. **Not changed.** `deploy-dev.yml` still passes the now-unused `RAAD_COGNITO_DOMAIN_PREFIX` variable, which is harmless. The plan's surface named only `ci.yml`, and the deploy workflow stays deliberately unable to authenticate. The deployment-pipeline stage should remove that line.

## Checks Still Open

None of these is claimed as passed.

- **C3 P1–P13 on a deployed dev**, especially P7 (the earlier code refused and the new code accepted after a resend, with the same acknowledgement for unknown and confirmed addresses). There is no invented pre-confirmation trigger. If native behavior fails, the gap goes back to the person and the co-engineer.
- **P10 is a dev gate (R-01).** Run `check_identity_capabilities.py --execute --burst` on dev, then record `secondCallerUnaffected` from a second caller. Dev is not called done, and stg is blocked, until P10 passes; a failed or pending P10 blocks release. The same run shows whether Cognito accepts the probe's `example.invalid` username; if it does not, the burst ends inconclusive after five requests (fails safe).
- **Regional WAF classification.** Beyond P10, confirm that GetUser is excluded, two-caller isolation behind shared egress, and how a provider refusal maps to the client. Associating a new ACL can fail with `WAFUnavailableEntityException` until the ACL propagates, which is a deploy-time risk.
- **COG8 still cites the WAF.** The COG8 (no paid Plus) reason still lists "the regional WAF on this pool" under its tested compensating controls, the same weakness R-01 found for COG1. Step 16 named only COG1, so COG8 was not changed; it needs the person's decision (reword it the same way, or accept it until P10 passes).
- **Native sign-in lockout** is documented provider behavior that COG1 now relies on; it has not been observed on a deployed pool.
- **Alarm delivery.** The email subscription confirmation and an actual stg breach and recovery notification.
- **Platform smoke on dev** (the smoke tool with `--execute`), including deployed TLS 1.0/1.1 refusal, direct-origin denial and the stub mapping.
- **C2 to U2 wallet creation** on dev (P12 plus U2's consumer).
- **Public p95 under load** (100 registered, about 10 active users) and complete observation reconciliation.
- **The coherent three-table restore drill** (U2's RPO/RTO).
- **cdk-nag warnings.** AwsSolutions-CFR1 (geo restriction) and AwsSolutions-COG2 (no MFA) are not suppressed and are reported here for a decision. MFA is not in C3.
- **C1 pin.** Contract design lists Raad as pinning C1 for the edge `Error` shape; no C1 pin was added (no C1 release tag exists yet).
- **CI enforcement of contract versions** (refusing a changed contract file with an already-tagged version) belongs to the CI Pipeline stage.
- **Deployment prerequisites.** GitHub OIDC role creation, deploy variables, cost authorization, and Lambda concurrency headroom for 20 + 2 + 2 + 2 reserved.

## Handoff for U2 and U3

- **U2 (RaadMoneyService), no change required.** It reads `/raad/<env>/event-bus/arn` and `/raad/<env>/alarm-topic/arn`, which now exist. The `/raad/<env>/verifier` shape is unchanged. The C2 pin stays valid. Its alarms can now publish to the topic. The edge forwards only correlation IDs that U2 keeps.
- **U3 (RaadMobile).** It receives `config/<env>.json` from `write_platform_config.py`, in the existing seven-key shape. C3 now holds the A4 examples, session policy and P1–P13 list. Rate refusals arrive as 429 `RATE_LIMITED` with Retry-After.
- **Deployment order**, after separate cost authorization: the completed platform first, then U2 directly. Do not deploy U1 MoneyService first or run the historical U1 index migrations on a fresh environment. Changing `UsernameConfiguration` and attribute mutability replaces any existing user pool; per the handoff, none has been deployed.
