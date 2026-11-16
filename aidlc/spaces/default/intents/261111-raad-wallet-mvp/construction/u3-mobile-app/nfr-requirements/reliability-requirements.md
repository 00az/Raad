# Reliability Requirements — u3-mobile-app

Conversation language: English.

## Scope

U3 completes the mobile UI and client behavior on iOS/Android; it owns neither server balances nor provider account settings. Arabic and English cover all frontend text, validation, states and accessibility labels. These are acceptance requirements, not claims of executed tests.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR3.10 | Parse and format SAR using integer halalas throughout all mobile forms, projections and snapshots; never floating point. Preserve the authoritative server balance and completed result. | Boundary/round-trip tests include 100 and 50000 halalas, overprecision, zero, negative, exact balance and very long input; localized display never changes the integer amount. |
| NFR4.10 | Persist one immutable key/recipient/amount per confirmed intent before send; suppress double taps. U1 unknown outcomes prohibit resubmit; full U2 enables explicit same-key retry and never fabricates historical outcomes. | Crash/restart/double-tap/lost-response tests with both pinned capability profiles. |
| NFR5.10 | Offline/failing reads show a stale timestamped snapshot or an error if no snapshot; never fabricate a successful balance/history or a zero. | Offline/recovery tests and independent device journeys; no local uptime SLA replaces server production target. |
| NFR15.10 | Preserve UTC instants and deterministic server order; display the same instant in device-local time, including daylight-saving transitions. | Fixed-clock tests in Riyadh and another zone; locale changes cannot change money or keys. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

