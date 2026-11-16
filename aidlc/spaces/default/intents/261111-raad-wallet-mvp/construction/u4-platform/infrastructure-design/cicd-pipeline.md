# cicd pipeline — u4-platform

Conversation language: English.

## Pipeline Flow

1. Independent Raad PR checks use pinned Python3.12/uv.lock/CDK. Ruff format/lint, strict mypy and >=80% repository line coverage include host scripts and scripts/** workflow triggers. C2–C5 schemas/provider tests/pins, audit, secret scan, actual Docker bundling/CDK synth/AwsSolutions checks all block on failure. Assertions do not replace packaging.
2. Other engineer approval and squash merge to protected main; record immutable asset digest/SHA and versioned contract tags. Never move a released tag. PR validation receives no deployment credentials.
3. Before upload/deploy, require explicit cost authorization, real hostname/certificate, matching account/environment/role, quotas and applicable C3 capability clearance. Current no-cost instruction stops before asset upload or resource creation. Do not reuse an unrelated role or deploy as root.
4. Platform foundation first: identity/configuration/origin roles/bus/monitoring/custom certificate. Service deploys through its own pipeline; platform integration binds actual service URL through SSM last. No circular CloudFormation exports. Incomplete routes fail closed.
5. Real dev smoke verifies SDK sign-in/profile, public wallet/transfer/history, forged origin header and direct-origin refusal, C2/C5 and matching environment outputs. scripts/verify-dev.sh requires actual C4, runtime fixture secret references and both device IDs; API/iOS/Android use separate fixture pairs and record SHAs. Complete DNS/TLS, public load, P1–P13 and mixed GetUser/account-burst isolation before claiming full identity release.
6. Promote identical application bytes using environment-specific assemblies dev->stg after smoke. Stg requires contract/load/alarm breach and recovery email/timed restore evidence. Prd is a protected manual approval after green stg, followed by safe smoke. No activity or incomplete metrics is not passing evidence.

| Stage | Gate |
|---|---|
| PR | Second engineer; full local/CI parity including bundle/nag/contracts/security |
| Upload/deploy | Explicit cost authorization and actual hostname/certificate/non-root role |
| Full identity | P7 earlier-code rejection plus all capability checks; no invented trigger |
| Stg | Dev smoke, mixed provider load, origin/TLS and coherent three-table recovery/alarms |
| Prd | Named human approval after stg; same bytes; post-deploy smoke |
| New service | Dev stub path responds without MoneyService/C1 changes or bypass |

## Deployment and Rollback

Publish immutable Lambda versions/aliases. Check candidate before traffic, then all-at-once dev/stg; proposed production10%/10min canary requires adequate measured healthy samples. Insufficient metrics cannot automatically promote. Keep a compatible last-known-good alias/artifact; failed smoke stops promotion and rolls back compatible code. Use additive expand/contract data changes; no blind logical-ID rename/table replacement.

Rotate origin credentials by preparing acceptance in edge, updating both CloudFront origins, waiting for deployed distribution, proving direct-origin refusal, then retiring the old secret. Retain correlation versions for log lifetime. No automatic rotation claim.

## Credentials and Evidence

GitHub OIDC uses audience sts.amazonaws.com and exact00az/Raad protected-environment subject, short-lived role per environment, scoped stack/assets/pass-role permissions. Human deployment identity must be non-root. No static AWS keys, provider API keys or private fixtures in logs/arguments/artifacts. DNS automation requires user-controlled credentials through protected local/runtime configuration; never request a credential pasted into chat. Known public and operational email addresses are configuration, not credentials.

## Sources

U4 specification, monitoring and six NFR designs; C2–C5; team practices; current workflows. These are proposed pipeline requirements, not successful CI/deployment evidence.
