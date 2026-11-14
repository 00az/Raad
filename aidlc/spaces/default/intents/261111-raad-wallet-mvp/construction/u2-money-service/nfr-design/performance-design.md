# Performance Design — U2 Money Service

Conversation language: English.

## Request Path and Latency Budget

The C1 API remains a stateless Python 3.12 Lambda service behind the shared public edge. The edge performs only routing, firewall/rate-limit checks, and SigV4 invocation; the service validates C5 identity, applies bounded input validation, then performs bounded DynamoDB reads/writes. No money-changing response is served from a cache.

The 2-second p95 transfer target is budgeted across edge and service work: authentication and bounded key lookup, recipient directory query, atomic transaction, and response mapping. Each outbound dependency call has a 1-second timeout; the handler returns a structured error before the Lambda's 7-second hard timeout. Load checks run at the approved 10 concurrent users and record p50/p95, errors, throttles, and transaction cancellations.

## Query and Compute Choices

- Keep the API handler stateless; do not require warm sessions or affinity.
- Use DynamoDB on-demand capacity at MVP scale. Alarm on throttling and consumed-capacity anomalies before changing capacity mode.
- Use keyed partition queries and the 20-item default / 100-item maximum for history. Do not scan the ledger table.
- Resolve history counterparties in one bounded batch read per page.
- Avoid caching balances, transfer outcomes, wallet ownership, or directory mappings: stale financial state risks incorrect review screens or authorization. Cache only non-sensitive C5 verification configuration/JWKS within its key expiry and refresh policy.
- Keep event consumption asynchronous; it must not add latency to account confirmation. The synchronous `PUT /wallet` path remains the setup safety net.

## Sources

`performance-requirements.md`, `functional-spec.md`, `rules.md`, `contract-summary.md`, and `tech-stack-decisions.md` define the targets, C1/C2 paths, and data-access constraints. The 1-second call timeout is the approved NFR6.4 budget; actual Lambda and DynamoDB settings are implemented in Infrastructure Design and Code Generation.
