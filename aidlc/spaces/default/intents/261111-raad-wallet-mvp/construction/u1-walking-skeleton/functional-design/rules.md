# Business Rules: U1 Walking Skeleton

Conversation language: English.

```yaml
rules:

  # ── Group 1: Sign-in check ─────────────────────────────────────────────────

  - id: BR1.1
    statement: Every money request must carry a valid, unexpired sign-in credential.
    category: authorization
    applies_to: MoneyApi (all endpoints)
    trigger: Any inbound request to a MoneyApi endpoint
    logic: >
      IF the request does not carry a valid credential from the sign-in service,
      or the credential has expired,
      THEN reject the request with an unauthorized error and return no wallet data.
    violation_behaviour: >
      Return 401 Unauthorized. No wallet data, balance, history or transfer result
      is included in the response.
    source: FR1.3, NFR1, AC1.3.4

  - id: BR1.2
    statement: >
      The caller's identity is taken from the verified credential, not from
      a request field.
    category: authorization
    applies_to: MoneyApi (all endpoints)
    trigger: Any authenticated request
    logic: >
      IF a request carries a valid credential,
      THEN the caller's holder_id is extracted from the credential.
      The caller may never override their own identity through a request field.
    violation_behaviour: Ignore any caller-supplied identity field; use the credential only.
    source: FR1.3, NFR1

  # ── Group 2: Wallet setup (safety net) ────────────────────────────────────

  - id: BR2.1
    statement: >
      A confirmed holder receives exactly one wallet with a 100,000 halala
      (1,000.00 SAR) starting balance on their first authenticated money request.
    category: policy
    applies_to: MoneyApi / Ledger (PUT /wallet safety net)
    trigger: >
      An authenticated request to any MoneyApi endpoint where the caller's
      holder_id has no Wallet yet.
    logic: >
      IF the authenticated caller has no Wallet,
      THEN create one Wallet for that holder_id with balance_halalas = 100,000.
      The creation is atomic: concurrent first requests for the same holder_id
      must produce exactly one Wallet, not two.
    violation_behaviour: >
      If a concurrent request races and a Wallet already exists when the create
      is attempted, return the existing Wallet. Do not create a second one.
      Do not add 100,000 halalas to an existing Wallet.
    source: FR1.2 (via ADR-003 safety net), AC1.2.3, AC1.2.4, AC6.4.2

  - id: BR2.2
    statement: >
      If wallet creation fails, the caller receives an error; no partial wallet
      is left behind.
    category: constraint
    applies_to: MoneyApi / Ledger (PUT /wallet safety net)
    trigger: Wallet creation attempt that fails (storage error, timeout, etc.)
    logic: >
      IF a wallet-creation attempt fails before it completes,
      THEN no Wallet record exists for that holder_id after the attempt.
      A retry of the same request is safe and will attempt creation again.
    violation_behaviour: >
      A failed creation must leave no Wallet record. The endpoint returns a
      retriable server error. The caller may retry; on the next attempt, BR2.1
      applies as if the first attempt never happened.
    source: AC1.2.5

  # ── Group 3: Transfer ──────────────────────────────────────────────────────

  - id: BR3.1
    statement: >
      A transfer debits the sender's wallet and credits the recipient's wallet
      atomically; either both happen or neither does.
    category: constraint
    applies_to: Ledger (transfer operation)
    trigger: A valid transfer request
    logic: >
      IF a transfer is requested with a valid sender, recipient and amount,
      THEN the sender's balance_halalas is reduced by amount_halalas AND
      the recipient's balance_halalas is increased by amount_halalas in one
      atomic operation. If the atomic operation cannot complete, neither
      balance changes and no Transfer record is created.
    violation_behaviour: >
      If the atomic operation fails, both balances remain unchanged.
      No Transfer record is written. The caller receives a retriable error.
    source: FR3.1, FR3.4, AC3.1.3, NFR3

  - id: BR3.2
    statement: >
      A transfer is refused when the sender's balance is less than the
      transfer amount.
    category: validation
    applies_to: Ledger (transfer operation)
    trigger: Transfer request where amount_halalas > sender.balance_halalas
    logic: >
      IF amount_halalas > sender.balance_halalas,
      THEN refuse the transfer. The sender's balance and the recipient's
      balance are both unchanged. No Transfer record is created.
    violation_behaviour: >
      Return an insufficient-funds error. Neither balance changes.
      The equal-balance case (amount_halalas == sender.balance_halalas) is
      accepted: the sender's balance becomes 0.
    source: FR3.5, AC3.4.1, AC3.4.2

  - id: BR3.3
    statement: The total money across all wallets never changes as a result of transfers.
    category: constraint
    applies_to: Ledger (all transfer operations)
    trigger: Any transfer attempt (including failures)
    logic: >
      AFTER any transfer operation (success or failure),
      the sum of balance_halalas across all Wallet records must equal
      the sum before the operation.
      This is the property test: for any sequence of transfers, total money
      is conserved and no balance is below zero.
    violation_behaviour: >
      A transfer that would violate conservation (balance below zero, money
      appearing from nowhere) is prohibited by BR3.1 and BR3.2. The property
      test verifies this across random sequences.
    source: FR3.4, AC3.1.4, NFR3

  - id: BR3.4
    statement: >
      A successful transfer response includes both the transfer_id (UUID) and the
      human-readable reference, the sender's new balance, and the recipient's
      display name and email.
    category: policy
    applies_to: MoneyApi (POST /transfers response)
    trigger: Successful transfer
    logic: >
      IF a transfer succeeds,
      THEN the response includes: transfer_id (UUID, opaque), reference (1–64 character
      human-readable string), amount_halalas, the sender's new balance_halalas,
      and the recipient's display_name and email_normalized.
      transfer_id and reference are distinct fields; they must both be present.
    violation_behaviour: >
      Omitting any of these fields is a contract violation (C1 §POST /transfers
      TransferResult schema). transfer_id and reference must both be non-null.
    source: AC3.1.2, contract-summary C1 §TransferResult

  - id: BR3.5
    statement: >
      The review screen shows the recipient's display name, email, the transfer amount in
      SAR, and the sender's projected balance after the transfer.
    category: policy
    applies_to: MobileApp (SendReviewScreen)
    trigger: Recipient resolved and user taps Send on SendFormScreen
    logic: >
      IF a recipient has been resolved and the user proceeds to review,
      THEN the review screen displays: recipient display_name, recipient email_normalized,
      amount in SAR (amount_halalas / 100 formatted to two decimal places), and the
      projected balance = (current balance_halalas - amount_halalas) / 100 SAR.
      The send button is active; no money has moved yet.
    violation_behaviour: >
      Omitting the projected balance or the recipient's email from the review screen
      means the user cannot make an informed confirmation decision (AC3.2.1).
    source: AC3.2.1, contract-summary C1

  - id: BR4.1
    statement: >
      Recipient email lookup normalizes the input before searching, so
      case and surrounding spaces do not affect the result.
    category: validation
    applies_to: WalletDirectory / MoneyApi (POST /recipients/resolve)
    trigger: Recipient lookup by email
    logic: >
      IF a recipient email is supplied,
      THEN normalize it (trim whitespace, lowercase) before comparing against
      email_normalized in WalletHolder. A match returns the holder's
      display_name and holder_id. No match returns a not-found error.
    violation_behaviour: >
      Return a not-found error when no WalletHolder has that normalized email.
      The not-found response must not confirm or deny whether the address
      is registered (safe message).
    source: FR3.1, AC3.5.3, C1 §POST /recipients/resolve

  # ── Group 5: History ───────────────────────────────────────────────────────

  - id: BR5.1
    statement: >
      The transfer history shows only completed transfers for the
      authenticated caller's wallet, ordered newest-first.
    category: authorization
    applies_to: MoneyApi / Ledger (GET /transfers)
    trigger: History request by an authenticated caller
    logic: >
      IF an authenticated caller requests history,
      THEN return only the completed Transfer records where
      sender_wallet_id or recipient_wallet_id equals the caller's wallet_id,
      ordered by completed_at descending. Refused, in-flight or failed
      transfers are never included.
    violation_behaviour: >
      Returning another holder's transfers, or including failed transfers,
      is an authorization violation. Return an empty list rather than data
      from other wallets.
    source: FR4.1, FR4.2, AC4.1.1, AC4.1.2, AC4.1.3

  - id: BR5.2
    statement: >
      Each history entry includes the counterparty's display name and
      email address, the amount, the direction, and the timestamp.
    category: policy
    applies_to: MoneyApi / Ledger (GET /transfers response)
    trigger: Successful history request
    logic: >
      IF a history response is built,
      THEN each Transfer entry includes: transfer_id, reference, amount_halalas,
      direction (sent / received), counterparty display_name, counterparty
      email_normalized, completed_at.
      Names and emails are fetched from WalletDirectory using the counterparty's holder_id.
    violation_behaviour: >
      A missing counterparty name, email or timestamp is a contract violation (C1
      §GET /transfers TransferListItem). Omit the entry rather than return incomplete data.
    source: FR4.1, FR5.3, AC4.1.1, AC4.1.4, contract-summary C1 §TransferListItem

  # ── Group 6: Balance read ──────────────────────────────────────────────────

  - id: BR6.1
    statement: >
      A balance read returns only the authenticated caller's own balance;
      no other wallet's balance is accessible.
    category: authorization
    applies_to: MoneyApi / Ledger (GET /wallet)
    trigger: Balance request by an authenticated caller
    logic: >
      IF an authenticated caller requests their balance,
      THEN return only the balance_halalas of the Wallet whose
      owner_id matches the caller's holder_id.
    violation_behaviour: >
      Returning another wallet's balance is an authorization violation.
      If no Wallet exists yet for the caller, trigger BR2.1 (wallet setup)
      first, then return the new balance.
    source: FR2.1, FR2.2, FR2.4, AC2.1.4
```

