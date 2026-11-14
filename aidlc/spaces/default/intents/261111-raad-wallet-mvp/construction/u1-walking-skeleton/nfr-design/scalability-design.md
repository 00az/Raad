# Scalability Design: U1 Walking Skeleton

Conversation language: English.

## C1 — Bounded stateless request handling

MoneyApi has no authoritative process-local wallet, balance, request outcome or user session. Every mutation is decided by Ledger's store transaction, so adding a service execution environment cannot bypass a balance condition or uniqueness check. Keep the approved MoneyApi/Ledger/WalletDirectory component boundaries; no additional deployable business service is introduced.

Size dev initially for 20 simultaneously admitted MoneyApi requests, covering two parallel reads for each of 10 active users. This is a candidate capacity setting for Infrastructure Design to validate, not a new concurrency/RPS acceptance target or an assumption that 20 workers always exist. Client-generated retries count against admission. Do not create an unbounded in-process queue or a thread per request. Each execution environment has the bounded outbound use described in performance-design.md; Infrastructure Design shows the aggregate connection/throughput envelope under its chosen compute/store.

Above that envelope, reject promptly with the applicable C5/C1 429 RATE_LIMITED and Retry-After when admission is a rate limit, or 503 SERVICE_UNAVAILABLE and Retry-After for exhausted/unavailable service capacity. Never report an accepted or pending transfer for a rejected admission. Initial Retry-After is 1 second for capacity exhaustion, subject to the edge's configured rate-limit reset. The mobile client does not automatically retry transfers. Basic edge protection is U1; full per-caller abuse controls remain U2/U4.

## C2 — Transactional scaling

Enforce one wallet per owner using a persistent unique/conditional key, with the opening credit in that same atomic creation. A read-then-unconditional-insert is insufficient. A simultaneous setup loser reads the winner and adds no credit. Directory user-ID and normalized-email uniqueness must likewise be store-enforced, within WalletDirectory's boundary.

Keep the source-balance condition, debit, credit and one immutable Transactions row in one all-or-nothing Ledger operation. The dedicated table is keyed by transferId, not wallet ID; many transfers between the same wallets retain distinct rows, with both wallet IDs stored as references. A concurrent sender cannot overdraw by acting on a pre-read balance. No write-behind cache, delayed credit, queue, replica or cross-service compensating debit replaces that transaction. A conflict may be reported safely without changing money; it may not become a partial success. U1 stores no key-to-outcome record. U2 introduces TransferRequest and atomically commits its successful outcome with the same transfer row and both balances.

The physical store must support these primitives and a real local-container concurrency test. Infrastructure Design chooses the product, owner/directory unique keys, transaction isolation/conditions and remaining layout while preserving the dedicated Transactions table keyed by transferId. This stage does not select a database or shard topology. Consistency and the logical ownership boundary take priority over theoretical scale.

## C3 — Bounded queries and service extension

Index/query design must support owner-to-wallet lookup, normalized-email-to-holder lookup and completed transfers for one wallet ordered newest first. Query no more than the requested first page plus bounded lookahead required by the C1 response. Batch distinct counterparty IDs from that page. Do not scan all users or load all transfers into memory and trim afterward. C1 and Functional Design fix the tie order as completedAt descending then transferId descending. U1 Infrastructure Design must demonstrate the bounded initial first-page access path. U2 extends the same Transactions table with sender/recipient history indexes and cursor paging; it does not create another transfer-history store. Both parties' views refer to the same immutable transferId.

Keep /money as the service mapping boundary and /v1 as its contract version. Platform outputs expose the shared domain/mapping interface; each service owns its API and registration through the platform's interface. U1 supplies that boundary, while the later platform unit demonstrates adding another service. No stub service, AI assistant, Qattah or extra region is built here.

## C4 — Capacity evidence and change triggers

Run performance-design.md P4 against the real dev path with 100 registered users and 10 active users. Verify atomic first setup and overlapping transfers separately with the selected real local store container. Record active requests, admission refusals, dependency utilization and the measured p95. Start investigating capacity when admitted in-flight requests reach 80% of the selected limit for 3 consecutive one-minute periods, any admission refusal occurs at the approved demo load, or transfer latency fails its target. These are engineering investigation thresholds, not new product SLOs or automatic permission to resize infrastructure.

The initial design uses bounded managed capacity and no custom autoscaling controller. Infrastructure Design may map demand-driven scaling within explicit min/max limits, and must show that its maximum cannot exceed downstream safe capacity. A change to the logical limit requires the same correctness/load checks; never weaken them to make a load run pass.

## Sources

- construction/u1-walking-skeleton/nfr-requirements/scalability-requirements.md: NFR3.1–3.2, NFR7.3–7.4 and NFR13.1.
- construction/u1-walking-skeleton/nfr-requirements/performance-requirements.md: NFR6.1 and NFR7.1–7.2.
- construction/u1-walking-skeleton/nfr-requirements/reliability-requirements.md: NFR3.3–3.4 and bounded failure behavior.
- construction/u1-walking-skeleton/nfr-requirements/tech-stack-decisions.md: deferred physical storage and compute selection.
- construction/u1-walking-skeleton/functional-design/functional-spec.md: concurrency-sensitive workflows, dedicated transaction rows and stable first history page.
- inception/contract-design/contract-summary.md: C1 ordering and errors; C5 mapping boundary.
- inception/domain-design/components.md: component ownership and logical store separation.
