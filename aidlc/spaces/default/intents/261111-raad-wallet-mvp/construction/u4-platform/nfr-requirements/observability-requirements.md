# Observability Requirements — u4-platform

Conversation language: English.

## Scope

U4 is infrastructure-only packaging; shared C2–C5 contracts specify its behavior, so there is no invented U4 business model. This pass supplies platform quality constraints even where category artifacts are optional by unit kind.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR8.10 | Every environment has request/error/latency/technical-transfer-failure dashboard and alarms; stg fault tests prove actual email delivery to jjii0@hotmail.com. | NFR Design sets windows, min samples, breach/recovery/insufficient-data policies; email subscription confirmation is required evidence. |
| NFR8.11 | Public latency acceptance requires complete observation reconciliation; missing, duplicate/conflicting logs or insufficient samples cannot report healthy complete-population results. | Loss/duplicate/late delivery and idle-start probes; current best-effort transport limitations remain explicit. |
| NFR15.10 | Operational timestamps are UTC; correlation uses the approved protected profile and cannot become a personal metric dimension. | Cross-boundary trace of allowed log records and environment separation. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

