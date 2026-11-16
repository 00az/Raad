# CI/CD Pipeline — U2 Money Service

Conversation language: English.

## Pipeline Flow

1. **Pull request checks:** install from committed `uv.lock`; run Ruff format/lint, strict mypy, pytest and Hypothesis; run local-container integration/concurrency tests; enforce the repository's 80% line-coverage floor and the money-core 95% line and branch floors; run `pip-audit`; synthesize the CDK app, run CDK assertions and `cdk-nag` AwsSolutions checks. Any failure blocks merge. Validate OpenAPI and C1/C2 contract tests against the published contract.
2. **Merge to `main`:** build the immutable application artifact once, record commit SHA and artifact digest, and use GitHub Actions OIDC to assume a short-lived role scoped to `00az/RaadMoneyService` and the `dev` environment. Do not store AWS access keys in GitHub secrets.
3. **Deploy to `dev`:** deploy service-owned CDK stacks (Lambda, Function URL permissions, Ledger and WalletDirectory tables, C2 consumer target/DLQ, parameters/secrets references, alarms/dashboard). U4 platform resources must already exist. Run the service smoke test with designated test identities and simulated SAR; cover wallet, balance, transfer and history. Never use real payment rails.
4. **Promote to `stg`:** after the `dev` smoke test passes, promote the same artifact digest and commit to `stg`, with environment-specific configuration and data stores. Run contract, smoke, load (10 concurrent users), alert-channel and recovery/PITR exercise checks. Deployment failures stop promotion.
5. **Promote to `prd`:** require a named human approval in the protected GitHub environment after green `stg` checks. Deploy the same artifact digest with production configuration; run production-safe smoke checks using designated test identities. The production release is complete only when smoke checks pass.

| Stage | Gate |
|---|---|
| Pull request | All formatting, types, security, coverage, unit/integration, CDK synth and contract checks pass; other engineer approves |
| `dev` deploy | OIDC role and U4 shared dependencies available; post-deploy smoke passes |
| `stg` promotion | Same artifact as `dev`; smoke, load, alert and recovery checks pass |
| `prd` promotion | Human approval after successful `stg`; production smoke passes |

## Deployment and Rollback

Use a rolling Lambda alias/version deployment with a pre-traffic smoke check; no blue/green data-store replacement is implied. A failed deployment or smoke check stops promotion and shifts the alias back to the last known-good Lambda version. Roll back by redeploying the previous known-good commit through the pipeline. DynamoDB schema changes are additive: expand first and contract in a later release. Never roll back through destructive table replacement. For data corruption, restore both persistent tables to the same PITR point, validate ledger/holder invariants, and switch configuration only under the documented recovery procedure; the timed exercise must meet RPO ≤5 minutes and RTO ≤3 hours.

## Environment and Secret Handling

Maintain separate GitHub protected environments (`dev`, `stg`, `prd`) and environment-scoped OIDC role assumptions. Roles are least privilege and trust only this repository and its named environment/ref. Provision the new MoneyService role; do not reuse the unrelated existing role. Keep C5 issuer/audience/JWKS profile in SSM Parameter Store as non-secret configuration. Store correlation signing material in Secrets Manager and pass only its ARN. Never print values to CI logs. Deploy prerequisites supplied by U4 include edge role ARN, event bus target identity, and environment verifier configuration. Alarm email, public domain and certificate remain explicit account-owner inputs; the pipeline must fail deployment configuration validation if required values are missing rather than inventing them.

## Operational Constraints

The service pipeline deploys only service-owned resources. The `Raad` platform pipeline must first provide the shared sign-in, edge, domain/certificate, firewall/rate limits and event bus in each environment. The service's C2 consumer contract tests and C1 OpenAPI compatibility tests run in CI; cross-repository integration remains an environment smoke responsibility. AWS account root credentials are not used for deployment.

## Sources

This pipeline implements deployment and recovery choices in `reliability-design.md`, `security-design.md`, `scalability-design.md`, `performance-design.md` and `observability-design.md`; it deploys the components in `logical-components.md` and `components.md`, follows `functional-spec.md` for smoke behavior, and validates the C1/C2/C5 boundaries in `contract-summary.md`.
