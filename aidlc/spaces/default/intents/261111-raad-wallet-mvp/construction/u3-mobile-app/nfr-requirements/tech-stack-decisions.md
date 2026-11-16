# Technology Decisions — u3-mobile-app

Conversation language: English.

## Decisions and Rationale

Retain Dart/Flutter, pinned SDK/pubspec.lock, generated C1 client, platform secure storage and C3 SDK adapter. C4 comes from actual environment outputs and must fail builds on missing/extra/cross-environment values. Preserve current SDK-token-compatible provider profile lookup at the service boundary; do not reintroduce an OAuth-only assumption. U3 owns translated catalogs and accessibility behavior; no new backend, payment SDK, analytics SDK or runtime upgrade is selected here.

## Quality and Boundaries

Use committed lockfiles and the team's exact local/CI commands. Do not weaken existing coverage, lint, type, dependency or infrastructure security gates. Fake/simulator checks are not live-provider/deployed proof. Current versions and service limits must be verified during implementation, not guessed here. No domain registration is authorized; hosting usage charges remain separate.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

