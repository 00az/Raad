# Reliability Design — U2 Money Service

Conversation language: English.

## Atomic Money and Idempotency

Use DynamoDB `TransactWriteItems` for successful transfers. One transaction conditionally confirms the sender balance and absent request key, debits and credits the two wallets, creates the Transfer and both history index items, and records the immutable successful TransferRequest outcome. A transfer never becomes visible unless all writes commit. On a transaction conflict, perform a strongly consistent read of the request key: if a matching outcome now exists, replay it; if a different fingerprint exists, return `IDEMPOTENCY_KEY_REUSED`; if no key exists, re-evaluate the sender balance and either retry a safe transaction or persist the first refusal.

Do not create a separate durable `reserved` idempotency row before the money transaction. The conditional full transaction is the reservation and outcome commit, so a crash before commit leaves no abandoned key that could stall retries. Persist business refusals as a single conditional request outcome without changing balances or writing history.

Define refusal precedence deterministically: malformed/authentication failures first; `WALLET_NOT_FOUND` next without consuming a key; existing-key replay/conflict next; then amount-range refusal; then recipient-not-found/self-transfer; then insufficient funds. Once a business outcome is saved for a key, every identical repeat returns that outcome. The first request's fingerprint is based on API major version, normalized recipient email, and amountHalalas, stored only as a one-way digest.

## Wallet Setup and Event Delivery

Use one conditional transaction across Ledger and Directory tables for wallet setup: create the wallet with 100000 halalas only if absent, create/verify the unique WalletHolder only if the normalized email key is unclaimed, and record the C2 event receipt. A different event ID for an already provisioned user sees the existing user-keyed wallet and never credits again. A same-user concurrent event and `PUT /wallet` converge through conditional writes. If any transaction action fails, no partial wallet/holder/receipt set commits; the public `PUT /wallet` can safely retry.

Configure the C2 event source for at-least-once delivery, bounded retries for 24 hours, and dead-letter handling for invalid/exhausted events. The event path is asynchronous; C1 setup remains authoritative if event publication was lost before bus acceptance. Alarm on dead-letter movement using only event ID and environment.

## Recovery and Failover

Enable DynamoDB point-in-time recovery for both persistent tables in `stg` and `prd`. Restore both tables to the same selected point in time, validate wallet/holder/ledger invariants, then switch the service configuration to the restored table names. Keep `dev` disposable and isolated. Run a timed restore exercise proving **RPO ≤5 minutes** and **RTO ≤3 hours**; do not declare production-ready until measured restore time meets the target. PITR's latest restorable time is typically five minutes behind current time and supports a 35-day recovery window; restore creates new tables, so the cutover and validation steps are part of the RTO. [DynamoDB backup and restore](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Backup-and-Restore.html).

The 99.5% monthly production availability target permits less than 3 hours 22 minutes of downtime in a 28-day month; the 3-hour RTO leaves a limited margin. Alerting, recovery rehearsal, and non-destructive table replacement are required to protect that margin.

## Failure Handling

- Bound all dependency calls to 1 second and the Lambda execution to its configured hard timeout. Return a safe structured error when a dependency is unavailable.
- Retry only idempotent reads or operations with a persisted key; use bounded exponential backoff with jitter for C2 delivery. Never automatically retry a transfer without its original idempotency key.
- Treat insufficient balance, invalid recipient, self-transfer, and amount-range outcomes as business results, not transient errors or circuit-breaker failures.
- Health/readiness signals distinguish a live handler from a service unable to reach required persistence. Readiness failure is visible to alarms; it does not make a public health endpoint reveal internals.

## Sources

`reliability-requirements.md`, `performance-requirements.md`, `functional-spec.md`, `rules.md`, `contract-summary.md` (C1/C2/C5), and `tech-stack-decisions.md` define atomicity, event retries, recovery, and timeouts. DynamoDB transactions provide ACID behavior within a Region: [DynamoDB transaction constraints](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html).
