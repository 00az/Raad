# Reliability Requirements — u4-platform

Conversation language: English.

## Scope

U4 is infrastructure-only packaging; shared C2–C5 contracts specify its behavior, so there is no invented U4 business model. This pass supplies platform quality constraints even where category artifacts are optional by unit kind.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR5.10 | Preserve >= 99.5% prd calendar-month service availability. U2's selected data recovery objectives remain RPO <= 5 minutes and RTO <= 3 hours; platform restoration must not invalidate them. | Monthly eligible-request report includes maintenance and has defined no-traffic coverage. Recovery drill records actual restoration time and retained environment configuration. |
| NFR4.10 | C2 at-least-once confirmation delivery uses the idempotent U2 consumer; provider confirmation never fails solely because publish failed. Accepted delivery retries for 24 hours, then dead-letter/alarm. | Fault tests distinguish publish-not-accepted, accepted-retry, duplicate and wrong-environment paths; safety-net PUT repairs lost setup. |
| NFR9.11 | Missing platform outputs, origin credentials or service targets fail closed without fabricated readiness; deployed URL and environment outputs must agree across consumers. | Remove/mismatch configuration in tests and verify safe unavailable/refusal. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

