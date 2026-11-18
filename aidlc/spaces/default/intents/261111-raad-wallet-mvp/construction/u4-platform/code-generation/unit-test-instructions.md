# Unit Test Instructions — u4-platform

Conversation language: English.

## Framework Setup and Ordering

Run commands below from `infrastructure/` in this Raad checkout unless a row explicitly names another directory. Use pinned Python 3.12 and `uv.lock`; keep pytest, pytest-cov, Hypothesis, Ruff, strict mypy, pip-audit and real CDK Docker bundling. Step 2 adds only the schema-validation/test dependencies needed by this unit, through the dependency manager with the lockfile committed.

The plan's complete tool-rendered Testing Contract is authoritative. It is mixed/custom: only the money core in RaadMoneyService is TDD. U4 implements each platform layer and then writes/runs that layer's tests. Do not manufacture Red/Green evidence for platform work. No money-service source is changed.

Runner readiness, runnable before new files exist:

```sh
uv run pytest tests/test_identity_stack.py --no-cov -q
```

Run the unchanged-tree baseline before changing implementation:

```sh
uv run pytest tests/test_identity_stack.py tests/test_monitoring_stack.py tests/test_public_edge_stack.py tests/test_edge_adapter.py tests/test_public_latency_stack.py tests/test_public_latency_processor.py tests/test_public_latency_driver.py tests/test_mobile_dev_runner.py --cov=raad_platform --cov=../scripts --cov-report=term-missing
```

Do not chain a later command behind a coverage command's exit status. Record tests and threshold results separately.

## Component Tests

Each command is scoped to exact U4 platform test files. New files become runnable as their implementation step lands. Keep existing tests; add approximately 5–8 cases per new component, with extra cases wherever the required boundary/concurrency matrix needs them. Estimate 60–90 new cases across the unit, not a cap.

| Area | Exact command, from infrastructure/ | Required coverage |
|---|---|---|
| Canonical contracts | `uv run pytest tests/test_platform_contracts.py --no-cov -q` | C2 routing/schema, exact emitted fields, C3 settings, C4/C5 schemas and environment binding, unknown/missing fields and compatible existing consumer shape |
| Identity and event publisher | `uv run pytest tests/test_identity_stack.py tests/test_identity_publisher.py --no-cov -q` | A4 sample passwords, SRP/public client, no hosted UI requirement, case-insensitivity, privacy attributes, session lengths, generic refusal support; signup-only trigger, no reset event, publish/partial failure never fails confirmation, no sensitive logs |
| Counter storage | `uv run pytest tests/test_platform_rate_store.py --no-cov -q` | Conditional/transaction wire requests, server-minute boundary, no reliance on TTL deletion, atomic send-plus-lookup, transient failure, caller/environment isolation and active-window key stability |
| Edge integration | `uv run pytest tests/test_platform_rate_limits.py tests/test_edge_adapter.py --no-cov -q` | Lookup 30/min, send 10/min sharing lookup budget, other reads/setup/history 60/min; no U2 call on quota/counter failure, 429/503 and Retry-After, verified caller only, original bearer/SigV4, flat C1 errors, forwarding/correlation/unknown routes |
| Stack/output/environment protection | `uv run pytest tests/test_public_edge_stack.py tests/test_identity_stack.py tests/test_monitoring_stack.py --no-cov -q` | SSM bus/topic and existing consumer outputs, publisher-only bus permissions, WAF regional association and GetUser exclusions, dev/stg/prd isolation, retention, stable logical IDs, optional existing-zone aliases, explicit viewer TLS 1.2, no paid Plus, scoped IAM/nag exceptions |
| Configuration writer | `uv run pytest tests/test_platform_config_writer.py --no-cov -q` | Exactly seven C4 keys, correct native verifier configuration, coherent deployment-output binding, missing/extra/secret-looking/cross-environment rejection, safe file destination, no AWS call in offline mode |
| Alarms/public observations | `uv run pytest tests/test_monitoring_stack.py tests/test_public_latency_stack.py tests/test_public_latency_processor.py tests/test_public_latency_driver.py --no-cov -q` | Defined thresholds/two breach windows/sample gates, heartbeat, native recovery deviation, insufficient/unknown coverage, idempotent windows, deduplication/conflicting/late/missing samples, safe seven fields and UTC |
| Extension mapping | `uv run pytest tests/test_platform_mapping.py --no-cov -q` | Dev-only stub, no stg/prd route, no MoneyService/C1 edits, original money mapping unchanged, direct-origin refusal, unknown paths fail closed |
| Smoke/capability tools | `uv run pytest tests/test_platform_smoke.py tests/test_platform_capabilities.py tests/test_mobile_dev_runner.py --no-cov -q` | Injected dependencies/clock; wrong account/environment/config rejected before action; incomplete evidence fails; code/token/profile values never logged; real execution requires explicit opt-in; no fake P7 pass |

