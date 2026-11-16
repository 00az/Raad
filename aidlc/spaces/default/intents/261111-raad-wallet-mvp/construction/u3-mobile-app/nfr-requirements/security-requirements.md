# Security Requirements — u3-mobile-app

Conversation language: English.

## Scope

U3 completes the mobile UI and client behavior on iOS/Android; it owns neither server balances nor provider account settings. Arabic and English cover all frontend text, validation, states and accessibility labels. These are acceptance requirements, not claims of executed tests.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR1.10 | All private screens and caches are bound to the verified user/environment. Sign-out and expired sessions clear or mask private views and navigation. | Back gesture, reopen, account switch and late-response tests reveal no previous account data. |
| NFR2.10 | Use TLS 1.2 or later and normal platform certificate/hostname validation for C1/C3. Access/refresh tokens and pending private state use protected device storage; passwords/codes are not persisted. | Inspect actual release network/storage adapters and test invalid certificate/refused insecure URLs. Never disable certificate validation for test convenience. |
| NFR10.10 | No password, code, token, email, name or request payload appears in diagnostic output, crash reports, test artifacts or telemetry. | Recognizable-value scans across success/failure paths, including Flutter subprocess output. |
| NFR11.10 | Collect no personal category beyond email/name; store only account-scoped necessary pending/snapshot data and clear it on explicit sign-out. | Inspect stored records before/after sign-out and account switching. |
| NFR12.10 | Respect stable 429 and Retry-After without automatic write retry; never treat client validation or disabled buttons as server authorization. | Burst/refusal fixtures plus same-key replay integration with U2. |
| NFR14.10 | At least 80% line coverage of measured app code, with format/lint/contract-pin checks and actual VoiceOver/TalkBack,200% text and keyboard/switch checks on both platforms. | Record unit/widget/contract results separately from real-device and manual accessibility evidence; meet refined WCAG 2.1 AA checklist. |
| NFR9.11 | Every frontend screen and status supports Arabic/English; switching language preserves financial intent/key and session. Proposed Western digits remain an explicit A8 review assumption. | Widget/screenshot/catalog completeness checks in both directions, LTR isolation and native Arabic review; unknown error codes show safe translations. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

