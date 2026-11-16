# cicd pipeline — u2-money-service

Conversation language: English.

## Pipeline Flow

1. PR checks: Python3.12/uv.lock, Ruff format/lint, strict mypy, pytest/Hypothesis and real DynamoDB Local tests. Enforce>=80% repo line coverage and>=95% money-core line AND branch; TDD in the money core. Audit/secret scan, C1/C2/C5 pin/provider compatibility checks, actual bundle/synth/cdk-nag. Other engineer approval, squash merge, no direct main.
2. Record immutable application asset/digest/SHA; environment-specific assemblies reference identical bytes. OIDC short-lived roles bound to repo/environment, no root/static keys. Validate real inputs and cost authorization before asset publication or resource creation; current no-cost instruction stops deployment.
3. After authorization: platform foundation, service-owned tables/compute/queues/configuration, then platform route binding. Direct origin stays refused. Dev smoke uses actual provider/public API/store with independent initialized fixtures. Never resend an uncertain transfer with a new key.
4. Stg checks C1 replay/refusal/concurrency/ordinal paging/profile versions, C2 delivery and processing DLQs, wrong environment/verifier/origin, complete public load, actual alarms and timed coherent three-table restore.
5. Prd protected environment requires named human approval after green stg; same bytes, designated simulated test fixtures and post-deploy smoke. New wallets receive100000halalas once; existing wallets never receive another opening credit.

| Stage | Gate |
|---|---|
| PR | Full local/CI parity; second engineer; coverage/security/contracts/bundling |
| Deploy | Explicit cost authorization and actual non-root role/outputs |
| Dev->stg | Real smoke with SHA/digest and separate fake/live labels |
| Stg->prd | Load/security/alarm/recovery evidence plus human approval |
| Post-deploy | Smoke passes; failure stops promotion |

## Deployment and Rollback

Publish versions/alias, pre-traffic candidate check, all-at-once dev/stg. Proposed production10%/10min canary requires adequate measured healthy samples; low traffic cannot automatically pass. Retain compatible previous version; failed smoke rolls alias back and stops promotion.

Additive GSIs/profile versions/outcomes/ordinals require quiesced migration with balances/counts verified. After cutover do not reactivate a legacy writer lacking the canonical/U2 layout. Data recovery restores all three tables and reconciles invariants under RPO/RTO; code rollback is not a data restore.

## Secrets and Evidence

Runtime-fetch fixture/cursor/correlation credentials by ARN; no passwords/bodies in CLI, logs or artifacts. Deploy role scoped to stacks/assets/required pass-roles, source-bound service permissions. Evidence records commit/digest/pins/environment and API/iOS/Android, fake/live separately. No live result claimed.

## Sources

U2 infrastructure and monitoring, six NFR designs, Functional Design; C1/C2/C5; team practices.
