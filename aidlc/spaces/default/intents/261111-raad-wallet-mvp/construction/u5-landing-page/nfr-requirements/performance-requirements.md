# Performance Requirements — u5-landing-page

Conversation language: English.

## Scope

U5 is a static bilingual public page with no wallet/auth API calls. Its public address is abdulaziz.alrubai@outlook.com; this does not replace operational alerts to jjii0@hotmail.com. Content/native Arabic wording requires review before release.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR7.10 | At the approved demo scale (100 users/about10 active), both language documents and static assets serve successfully over HTTPS. | Concurrent page fetch smoke check; no separate numerical page-latency SLO is invented from the transfer API's 2-second target. |
| NFR9.10 | Primary introduction/language/contact navigation works without application JavaScript, and an unavailable page is a failed smoke test, not an empty success. | Fetch both documents and inspect basic navigation with scripting off; check missing-asset fallback. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