## Rules Summary

| ID | Group | Statement | Category | Source |
|---|---|---|---|---|
| BR1.1 | Sign-in check | Every money request must carry a valid credential | Authorization | FR1.3, AC1.3.4 |
| BR1.2 | Sign-in check | Caller identity comes from the credential only | Authorization | FR1.3 |
| BR2.1 | Wallet setup | One wallet per holder, 100,000 halalas on first request | Policy | FR1.2, AC1.2.3–1.2.4 |
| BR2.2 | Wallet setup | Failed creation leaves no partial wallet | Constraint | AC1.2.5 |
| BR3.1 | Transfer | Debit and credit are atomic; all-or-nothing | Constraint | FR3.1, AC3.1.3 |
| BR3.2 | Transfer | Refuse when balance < amount (exact balance accepted) | Validation | FR3.5, AC3.4.1–3.4.2 |
| BR3.3 | Transfer | Total money is conserved across all wallets | Constraint | FR3.4, AC3.1.4 |
| BR3.4 | Transfer | Success response includes transfer_id, reference, new balance, recipient name + email | Policy | AC3.1.2, C1 |
| BR3.5 | Transfer | Review screen shows recipient name, email, amount, and projected balance | Policy | AC3.2.1 |
| BR4.1 | Recipient lookup | Normalize email before lookup; safe not-found message | Validation | FR3.1, AC3.5.3 |
| BR5.1 | History | Show only own completed transfers, newest first | Authorization | FR4.1, AC4.1.1–4.1.3 |
| BR5.2 | History | Each entry includes name, email, amount, direction, timestamp | Policy | FR4.1, C1 |
| BR6.1 | Balance | Return only the caller's own balance | Authorization | FR2.1, AC2.1.4 |

## Sources

- `requirements.md`: FR1.3, FR2.1, FR2.2, FR2.4, FR3.1, FR3.4, FR3.5, FR4.1, FR4.2, FR5.3, NFR1, NFR3
- `stories.md`: AC1.2.3–1.2.5, AC1.3.4, AC2.1.4, AC3.1.2–3.1.4, AC3.4.1–3.4.2, AC3.5.3, AC4.1.1–4.1.4, AC6.4.2
- `contract-summary.md`: C1 OpenAPI (POST /transfers, GET /wallet, GET /transfers, POST /recipients/resolve)
- `unit-of-work.md`: U1 responsibilities (Ledger, WalletDirectory, MoneyApi scope)
- Project rules: ALWAYS store and calculate money as whole halalas
