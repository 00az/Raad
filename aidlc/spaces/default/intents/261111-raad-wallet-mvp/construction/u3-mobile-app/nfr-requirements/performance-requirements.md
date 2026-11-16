# Performance Requirements — u3-mobile-app

Conversation language: English.

## Scope

U3 completes the mobile UI and client behavior on iOS/Android; it owns neither server balances nor provider account settings. Arabic and English cover all frontend text, validation, states and accessibility labels. These are acceptance requirements, not claims of executed tests.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR6.10 | C1 request timeout remains 15 seconds; only its permitted read/setup operations get one bounded retry. Transfers never retry automatically; same-key retry is user initiated only after full U2 conformance. | Fault tests count attempts and deadlines; separate device/network elapsed from the public API's 2-second p95. |
| NFR7.10 | Render history by C1 pages (20 default,100 maximum), including a 1000-entry test history; do not eagerly fetch all pages or issue duplicate load-more operations. | Instrument page requests and screen states; verify no skipped/duplicate entries in an active cursor chain. |
| NFR9.10 | An older screen/session response cannot replace newer state; offline status disables writes and never queues them. | Controllable out-of-order, offline and session-switch tests; no artificial zero balance. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

