# Reliability Requirements — U2 Money Service

Conversation language: English.

## Availability, Durability, and Recovery

| ID | Requirement | Acceptance |
|---|---|---|
| NFR3.1 | Store all money as whole halalas; across any successful transfer sequence the total funds are conserved and no wallet balance falls below zero, except for one-time opening credits at wallet creation. | Property-based transfer tests maintain the total and non-negative balance invariants. |
| NFR3.2 | The Ledger money-movement core maintains at least 95% line and branch coverage. | Coverage report for the isolated money core meets both floors; do not lower a floor to make CI pass. |
| NFR4.1 | A repeated request never moves money twice, including simultaneous requests; the first business outcome for a caller/key is replayed exactly. | Sequential and concurrent idempotency replay tests pass against a real local data-store container. |
| NFR4.2 | Concurrent transfers use atomic balance conditions so a wallet cannot be overdrawn. | Concurrent requests against a real local data-store container preserve total money and non-negative balances. |
| NFR5.1 | The production (`prd`) C1 API and wallet service achieve at least 99.5% availability in each calendar month. | Report monthly successful eligible requests and service availability from monitoring; planned maintenance is not silently removed from the denominator. |
| NFR5.2 | Wallet and transfer data recovery has RPO no greater than 5 minutes and RTO no greater than 3 hours. | A documented restore exercise demonstrates both targets; this RTO fits within the 99.5% monthly downtime budget, including February. |
| NFR5.3 | A completed transfer is an all-or-nothing operation: sender debit, recipient credit, transfer row, and keyed result commit together. | Failure injection at each persistence boundary shows either the full transfer or no transfer. |
| NFR5.4 | Repeated or simultaneous use of the same sender/key cannot move money twice; the first business result is stable and replayable. | Sequential, simultaneous, and lost-response replay tests pass against a real local data-store container. |
| NFR5.5 | Accepted `UserConfirmed` events may be delivered more than once, but create one wallet and one starting credit; event failures do not make confirmation appear to fail. | Duplicate event tests and the C2 retry/dead-letter path demonstrate one wallet and one credit. |

## Failure Handling and Degradation

| ID | Requirement | Acceptance |
|---|---|---|
| NFR9.2 | Every outbound call has a finite timeout. On timeout or store unavailability, return a safe structured error and never report a partial transfer as successful. | Inject a slow/unavailable dependency and verify bounded response, no partial state, and retry-safe behavior. |
| NFR9.3 | Transient failures may be retried only where the operation is idempotent; do not automatically retry business refusals or an unkeyed mutation. | Failure tests show only explicitly safe operations retry and keyed transfer replay returns the original result. |
| NFR9.4 | The U2 service exposes health/readiness signals that distinguish process health from inability to access required persistence. | Health checks report dependency failure for alerting without exposing credentials or internal details publicly. |

## Time Representation

| ID | Requirement | Acceptance |
|---|---|---|
| NFR15.1 | Store all instants in UTC and return an offset-bearing timestamp; presentation in the device's time zone is U3's responsibility. | A transfer at 23:30 Riyadh time round-trips to the same instant and displays correctly in Riyadh and another device zone. |

## Constraints

Wallet values are simulated SAR. Durability and correctness apply to these records, but no real payment settlement or external financial institution recovery is in scope. Backup/restore implementation, failover, and recovery procedures are finalized in Infrastructure Design and Operation; missing recovery prerequisites must be visible before production release.
