# Performance Requirements — u4-platform

Conversation language: English.

## Scope

U4 is infrastructure-only packaging; shared C2–C5 contracts specify its behavior, so there is no invented U4 business model. This pass supplies platform quality constraints even where category artifacts are optional by unit kind.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR6.10 | The public transfer boundary includes authorization, forwarding, initialization and service work in the inherited p95<= 2000 ms target at demo load; handler timing is diagnostic only. | Retain slow/cold samples; reconcile public observations to every eligible response. Expected refusals and technical failures are separate. |
| NFR7.10 | Support 100 registered users and approximately 10 active users without account-specific starvation; no larger traffic forecast is asserted. | Environment-specific load proof and configured quotas/concurrency inventory. |
| NFR9.10 | Every edge/provider/dependency call has a finite deadline; responses preserve C1/C5 safe errors and correlation agreement. | Timeout/fault injection with bounded completion, no secret/profile disclosure. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

