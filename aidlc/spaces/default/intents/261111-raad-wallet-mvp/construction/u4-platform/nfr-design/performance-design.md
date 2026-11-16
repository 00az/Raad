# performance design — u4-platform

Conversation language: English.

## Public budget and deadlines
Use U1/U2 2000-ms public p95 budget including edge JWT verification/cold initialization; no handler-only substitute. Edge hard9s, MoneyApi7s, signed upstream <=7.5s and <=remaining edge deadline, client15s. U2 dependency attempt <=1s, bounded two-connection pools, no unbounded retries. Public sample reconciliation and cold/sustained load follow U1 design, >=200 eligible attempts/10minutes at100 registered/about10active. Rate-limit refusal windows are reported separately; no larger RPS forecast.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
