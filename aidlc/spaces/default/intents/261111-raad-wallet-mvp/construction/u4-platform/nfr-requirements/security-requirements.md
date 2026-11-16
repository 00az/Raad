# Security Requirements — u4-platform

Conversation language: English.

## Scope

U4 is infrastructure-only packaging; shared C2–C5 contracts specify its behavior, so there is no invented U4 business model. This pass supplies platform quality constraints even where category artifacts are optional by unit kind.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR1.10 | C3/C5 identity settings and verifier outputs are environment-bound; signatures, issuer, audience, type, expiry and matching profile subject are independently verified at both layers. | P1–P13 capability matrix and negative wrong-environment/type/subject tests against actual configured flow. |
| NFR2.10 | All app/API/provider/service traffic must meet inherited TLS 1.2 minimum. Prefer the requested AWS-generated hostname with no domain purchase, but do not declare compliance from default HTTPS alone. | Deployed protocol/certificate probes prove the configured policy; unsupported default-certificate policy is a blocking gap for NFR/Infrastructure Design, not permission to lower the target. |
| NFR2.11 | Encrypt persistent platform/configuration secrets and logs at rest; secrets remain runtime-only with narrow roles and never in C4 or verifier configuration. | Synth/resource inspection and secret scan of templates/build artifacts; generated origin credential never enters client config. |
| NFR12.10 | Money routes have no public bypass around intended CloudFront WAF/rate/telemetry boundary. Origin-only credentials or equivalent restrictions fail closed before private work. | Direct-origin missing/counterfeit credential refuses; public-edge request succeeds. Validate header overwrite and no credential forwarding to clients/service logs. |
| NFR12.11 | Per-caller account, recipient and transfer limits isolate an abusive caller; attempts that send also consume lookup policy where C1 requires it. | U4 NFR Design chooses measurable windows/limits from NFR7 capacity and C3; burst tests show another caller unaffected. Native SDK identity calls cannot silently bypass claimed account protections. |
| NFR10.10 | Logs/metrics/alerts contain no password, code, token, email or display name; dimensions are bounded. | Scan success, refusal, provider failure, WAF and dead-letter output with recognizable values. |
| NFR11.10 | Identity stores only email/displayName plus required opaque identifiers; no real payment/identity documents. | Inspect provider attributes and event/schema output. |
| NFR14.10 | Python CDK, cdk-nag, strict types, lint, audit, secret scan and >= 80% platform repo line coverage remain required; other-engineer PR review before merge. | Actual synth/bundle and CI evidence; assertion tests do not replace real packaging. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