## Real Local DynamoDB Boundary

The test fixture is a local container, not AWS and not an in-memory substitute. Step 2 supplies `infrastructure/docker-compose.yml` with a named `rate-dynamodb` service pinned to the supported local image, bound only to `127.0.0.1:8002`. Check that the port is free; do not stop another project's container. Integration tests use isolated per-run tables and remove only those test tables in cleanup. They never use normal AWS credential discovery or a non-local endpoint.

Start the named local service:

```sh
docker compose -f docker-compose.yml up -d rate-dynamodb
```

Run the exact boundary file:

```sh
RAAD_RATE_DYNAMODB_ENDPOINT=http://127.0.0.1:8002 uv run pytest tests/integration/test_platform_rate_limits.py --no-cov -q
```

Require concurrent admissions to stop exactly at the limit; lookup and send consumption is all-or-nothing; a denied combined send consumes neither counter. Cover competing callers, environment isolation and stale TTL items. Missing local-store prerequisites are reported unavailable, not replaced with mocks or claimed passing. CI starts this service and runs the same command without silently skipping it.

Stop only this unit's named service when finished:

```sh
docker compose -f docker-compose.yml stop rate-dynamodb
```

## Unit Coverage and Repository Floor

Run the complete named U4 platform selection after all files exist:

```sh
uv run pytest tests/test_identity_stack.py tests/test_monitoring_stack.py tests/test_public_edge_stack.py tests/test_edge_adapter.py tests/test_public_latency_stack.py tests/test_public_latency_processor.py tests/test_public_latency_driver.py tests/test_mobile_dev_runner.py tests/test_identity_publisher.py tests/test_platform_rate_limits.py tests/test_platform_rate_store.py tests/test_platform_contracts.py tests/test_platform_config_writer.py tests/test_platform_smoke.py tests/test_platform_capabilities.py tests/test_platform_mapping.py --cov=raad_platform --cov=../scripts --cov-report=term-missing
```

The platform repository floor remains **80% line coverage**, including applicable host scripts, and coverage on main must not decrease. Build and Test also checks it on the full assembled repository suite. A unit selection can pass every test while failing only the whole-repository threshold; record both facts and do not lower the threshold or omit uncovered source. There is no separate 95% money-core target for U4; that remains U2's requirement. No coverage-ignore pragmas are planned.

## Static and Packaging Checks

After implementation, use the existing platform source paths and explicitly named new scripts:

```sh
uv run ruff check raad_platform tests app.py ../scripts/write_platform_config.py ../scripts/platform_smoke.py ../scripts/check_identity_capabilities.py ../scripts/run_mobile_dev.py
```

```sh
uv run ruff format --check raad_platform tests app.py ../scripts/write_platform_config.py ../scripts/platform_smoke.py ../scripts/check_identity_capabilities.py ../scripts/run_mobile_dev.py
```

```sh
uv run mypy raad_platform app.py ../scripts/write_platform_config.py ../scripts/platform_smoke.py ../scripts/check_identity_capabilities.py ../scripts/run_mobile_dev.py
```

```sh
uv run pip-audit
```

