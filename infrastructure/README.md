# RAAD platform infrastructure

The shared platform every RAAD service relies on, one set of stacks per environment
(`dev`, `stg`, `prd`) in `us-east-1`:

- `RaadMonitoring-<env>`: the `raad-<env>-alerts` topic, dashboard, alarms and public-latency
  telemetry.
- `RaadIdentity-<env>`: the Cognito user pool and public app client (native SDK sign-in with SRP;
  no hosted UI or OAuth), the C2 event bus and its sign-up confirmation publisher, the regional
  WAF on the pool, and the correlation HMAC secret.
- `RaadPublicEdge-<env>`: CloudFront with the custom certificate and TLS 1.2 minimum, its WAF,
  the HTTP API and the edge adapter that verifies the origin and the access token, applies the
  verified-caller rate limits and forwards to MoneyApi, plus a dev-only stub mapping.

## Prerequisites

- `uv` (installs the pinned Python 3.12 and the locked dependencies)
- Node.js 22 and the AWS CDK CLI (`npm install --global aws-cdk`)
- Docker, for Lambda asset bundling during `cdk synth` and the local DynamoDB rate-store tests

## Setup and test

```sh
uv sync --locked --all-groups
uv run pytest
```

The local rate-store boundary runs against a loopback DynamoDB Local container:

```sh
docker compose -f docker-compose.yml up -d --wait rate-dynamodb
RAAD_RATE_DYNAMODB_ENDPOINT=http://127.0.0.1:8002 uv run pytest tests/integration/test_platform_rate_limits.py --no-cov -q
docker compose -f docker-compose.yml stop rate-dynamodb
```

## Local configuration

Copy `.env.example` to `.env.local` (gitignored) and fill it from protected deployment
configuration. Supply the environment's host and its existing us-east-1 ACM certificate together;
the certificate must belong to `CDK_DEFAULT_ACCOUNT`. The hosted-zone ID is optional and must name
an existing Route 53 zone; without it, point external DNS at the distribution. No hosted zone,
domain or certificate is ever created here. The alert address appears only in that local file and
in protected CI configuration, never in source. Set `RAAD_EXPECTED_ACCOUNT` to make synthesis
refuse any other account.

`read_deployment_inputs` validates the environment, account, region, host, certificate, zone and
alert input before any stack is built, and its errors name the input, never its value. The default
`cloudfront.net` certificate cannot enforce TLS 1.2 and is refused.

## Sign-in (C3)

Sign-in uses the native Cognito SDK flow: SRP for the app, refresh tokens, and the IAM-only admin
password flow reserved for controlled test-fixture setup. Email sign-in is case-insensitive, only
email and name are stored (both required and immutable), the password rule is exactly A4 (8+
characters with lower, upper and digit; no symbol requirement), refusals do not reveal whether an
account exists, access tokens last 60 minutes and refresh tokens a fixed 30 days from sign-in.
The 30-day idle rule is the mobile app's (C3 check P9), not a provider guarantee. Paid Cognito
Plus is not used in any environment.

## Shared outputs

The SSM parameters other units read are listed in `../contracts/README.md`. To produce the C4
mobile configuration and the C5 verifier file for one environment from `cdk deploy
--outputs-file` output, without calling AWS:

```sh
uv run python ../scripts/write_platform_config.py --environment dev --account <account-id> \
  --outputs <outputs.json> --output-dir <directory>
```

## Platform checks against a deployed environment

`../scripts/platform_smoke.py` and `../scripts/check_identity_capabilities.py` check one deployed
environment and refuse to act unless `--execute` is given and the caller's account and the outputs
match the expected account and environment. They print check names and outcomes only. Live checks
they cannot prove (for example C3 P7 code replacement) stay pending and fail the run until evidence
is recorded.

### Dev gate: C3 P10 (regional WAF on the user pool)

The regional WAF rules match the `x-amzn-cognito-operation-name` header, whose real value has not
been observed. Every local test is a synth-time assertion, so until a real burst is refused the WAF
is an unverified control, and the AwsSolutions-COG1 exception does not rely on it.

**Dev is not done until P10 passes, and a failed or pending P10 blocks release to `stg`.**

1. Wait at least five minutes with no other Cognito traffic from the address you run from, because
   earlier requests still count in the WAF's window.
2. Run the burst against dev only. The tool refuses `prd`, and it refuses any account, environment
   or outputs mismatch before sending a request:

   ```sh
   uv run python ../scripts/check_identity_capabilities.py --environment dev \
     --expected-account <account-id> --outputs <outputs.json> --evidence <evidence.json> \
     --execute --burst
   ```

   From this one address it sends unauthenticated `InitiateAuth` (`USER_SRP_AUTH`) requests for a
   random, unregistered address, about one every 1.2 seconds and all within one 5-minute window.
   It stops at the first WAF refusal, which the SDK reports as `ForbiddenException`. The budget is
   200 admitted requests: twice the 100-per-address account limit and under the 300 general limit,
   so only the account-operation rule can refuse it. No account, code or email results. The tool
   records `operationClassificationObserved` and `burstRefusedForOneCaller` as true on a refusal,
   or false when the budget is spent without one. Throttling, network and other provider errors
   count as neither. Five of them, or pacing that slips out of the window, makes the run
   inconclusive and leaves both fields pending. The output holds counts and outcomes only.
3. While the first address is still refused, sign in from a second address (for example a phone on
   mobile data). Record `secondCallerUnaffected` in the evidence file as `true` only if that sign-in
   works. The tool never decides this field.

## Security exceptions

cdk-nag's AwsSolutions checks run on every synth. Each exception is resource-specific with its
reason beside it in `raad_platform/stacks.py`: the tested Python 3.12 runtime pin, coordinated
protocol-secret rotation, paid Plus not approved (all environments, with the retained risk
stated), the A4 password rule (compensated by the approved A4 rule and Cognito's native sign-in
lockout, not by the regional WAF until the dev P10 gate passes), API-limited IAM wildcards, edge
authentication in the adapter, privacy-safe CloudFront logging and the dev-only stub route. No rule
is disabled and TLS is never excepted.

## Deployment

Nothing in this repository deploys by itself, and no deployment is authorized by these
instructions. A deployment needs separate cost approval, the real host and certificate, a non-root
identity and the matching account. Deploy this platform first in an environment, then the money
service. The CI deploy role (GitHub OIDC scoped to `00az/Raad` and the environment) does not exist
yet; the deploy workflow therefore cannot authenticate, by design.
