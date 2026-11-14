# Business Rules — U2 Money Service

Conversation language: English.

```yaml
rules:
  - id: BR2.1
    statement: A wallet has exactly one verified owner and is opened with 100000 halalas in SAR exactly once.
    category: constraint
    applies_to: Wallet
    trigger: PUT /wallet or UserConfirmed event
    logic: IF no wallet exists for the verified user in this environment THEN create one with 100000 halalas; IF it already exists THEN return the existing wallet without crediting it again.
    violation_behaviour: Reject identity/environment mismatch; do not expose wallet data.
    source: FR1.5, AC1.2.3, AC1.2.4
  - id: BR2.2
    statement: Wallet setup registers a holder only after ensuring the wallet exists.
    category: policy
    applies_to: Wallet and WalletHolder
    trigger: Wallet setup flow
    logic: IF wallet open succeeds THEN create or verify the holder using identity claims from the verified token/event; IF holder registration fails THEN return a safe setup failure and allow an idempotent retry that does not re-credit the wallet.
    violation_behaviour: Do not report setup success until both wallet and holder are ready; return the contract's safe unavailable/setup error.
    source: FR1.5, AC1.2.5
  - id: BR2.3
    statement: A wallet holder's normalized email belongs to at most one user.
    category: constraint
    applies_to: WalletHolder
    trigger: Holder registration
    logic: Normalize by trimming Unicode surrounding whitespace, NFC normalization, and lowercase comparison; IF emailKey belongs to a different userId THEN refuse registration without merging or changing either holder.
    violation_behaviour: Return the contract's conflict outcome without personal data in logs.
    source: FR1.6, AC1.2.6
  - id: BR2.4
    statement: Recipient resolution is exact and case/space-insensitive.
    category: validation
    applies_to: WalletHolder
    trigger: Recipient lookup or transfer request
    logic: Normalize input before complete-address validation and lookup; return only the single exact matching holder; IF none exists THEN return RECIPIENT_NOT_FOUND.
    violation_behaviour: Do not return partial matches, enumerate holders, or create a transfer.
    source: FR3.1, FR3.6, AC3.5.1, AC3.5.3
  - id: BR2.5
    statement: A user cannot transfer to their own wallet.
    category: authorization
    applies_to: Transfer
    trigger: Transfer request
    logic: IF normalized recipient resolves to the verified caller's userId THEN persist SELF_TRANSFER as the first keyed business outcome and change no balances.
    violation_behaviour: Return the contract's self-transfer refusal.
    source: FR3.6, AC3.5.2
  - id: BR2.6
    statement: Transfers accept only integer halalas from 100 through 50000 inclusive, with no daily aggregate limit.
    category: validation
    applies_to: TransferRequest
    trigger: Transfer request
    logic: IF amountHalalas is not an integer in the inclusive range THEN persist AMOUNT_OUT_OF_RANGE as the first keyed business outcome; otherwise evaluate the transfer.
    violation_behaviour: Return the documented amount-range refusal and leave balances/history unchanged.
    source: FR3.2, FR3.12, AC3.3.1, AC3.3.2, AC3.3.3
  - id: BR2.7
    statement: A transfer is atomic and never makes either balance negative or changes the total money.
    category: constraint
    applies_to: Transfer, Wallet
    trigger: Transfer commit
    logic: IF sender and recipient wallets exist and sender has sufficient balance THEN atomically subtract and add the same amount and write one completed Transfer and its successful request outcome; otherwise make no changes.
    violation_behaviour: Persist INSUFFICIENT_FUNDS as the first keyed business outcome; return the existing result on a repeat.
    source: FR3.5, FR3.8, AC3.7.1, AC3.7.2
  - id: BR2.8
    statement: One sender and idempotency key identify one immutable request fingerprint and one first business outcome.
    category: constraint
    applies_to: TransferRequest
    trigger: Transfer request
    logic: IF the pair is new THEN reserve it conditionally; IF the pair exists with the same fingerprint THEN return its original outcome; IF its fingerprint differs THEN return IDEMPOTENCY_KEY_REUSED without replacing the first result.
    violation_behaviour: Concurrent duplicates converge on the same saved result; the money movement and history entry occur at most once.
    source: FR3.7, FR3.9, FR3.10, NFR4, AC3.6.1, AC3.6.2, AC3.6.4, AC3.8.2, AC3.8.3
  - id: BR2.9
    statement: Each completed transfer has one unique immutable human-readable reference.
    category: constraint
    applies_to: Transfer
    trigger: Transfer creation
    logic: Generate a separate random short code for the reference; enforce uniqueness atomically and regenerate if it collides; keep the UUID transferId as the machine identifier.
    violation_behaviour: Never expose an ambiguous or duplicated reference as a completed result.
    source: FR3.4, FR5.1, AC3.1.2
  - id: BR2.10
    statement: History contains only completed transfers belonging to the verified caller and is stable across pages.
    category: authorization
    applies_to: Transfer
    trigger: GET /transfers
    logic: Return sent and received items newest first by completedAt then transferId descending; bind an opaque cursor to user, environment, size, sort, snapshot and last key; expire the chain after 24 hours.
    violation_behaviour: Refuse invalid, altered, expired, wrong-user, wrong-environment, or wrong-size cursors and require page one to reload; never skip or repeat entries within a valid snapshot.
    source: FR5.3, AC4.3.1, AC4.3.2
  - id: BR2.11
    statement: UserConfirmed delivery is at-least-once and environment-isolated.
    category: authorization
    applies_to: UserConfirmedEventReceipt
    trigger: UserConfirmed event consumption
    logic: IF eventId/userId is already processed THEN no-op; IF event environment differs from service environment THEN reject; otherwise run the same safe wallet setup and record the receipt idempotently.
    violation_behaviour: Invalid events go to dead-letter handling; accepted-event retries never create another wallet or starting credit.
    source: FR1.5, NFR4, AC1.2.3, AC1.2.4
  - id: BR2.12
    statement: Personal data is minimized and excluded from logs.
    category: policy
    applies_to: WalletHolder, UserConfirmedEventReceipt, MoneyApi
    trigger: Any request or event handling
    logic: Keep email/displayName only in WalletHolder; logs may include eventId, environment, and opaque user hash or final userId characters, never email, displayName, token, or full userId.
    violation_behaviour: Do not emit request/event payloads or personal data in diagnostics.
    source: NFR10, NFR11
```

## Rules Summary

| Area | Rule | Outcome |
|---|---|---|
| Wallet creation | BR2.1–BR2.3 | One starting credit, safe setup retry, no duplicate holder ownership |
| Transfers | BR2.4–BR2.9 | Exact recipient, validated range, atomic balance movement, immutable replay, unique display reference |
| History | BR2.10 | Caller-only stable pages with expiring bound cursors |
| Events and privacy | BR2.11–BR2.12 | Safe duplicate event delivery, environment checks, personal data excluded from logs |