Actual synth/nag uses production asset bundling, separately from assertion tests' inline asset fixture. Keep Linux amd64 packages and X86_64 Lambda declarations aligned; inspect native bundled assets after synthesis. These commands use only synthetic fixture values, do not source `.env.local`, and do not authorize lookup, asset upload, `cdk diff` against AWS, bootstrap or deploy. Use an isolated generated assembly for each environment. The example alert value below is synthetic test data, not the configured operational destination.

```sh
RAAD_ENVIRONMENT=dev CDK_DEFAULT_ACCOUNT=111111111111 CDK_DEFAULT_REGION=us-east-1 RAAD_DOMAIN_NAME=dev.api.example.test RAAD_HOSTED_ZONE_ID=Z0123456789 RAAD_CERTIFICATE_ARN=arn:aws:acm:us-east-1:111111111111:certificate/00000000-0000-0000-0000-000000000000 RAAD_ALERT_EMAIL=build@example.test uv run cdk synth --all --output cdk.out/u4-dev
```

```sh
RAAD_ENVIRONMENT=stg CDK_DEFAULT_ACCOUNT=111111111111 CDK_DEFAULT_REGION=us-east-1 RAAD_DOMAIN_NAME=stg.api.example.test RAAD_HOSTED_ZONE_ID=Z0123456789 RAAD_CERTIFICATE_ARN=arn:aws:acm:us-east-1:111111111111:certificate/00000000-0000-0000-0000-000000000000 RAAD_ALERT_EMAIL=build@example.test uv run cdk synth --all --output cdk.out/u4-stg
```

```sh
RAAD_ENVIRONMENT=prd CDK_DEFAULT_ACCOUNT=111111111111 CDK_DEFAULT_REGION=us-east-1 RAAD_DOMAIN_NAME=api.example.test RAAD_HOSTED_ZONE_ID=Z0123456789 RAAD_CERTIFICATE_ARN=arn:aws:acm:us-east-1:111111111111:certificate/00000000-0000-0000-0000-000000000000 RAAD_ALERT_EMAIL=build@example.test uv run cdk synth --all --output cdk.out/u4-prd
```

Retain scoped security exceptions with reasons and report all findings. Do not suppress TLS/origin/unknown IAM findings to complete a synth. Dependency and secret scans remain enabled in CI. Review every source-history finding with fully redacted reports, retaining only narrowly justified prose/fixture exceptions; generated third-party output findings are classified separately, not called a clean scan.

## Fixtures and Privacy

- Use contract-derived payload builders, local signing keys, injected boto3 clients/Stubber, mocked HTTP/clock and generated opaque subject/event IDs. No AWS reads in unit/assertion/config-writer tests.
- Publisher assertions validate against C2 and separately require exactly declared emitted fields. Preserve every unknown incoming Cognito-event field when returning the original event.
- Validate actual SDK request/response shapes; tests must distinguish thrown PutEvents failure from per-entry failure.
- Capture logs with recognizable synthetic tokens/codes/profiles and assert absence; never print actual credential/configuration values.
- No actual alarm address, password, access/refresh token, confirmation code, raw trigger, request body/query or profile goes into evidence. Runtime configuration is not copied into these instructions.

## Live Checks — Explicitly Not Run Here

Actual P1–P13, especially P7 old-code rejection/new-code success, Cognito/WAF operation isolation, real C2-to-U2 wallet creation, deployed TLS/origin denial, smoke journeys, alarm subscription/delivery, latency/demo load and restore drills remain **pending**. Tests of the tools do not satisfy those checks. The fixed native refresh lifetime does not prove the U3 idle fallback. Native alarms' one-healthy-evaluation recovery is an accepted deviation from the earlier three-window design; retain this in U4's results and release checklist.

Do not use current login credentials to run these procedures or repair GitHub deployment credentials. Any deployment needs Ziyad's separate cost go-ahead. Fresh dev order is completed platform then U2 directly, without the historical U1 table migration. Record unavailable evidence and hand off exact outputs/contracts to the co-engineer rather than declaring integration complete.
