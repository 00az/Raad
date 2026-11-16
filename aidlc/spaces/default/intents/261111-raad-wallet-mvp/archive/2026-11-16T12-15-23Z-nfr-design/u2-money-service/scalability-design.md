# Scalability Design — U2 Money Service

Conversation language: English.

## Compute and Data Distribution

Keep each request handler stateless and horizontally scalable. Lambda concurrency is bounded per environment to protect downstream stores; start with the existing development guardrail of 20 reserved concurrent executions and set staging/production limits from load-check evidence and account quotas. Do not increase concurrency without verifying the 10-user target and DynamoDB throttling behavior.

Use DynamoDB on-demand capacity for the MVP. Partition by environment-scoped owner or entity key, not a global constant. Wallet reads/writes are keyed by user; holder lookup is keyed by normalized email; transfer history uses per-user access keys for sent and received entries. Avoid table scans and a single global counter. Keep all monetary invariants in conditional/transactional writes so horizontal compute scaling cannot bypass them.

History is a bounded fan-out over the caller's sent and received index streams, merged by `(completedAt DESC, transferId DESC)` within the cursor snapshot. The cursor determines last keys for both streams; page size remains at most 100 and counterparties are resolved in a bounded batch. A user with many transfers cannot cause an unbounded response.

## Capacity Guardrails

The only accepted load target is 100 users total and approximately 10 concurrent users. Scale-up signals are Lambda throttles/concurrency, API p95 latency, DynamoDB throttles, and transaction cancellation rate. Capacity above the target requires a new load test and explicit review of per-user partition hot spots. No cache, read replica, queue, shard layer, or regional active-active replication is introduced for this MVP.

## Service Extension

New RAAD services attach through the shared edge's path mapping and own their compute/data. MoneyService keeps the C1 path and contract stable; it does not add coupling to AI or Qattah. New clients continue to use the published C1 contract.

## Sources

`scalability-requirements.md`, `performance-requirements.md`, `functional-spec.md`, `rules.md`, `contract-summary.md`, and `tech-stack-decisions.md` define capacity, stable paging, and extension boundaries.
