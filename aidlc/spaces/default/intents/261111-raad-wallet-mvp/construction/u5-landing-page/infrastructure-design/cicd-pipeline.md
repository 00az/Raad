# cicd pipeline — u5-landing-page

Conversation language: English.

## Pipeline Flow

1. PR checks static HTML/CSS, links, both language documents, approved public email, no fabricated distribution links, no auth/money network integration, semantic accessibility and safe headers. CDK assertions, real synth and cdk-nag validate private S3/OAC/TLS/privacy. No executable coverage floor for static HTML/CSS. Other engineer approves; squash merge to main.
2. Build one immutable static artifact/digest. After explicit cost clearance and real hostname/certificate/account readiness, assume repo/environment-scoped GitHub OIDC role and deploy only RaadWeb resources. No deploy credential for PR jobs.
3. Publish versioned assets then language HTML, invalidate/revalidate HTML and fetch both actual HTTPS paths/assets. Smoke fails on missing content, wrong contact or unavailable page; no empty success.
4. Promote identical static artifact from dev to stg after smoke; prd protected environment requires human approval after stg. Browser/manual ar/en accessibility and native wording review remain release requirements.

| Stage | Gate |
|---|---|
| PR | Static checks, synth/nag, second engineer |
| Dev | Cost/host/certificate readiness; actual both-language smoke |
| Stg | Same artifact; smoke plus browser/manual evidence |
| Prd | Human approval after green stg; post-deploy smoke |

## Rollback and Secrets

Redeploy last-known-good artifact and rerun both-language smoke; do not change money resources. OIDC roles scope bucket/distribution/config actions to this repo/environment; S3 read policy uses OAC and exact distribution/account. No credentials, visitor data or wallet data in artifacts. No purchase, deployment or external message is performed by this design.

## Sources

U5 infrastructure-specification, monitoring-design, six NFR designs and team pipeline practices.
