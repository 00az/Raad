# Entities — U2 Money Service

Conversation language: English.

```yaml
entities:
  - name: Wallet
    description: One SAR wallet owned by one verified account in one environment.
    attributes:
      - { name: walletId, type: opaque identifier, required: true, unique: true }
      - { name: userId, type: opaque identifier, required: true, unique: true }
      - { name: balanceHalalas, type: non-negative integer, required: true, default: 100000, min: 0 }
      - { name: currency, type: currency code, required: true, allowed: [SAR] }
      - { name: openedAt, type: UTC instant, required: true }
      - { name: version, type: positive integer, required: true, default: 1 }
    constraints:
      - Exactly one wallet exists per userId and environment.
      - Wallet identity is derived from the verified caller, never from request input.
      - A wallet's balance is always a whole number of halalas and never negative.
  - name: WalletHolder
    description: Directory record used to resolve recipient email and display names.
    attributes:
      - { name: userId, type: opaque identifier, required: true, unique: true }
      - { name: email, type: email address, required: true }
      - { name: emailKey, type: normalized email address, required: true, unique: true }
      - { name: displayName, type: text, required: true }
      - { name: registeredAt, type: UTC instant, required: true }
    constraints:
      - One holder exists per userId and one userId owns each emailKey in an environment.
      - Email comparison trims Unicode surrounding whitespace, normalizes NFC, and ignores case; the confirmed email is retained for display.
      - A conflicting emailKey owned by another user is refused; records are never merged.
      - Register the holder only after the wallet is open.
  - name: TransferRequest
    description: Durable idempotency record for the first business result of a caller's keyed transfer.
    attributes:
      - { name: senderUserId, type: opaque identifier, required: true }
      - { name: idempotencyKey, type: opaque text, required: true }
      - { name: fingerprintDigest, type: one-way digest, required: true }
      - { name: outcome, type: non-personal transfer business result or business refusal, required: true }
      - { name: recipientProfileVersionId, type: opaque identifier, required: false, references: WalletHolderProfileVersion.profileVersionId }
      - { name: transferId, type: UUID, required: false, references: Transfer.transferId }
      - { name: createdAt, type: UTC instant, required: true }
    constraints:
      - The composite (senderUserId, idempotencyKey) is unique within an environment.
      - The fingerprint covers API major version, normalized recipient email, and amountHalalas; it contains no raw email.
      - No separately durable pending reservation exists; create the record with its final outcome only.
      - Saved Ledger outcomes contain no recipient email or name. MoneyApi reconstructs the original recipient fields from an immutable WalletDirectory-owned profile version, referenced only by opaque ID; all other replayed business fields, including balanceAfter, are saved unchanged.
      - The first business outcome and fingerprint remain for the environment's lifetime. A key is never reused for another transfer.
  - name: WalletHolderProfileVersion
    description: Immutable WalletDirectory-owned version of a holder profile used to preserve the original recipient display fields on replay.
    attributes:
      - { name: profileVersionId, type: opaque identifier, required: true, unique: true }
      - { name: userId, type: opaque identifier, required: true, references: WalletHolder.userId }
      - { name: email, type: confirmed email address, required: true }
      - { name: displayName, type: text, required: true }
    constraints:
      - WalletDirectory alone owns personal attributes, including immutable versions; Ledger never reads or stores them.
      - Create or ensure a durable immutable version before preparing a transfer outcome reference. Unused versions after a failed attempt contain no transfer record or monetary state.
      - Retain referenced versions for at least the full request-outcome lifetime; changing a current profile never changes an old version.
      - MoneyApi may read a version only for its authenticated caller's saved outcome; a version ID from a request is not authorization.
  - name: Transfer
    description: Completed, all-or-nothing movement of simulated SAR between two wallets.
    attributes:
      - { name: transferId, type: UUID, required: true, unique: true }
      - { name: reference, type: human-readable reference, required: true, unique: true, minLength: 1, maxLength: 64 }
      - { name: senderWalletId, type: opaque identifier, required: true, references: Wallet.walletId }
      - { name: recipientWalletId, type: opaque identifier, required: true, references: Wallet.walletId }
      - { name: amountHalalas, type: positive integer, required: true, min: 100, max: 50000 }
      - { name: completedAt, type: UTC instant, required: true }
    constraints:
      - Only completed transfers are represented; refusals create no transfer or history entry.
      - Sender and recipient differ.
      - Reference is a separate random, short human-readable code, unique across the environment; generate another on collision.
      - A transfer and its two balance changes and successful TransferRequest outcome commit atomically.
  - name: UserConfirmedEventReceipt
    description: Idempotency marker for account-confirmation events received from the same environment.
    attributes:
      - { name: eventId, type: UUID, required: true, unique: true }
      - { name: userId, type: opaque identifier, required: true }
      - { name: environment, type: environment name, required: true, allowed: [dev, stg, prd] }
      - { name: receivedAt, type: UTC instant, required: true }
    constraints:
      - Both eventId and userId are unique within the environment's processed mappings. Atomically claim the first pair after setup; an event ID reused for another user is rejected as conflict.
      - A duplicate pair or later distinct event for an initialized user is a no-op; concurrent consumers converge on the existing user receipt and never credit again.
      - A receipt is accepted only when event environment matches the service environment.
relationships:
  - { from: WalletHolder, to: Wallet, cardinality: one-to-one, direction: WalletHolder.userId -> Wallet.userId }
  - { from: Transfer, to: Wallet, cardinality: many-to-one, direction: senderWalletId and recipientWalletId reference Wallet.walletId }
  - { from: TransferRequest, to: WalletHolderProfileVersion, cardinality: many-to-one, direction: recipientProfileVersionId -> WalletHolderProfileVersion.profileVersionId }
  - { from: TransferRequest, to: Transfer, cardinality: zero-or-one-to-one, direction: transferId -> Transfer.transferId }
  - { from: UserConfirmedEventReceipt, to: Wallet, cardinality: many-to-one, direction: userId -> Wallet.userId }
```

## Entity Summary

Wallet stores only the balance and environment-scoped owner. WalletHolder owns the minimum personal data needed for exact recipient lookup and history names. TransferRequest preserves replayable first outcomes without storing raw email. Transfer contains successful ledger history only. UserConfirmedEventReceipt makes at-least-once event delivery safe.
