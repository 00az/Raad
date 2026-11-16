# scalability design — u4-platform

Conversation language: English.

## Limits and mapping isolation
Initial environment concurrency20 subject to real quotas and demo load evidence; bounded HTTP pools, on-demand owner-partitioned DynamoDB. Never increase limits to conceal contention or relax Ledger conditions. Exact platform rate counters are independent from money stores; TTL expiration is cleanup only, windows derive from server time so delayed deletion cannot reopen a window.
Each mapped service owns compute/data and explicit target/IAM permissions. Attach a dev stub path and verify its response without MoneyService source/C1 changes; /money protection unchanged. No catch-all cross-environment targets or unbounded queues. Capacity changes need measured100-user/~10active acceptance.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
