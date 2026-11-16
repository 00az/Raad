# Infrastructure Specification — U2 Money Service

Conversation language: English.

## Deployment

| Facet | Choice | Rationale |
|---|---|---|
| Compute model | AWS Lambda, Python 3.12, stateless; API handler timeout 7 seconds; reserve concurrency 20 in `dev`, set `stg`/`prd` limits from measured load and account quota | Meets the 10-concurrent-user target while bounding store pressure; dependency calls have 1-second timeouts. |
| Networking topology | No service VPC for MVP. IAM-authenticated Function URL is callable only by the environment's shared edge role; public routing, TLS, WAF/rate limits and DNS belong to U4/platform | Avoids NAT cost and keeps the Function URL out of the public client path. |
| Storage strategy | Two environment-isolated DynamoDB on-demand tables: Ledger and WalletDirectory; AWS-managed encryption at rest; PITR enabled in `stg`/`prd`, disabled for disposable `dev`; retain persistent data and deletion protection in `stg`/`prd` | Supports conditional/transactional money writes, environment separation and approved recovery objectives. |
| Environments | `dev`, `stg`, `prd` in AWS account `027863026273`, `us-east-1`; separate stacks, tables, parameters, secrets, event targets and roles per environment | Matches team practice and prevents cross-environment data/config fallback. No production deployment until CI and staging smoke checks pass. |
| IaC approach | Python AWS CDK v2 in `RaadMoneyService`; synth and `cdk-nag` AwsSolutions checks in CI; all changes through reviewed pull requests | Service owns its compute and data resources; no manual console changes. |
| Resource sizing | DynamoDB on-demand; Lambda 7-second timeout; `dev` reserved concurrency 20. Set other concurrency caps using load evidence; no provisioned capacity, cache, read replica or multi-region replication at MVP | Expected scale is 100 total users / about 10 concurrent; scale only after load test and quota review. |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---|---|---|---|
| AWS Lambda | Compute | MoneyApi; Python 3.12; per-environment configuration; 7-second timeout; bounded concurrency | Stateless handler; only the shared edge role may invoke the Function URL. |
| Lambda Function URL | Load-balancer / ingress | `AWS_IAM`; edge role is the only granted invoker; SigV4; CORS disabled | U4 owns public edge/domain/TLS/firewall/rate limits. Function URL is not a mobile endpoint. |
| Amazon DynamoDB Ledger | Database | On-demand; environment-specific; encryption at rest; PITR in `stg`/`prd`; retain and deletion protection outside `dev` | Holds wallet balances, transfer records, idempotency outcomes, event receipts and history access items. Transactions enforce all-or-nothing updates. |
| Amazon DynamoDB WalletDirectory | Database | On-demand; environment-specific; encryption at rest; PITR in `stg`/`prd`; retain and deletion protection outside `dev` | Holds normalized unique email ownership and display names, keeping personal data outside ledger rows. |
| Amazon EventBridge target + SQS DLQ | Queue | U4 owns the event bus; U2 owns its per-environment consumer target/retry policy and DLQ. Set maximum event age to 86,400 seconds and maximum retries to 185; alarm on DLQ delivery | Provides bounded C2 retries up to 24 hours, then durable failure handling. Confirm the bus/target integration with U4 contract tests. |
| AWS Systems Manager Parameter Store | Configuration | Per-environment non-secret C5 issuer, audience, JWKS/verifier profile and parameter name | Missing or invalid profile fails closed. Cache only public verification keys under their expiry/refresh policy. |
| AWS Secrets Manager | Secret storage | Per-environment correlation-signing secret; Lambda gets only `GetSecretValue` for its secret | Secret ARN is supplied at deployment; no secret material in source or logs. |
| Amazon CloudWatch | Monitoring | Structured logs, custom low-cardinality metrics, per-environment dashboard and alarms; shorter `dev` log retention and retention to be set for `stg`/`prd` | Notification email is a required deployment input; no address is configured until supplied by account owner. |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Public API edge, API domain/certificate, WAF/rate limits and `/money` route | U4 platform | U2 service, U3 mobile | Edge invokes the per-environment IAM-protected Function URL using its dedicated role. U2 does not create duplicate public ingress. |
| Shared sign-in pool, C5 issuer/audience/JWKS publication | U4 platform | U2 service, U3 mobile | U2 reads only its environment's non-secret verifier profile and independently validates each caller. |
| Shared account-confirmed event bus | U4 platform | U2 service | U2 consumes the contracted event in its environment; U2 owns its target, retry and DLQ resources. |

## Account and Provisioning Inputs

Read-only account inspection on 2026-11-13 confirmed account `027863026273` and region `us-east-1`. No RAAD domain/hosted zone, ACM certificate, MoneyService deploy role or monitoring email was present. The unrelated existing GitHub Actions role is not reused. Before deployment, provision a least-privilege GitHub OIDC role restricted to repository `00az/RaadMoneyService` and the approved environment; supply each environment's edge role ARN, C5 issuer/audience/JWKS values, correlation secret ARN, event bus/target identity and alarm email through secure environment configuration. No AWS resources are deployed by this design.

The current API's C1 contract describes bearer-token calls through the shared public edge; the internal Function URL uses SigV4/IAM between edge and service. Account/host values shown as examples in the contract are placeholders until U4 supplies the real domain.

## Cost Notes

Use on-demand DynamoDB and Lambda pay-per-use for the low, currently unquantified MVP volume. Main cost drivers are Lambda duration/invocations, DynamoDB reads/writes and PITR storage in persistent environments, CloudWatch log ingestion/retention, EventBridge events and SQS DLQ retention. No reliable total can be calculated until request volume, item sizes, log volume and retention are agreed; calculate each environment in AWS Pricing Calculator before production provisioning. No monthly budget ceiling has been provided.

## Sources

This specification implements `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md`, `observability-design.md` and `logical-components.md` for this Unit. It follows the MoneyApi, Ledger and WalletDirectory boundaries in `components.md`, the wallet, transfer and event behavior in `functional-spec.md`, and the C1/C2/C5 ownership in `contract-summary.md`.
