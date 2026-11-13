# Performance Design: U1 Walking Skeleton

Conversation language: English.

## P1 — Latency budget and deadlines

The acceptance target remains at least 95% of transfer requests answered within 2,000 ms at the public API boundary, with 100 registered demo users and 10 active concurrently. Valid funded transfers must succeed; fast errors do not turn a failed transfer into a passing sample. No latency SLO is added for other operations.

The following is an initial engineering allocation for an established wallet, not a claim about measured service performance:

| Work on the transfer path | Budget, ms |
|---|---:|
| Public edge, including its token verification | 200 |
| Independent MoneyApi token verification | 100 |
| Caller-wallet and recipient resolution | 250 |
| Guarded atomic Ledger change | 1,000 |
| Serialization and response transit through the edge | 200 |
| Unallocated margin | 250 |
| Total | 2,000 |

Key discovery, cold starts and contention can consume this margin or exceed the target. They remain in the measured distribution. Infrastructure Design must demonstrate the selected implementation against this allocation; it cannot turn it into evidence by copying it.

Use monotonic elapsed-time deadlines. The public edge has a 9-second overall limit from receipt of a complete request. Its key-discovery attempt is capped at 1 second and its upstream wait at the smaller of 7.5 seconds or the remaining edge budget. MoneyApi has a 7-second execution deadline from entry, leaving room to return a structured error through the edge. The C1 client timeout stays 15 seconds per attempt. These are failure bounds, not relaxed latency targets.

Every dependency operation is bounded by the remaining request time. Initial per-operation caps are: connection establishment 250 ms, key discovery 1 second total, an own-profile lookup 1 second total, a wallet/directory read 750 ms total, a batched history-profile lookup 1 second total and a Ledger write 2 seconds total. A total cap includes connecting, waiting and reading. A transaction is not started after its available budget is exhausted. SDK retries are disabled on the transfer write path; an unobserved commit after a timeout remains uncertain, as reliability-design.md specifies. The selected SDK/edge must support equivalent enforceable limits; Infrastructure Design records any mismatch before implementation.

## P2 — Reads, pooling and caching

Balances, recipient resolution and transfer results are read from their owning stores. Do not add a response cache, balance cache, replica read path, queue, distributed cache or asynchronous money movement. Only C5 public signing keys are cached, with the security-design.md lifetime and refresh rules. A stale balance must never authorize a debit.

Reuse a bounded HTTP/data client within each service execution environment where its SDK supports it. Initially allow at most two simultaneous outbound operations per execution environment, matching the independent balance/history read path; admission and connections remain bounded as scalability-design.md describes. Do not start one network request per history entry. Ledger selects only the caller's first page; MoneyApi collects distinct counterparty IDs and makes one bounded batch lookup, internally chunked only to the chosen store's batch limits. Default page size is 20, maximum 100. There is no whole-history or whole-directory scan.

## P3 — Retry budget

Only PUT /wallet, GET /wallet, POST /recipients/resolve and GET /transfers are eligible for one client retry after timeout, 500 or 503. Use 250–750 ms random delay unless a valid Retry-After requires longer. If Retry-After exceeds 5 seconds, show the retry time and leave the next attempt to the person instead of keeping an automatic timer. Never retry earlier than Retry-After. A 429 shows a wait/retry message and is not automatically retried. No validation/authentication/business refusal or POST /transfers is automatically retried. Disable a generated client's generic retry interceptor on transfers and avoid nested SDK/client retries that multiply attempts.

## P4 — Deployed performance check

Prepare 100 confirmed dev users with wallets and holder entries through supported setup, using credentials from the selected secrets store. Use an isolated, run-labelled fixture set. Verify readiness before timing: the unresolved setup concerns in Functional Design must not be hidden by direct store inserts. Ten active users run a representative balance, recipient, valid transfer and first-history-page cycle for 10 minutes, with a 1-second think interval between completed cycles. Do not submit a second operation for a user's transfer before the first finishes. Include at least 200 valid funded transfer attempts; extend the run if necessary. Use balanced sender/recipient pairs or sufficient known balances to avoid accidental insufficient-funds results. Record achieved concurrency and operation counts, rather than claiming a requests-per-second capacity.

Run an idle-start observation before the sustained run and retain both results. No warm-up samples are silently discarded. Capture public-edge total latency, valid-transfer status, expected business refusals, technical failures, sample count and nearest-rank p95. Acceptance requires both the combined idle-start/sustained population and the sustained population to have p95 at most 2,000 ms, with every valid funded transfer successful. Also report the idle-start subset separately and flag its slow results; this design grants no cold-start exemption from NFR6.1. Measure other endpoints diagnostically. Fault/load tools must not log payloads or credentials.

Record commit IDs for all three repos, environment, fixture run ID, timestamps, population, load shape and raw safe timing samples. API, iOS, Android and performance checks use independent fixtures or explicitly measured starting balances. scripts/verify-dev.sh remains the authorized integrated verification command; the load check supplements it and does not replace it.

## Dependencies and limits

Public C1 fields and methods remain authoritative. The approved Functional Design has unresolved holder setup, GET/PUT, public mapping, display, fixtures, ordering and integer-conversion concerns. These documents do not edit it or claim the concerns are closed. A failed setup or contract check is a failed prerequisite for this performance demonstration.

## Sources

- construction/u1-walking-skeleton/nfr-requirements/performance-requirements.md: NFR6.1–6.3, NFR7.1–7.2 and NFR9.1.
- construction/u1-walking-skeleton/nfr-requirements/security-requirements.md: token checks, privacy and protected dependencies.
- construction/u1-walking-skeleton/nfr-requirements/scalability-requirements.md: NFR7.3–7.4 and concurrency safety.
- construction/u1-walking-skeleton/nfr-requirements/reliability-requirements.md: NFR9.2–9.3, disposable dev and verification command.
- construction/u1-walking-skeleton/nfr-requirements/observability-requirements.md: boundary measurements and safe telemetry.
- construction/u1-walking-skeleton/nfr-requirements/tech-stack-decisions.md: existing Python/Flutter stack and deferred physical selections.
- construction/u1-walking-skeleton/functional-design/functional-spec.md: workflows and integrated check, with accepted concerns retained.
- inception/contract-design/contract-summary.md: C1 methods, schemas, 15-second timeout and retry policy; C5 verification.
