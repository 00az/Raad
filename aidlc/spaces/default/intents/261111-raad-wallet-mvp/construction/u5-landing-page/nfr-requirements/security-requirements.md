# Security Requirements — u5-landing-page

Conversation language: English.

## Scope

U5 is a static bilingual public page with no wallet/auth API calls. Its public address is abdulaziz.alrubai@outlook.com; this does not replace operational alerts to jjii0@hotmail.com. Content/native Arabic wording requires review before release.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR2.10 | HTTPS and inherited TLS 1.2 policy apply to both language documents/assets. A generated CloudFront hostname avoids domain purchase but still requires actual protocol-policy proof. | Protocol/certificate checks; an unsupported default policy remains a release-blocking design gap. |
| NFR1.10 | No authenticated session, wallet ownership, payment field or sign-in flow exists on this page; an auth/money integration must not be added implicitly. | Static source/network inventory confirms zero wallet/auth calls and no credential collection. |
| NFR11.10 | The page collects no personal data and uses no analytics/cookie registration. Only the approved public contact address is displayed. | Browser/network and storage check confirms no hidden collection or third-party tracking. |
| NFR10.10 | Build/access diagnostics contain no visitor-provided personal fields or wallet payloads; query logging policy must avoid collecting arbitrary query strings. | Infrastructure logging configuration and representative log scan; do not reuse money telemetry schemas blindly. |
| NFR14.10 | Static HTML/CSS has no executable coverage percentage; both-language smoke, semantic markup, keyboard/skip link,200% text,320dp reflow and automated accessibility scan are required. | Each deploy checks its actual URL; browser/manual evidence is distinguished from parser-only checks. |
| NFR9.11 | All page copy/actions/accessibility names support Arabic and English; email stays isolated LTR, mail-handler failure leaves a visible selectable address, and opening mail never claims delivery. | Both-language/browser/screen-reader checks with no mail handler and long text. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

