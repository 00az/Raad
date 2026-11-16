# Technology Decisions — u5-landing-page

Conversation language: English.

## Decisions and Rationale

Retain plain static HTML/CSS in RaadWeb, semantic bilingual documents and no frontend application framework. Hosting remains the team's S3/CloudFront design, with public access restrictions and generated HTTPS distribution URL validated in Infrastructure Design. No custom domain is purchased. Keep email/address copy configurable as public content, separate from runtime operational alerts. No backend, sign-in SDK or payment integration is introduced.

## Quality and Boundaries

Use committed lockfiles and the team's exact local/CI commands. Do not weaken existing coverage, lint, type, dependency or infrastructure security gates. Fake/simulator checks are not live-provider/deployed proof. Current versions and service limits must be verified during implementation, not guessed here. No domain registration is authorized; hosting usage charges remain separate.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

