# Technology Decisions — u4-platform

Conversation language: English.

## Decisions and Rationale

Retain Python CDK and shared AWS identity/edge/event/configuration responsibilities in Raad. Existing implementation candidates are Cognito, API Gateway HTTP API, CloudFront/WAF, Secrets Manager, CloudWatch/SNS and the approved telemetry transport. These are inherited design inputs, not fresh version claims; Infrastructure Design verifies current capabilities, packages and exact resources. Use generated distribution hostnames and existing account 027863026273/us-east-1 for deployment planning; no domain purchase or hosted-zone fees. Cloud hosting is not claimed free. Short-lived credentials, independent repo pipelines and stage-first production promotion remain mandatory.

## Quality and Boundaries

Use committed lockfiles and the team's exact local/CI commands. Do not weaken existing coverage, lint, type, dependency or infrastructure security gates. Fake/simulator checks are not live-provider/deployed proof. Current versions and service limits must be verified during implementation, not guessed here. No domain registration is authorized; hosting usage charges remain separate.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

