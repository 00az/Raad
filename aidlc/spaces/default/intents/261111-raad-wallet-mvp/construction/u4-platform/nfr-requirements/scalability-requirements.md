# Scalability Requirements — u4-platform

Conversation language: English.

## Scope

U4 is infrastructure-only packaging; shared C2–C5 contracts specify its behavior, so there is no invented U4 business model. This pass supplies platform quality constraints even where category artifacts are optional by unit kind.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR7.11 | Bound concurrency, dependency pools and rate policies for demo load; increasing capacity cannot relax Ledger conditions or identity boundaries. | Record selected quotas and overhead before load acceptance; no automatic unbounded scaling claim. |
| NFR13.10 | A stub service attached by its own path mapping answers at dev without changing MoneyService code or C1 contract. | Integrated mapping demonstration, preserving /money behavior and origin protection. |

These requirements define future acceptance. No deployment, manual review or load result is asserted here. Derived implementation budgets and resource choices belong to NFR Design and Infrastructure Design.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1–NFR15, demo scope and constraints.
- `inception/contract-design/contract-summary.md`: C1–C5, timeout/retry, identity, event and configuration contracts.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: unit boundaries and shared acceptance ownership.
- This unit's `functional-design/functional-spec.md` and `rules.md` where applicable; U4 is packaging and instead uses shared C2–C5 contracts.
- `aidlc/spaces/default/memory/team.md`: stack, testing, security and delivery obligations.
- Person's decisions: bilingual frontend, public email and prd credit (77a32fc9); AWS-assigned cloudfront.net hostname (951a2dfd).

