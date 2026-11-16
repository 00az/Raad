# Observability Requirements — u3-mobile-app

Conversation language: English.

## Scope

U3 completes the mobile UI and client behavior on iOS/Android; it owns neither server balances nor provider account settings. Arabic and English cover all frontend text, validation, states and accessibility labels. These are acceptance requirements, not claims of executed tests.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR8.10 | Client status distinguishes loading, empty, refused, error, uncertain and stale. Operational API metrics are U1/U2/U4-owned; the app adds no tracing backend or personal telemetry. | Widget tests and privacy scan; app timing is never substituted for public API latency. |
| NFR14.11 | Maintain separate evidence for API, iOS, Android and fake/live journeys, with exact app/backend revisions and environment. | Acceptance report explicitly labels every unrun check and every stand-in. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

