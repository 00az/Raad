# performance design — u2-money-service

Conversation language: English.

## Budget and deadlines
Keep the inherited public p95 <=2000 ms including edge authorization, cold initialization and service work at 100 registered/about 10 active users. Allocation: edge 200, MoneyApi auth 100, resolution 250, atomic commit 1000, serialization 200, margin 250 ms. These are engineering budgets, not observed results. Every U2 dependency attempt <=1 second including SDK retries; bound total work below MoneyApi 7-second hard timeout, edge 9 seconds, client 15 seconds. Reuse bounded connections (two outbound per execution); no unbounded retry queue.

## Data access
On-demand DynamoDB; strong keyed wallet/outcome reads, transactional success writes; no balance/result/profile caching. Cache only verifier configuration and public signing keys with the inherited six-hour monotonic TTL, once-per-minute unknown-kid refresh guard, one refresh then 401 if still unknown; unavailable expired discovery returns 503. Bound history to 20 default/100 max and counterparties to a bounded batch. History gap detection and snapshot algorithm are in scalability-design; retry within the same dependency/deadline budget, then return safe 503 rather than incomplete success.

## Evidence
Use native CloudFront public time-taken observations and complete eligible-response reconciliation as U1/U4 specify. At least 200 valid funded attempts over >=10 minutes, idle-start plus sustained windows; retain cold/slow observations. Report technical failures/refusals separately. Handler duration cannot establish the public SLO. No production latency claim until deployed load evidence passes.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design/functional-spec.md and rules.md; shared inception/contract-design/contract-summary.md and domain-design/components.md; U1 nfr-design/nfr-design-questions.md (free DNS decision b8664859). No target is lowered by this revision.
