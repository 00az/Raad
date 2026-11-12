# Frontend Components: U1 Walking Skeleton

Conversation language: English.

U1's MobileApp scope is the sign-in, wallet (balance), send (form → review → result) and history screens, in English only. Arabic, accessibility, and all other screens come in U3. This document describes the component hierarchy, props/state, and interaction flows for the U1 screens only.

---

## Component Hierarchy

```
App
├── AuthGuard                     # wraps all screens; redirects to SignIn if no session
├── SignInScreen                  # US1.3
├── WalletScreen                  # US2.1 — balance and history list
│   └── HistoryList               # US4.1, US4.2
│       └── HistoryEntry          # one completed transfer row
├── SendFlow                      # US3.1, US3.2, US3.4
│   ├── SendFormScreen            # recipient email + amount input
│   ├── SendReviewScreen          # US3.2 — confirm before sending
│   └── SendResultScreen          # US3.1 — reference + new balance on success
└── WalletSetupErrorScreen        # US1.2 AC1.2.5 — wallet creation failed, retry CTA
```

---

## Components

### AuthGuard

**Responsibility:** Checks that a valid session token exists before rendering any protected screen. Redirects to SignInScreen if the token is absent or expired.

**State:** `sessionToken: string | null`

**Behaviour:**
- On mount, reads the stored session token.
- If token is absent or expired: navigate to SignInScreen.
- If token is valid: render the child screen.

**Sources:** BR1.1, AC1.3.4

---

### SignInScreen

**Stories:** US1.3

**Props:** none

**State:**
- `email: string` — controlled input
- `password: string` — controlled input (masked)
- `loading: bool`
- `error: string | null`

**Interaction flow:**
1. User enters email and password; taps **Sign in**.
2. App calls the sign-in service with the credential.
3. **Success:** session token stored; navigate to WalletScreen.
4. **Failure (wrong password, unrecognized email, unconfirmed account):** show the same generic error message in all cases — do not reveal which part was wrong (AC1.3.2, AC1.3.3).
5. **Rate-limited (too many attempts):** show the too-many-attempts message (AC1.3.5). This message is distinct from the wrong-credential message.
6. The screen includes a link that opens the confirmation-code entry screen for any email address. This is reachable even when sign-in fails, so a user with an unconfirmed account can confirm without help (AC1.3.3).

**Form validation:**
- Email: non-empty, valid format.
- Password: non-empty.
- Errors clear when the user edits either field.

---

### WalletScreen

**Stories:** US2.1, US4.1, US4.2

**Props:** none (reads from session)

**State:**
- `balance: { halalas: int, loadedAt: timestamp } | null`
- `balanceError: string | null`
- `balanceLoading: bool`
- `history: HistoryEntry[]`
- `historyLoading: bool`
- `historyError: string | null`

**Interaction flow:**
1. On mount: call `GET /wallet` and `GET /transfers` in parallel.
2. While loading: show a loading indicator for balance and for history list.
3. Balance loaded: display `halalas / 100` formatted to two decimal places (e.g., `1,234.56 SAR`). Never show 0 for a missing wallet — trigger the wallet setup safety net (WF2) server-side; the balance returned is 1,000.00 SAR for a new account (BR2.1).
4. History loaded: show the HistoryList. If empty: show an empty-state message.
5. **Refresh:** tapping the refresh button re-calls both endpoints. Pull-to-refresh is in U3.
6. A received transfer that arrived while the screen was open is not shown until the next refresh (pull-to-refresh is U3).
7. The screen shows a **Send** button that opens SendFlow.

---

### HistoryList / HistoryEntry

**Stories:** US4.1, US4.2

**HistoryList props:** `entries: HistoryEntry[]`, `loading: bool`, `error: string | null`

**HistoryEntry props:**
- `transferId: string`
- `direction: 'sent' | 'received'`
- `counterpartyName: string`
- `amountHalalas: int`
- `completedAt: timestamp`

**Display:**
- Amount: `amountHalalas / 100` formatted to two decimal places.
- Direction: "To [name]" for sent; "From [name]" for received.
- Time: formatted in the device's local timezone (AC4.1.4 — not UTC).
- Order: newest first (BR5.1).

---

### SendFlow

**Stories:** US3.1, US3.2, US3.4

A multi-step flow managed by a navigator. State is owned at the flow level and passed down.

**Flow-level state:**
- `recipientEmail: string`
- `amountHalalas: int | null`
- `resolvedRecipient: { displayName: string, recipientId: string } | null`
- `idempotencyKey: string` — generated once per send attempt (new for each distinct send)
- `submitState: 'idle' | 'submitting' | 'success' | 'error'`
- `errorCode: 'insufficient_funds' | 'server_error' | null`
- `resultTransferId: string | null`
- `resultNewBalanceHalalas: int | null`

#### SendFormScreen

**Interaction flow:**
1. User enters recipient email and amount (in SAR; app converts to halalas before sending).
2. App calls `POST /recipients/resolve` to validate the recipient.
3. **Recipient not found:** show "No RAAD user has that address" (AC3.5.1); keep values in form.
4. **Recipient found:** store `resolvedRecipient`; navigate to SendReviewScreen.
5. The send button is disabled after the first tap (prevents double submission before WF4 returns).

**Form validation:**
- Recipient email: non-empty, valid format; normalized (trim + lowercase) before the API call.
- Amount: must be a positive number representable in halalas (integer number of halalas ≥ 1). Entered in SAR (decimal); converted to `int(amount_SAR * 100)` before the API call.
- Errors clear when the field is edited; values are retained after a refusal (AC3.4.3).

#### SendReviewScreen

**Stories:** US3.2

**Props (from flow state):** `recipientEmail`, `resolvedRecipient.displayName`, `amountHalalas`, `currentBalanceHalalas`

**Display:** Recipient name and email, amount in SAR, projected balance after transfer (`currentBalanceHalalas - amountHalalas`, in SAR) (AC3.2.1).

**Interaction flow:**
1. User reviews the details.
2. **Confirm:** generate a new `idempotencyKey` if none exists for this send attempt; navigate to submitting (see SendFlow submit below).
3. **Back / Do not confirm:** no request is sent; balance is unchanged (AC3.2.2).

#### SendFlow Submit

After the user confirms on SendReviewScreen:
1. Disable the confirm button immediately (prevents a second tap while the request is in flight).
2. Call `POST /transfers` with `recipientEmail` (normalized), `amountHalalas`, `idempotencyKey`.
3. **201 success:** store `resultTransferId` and `resultNewBalanceHalalas`; navigate to SendResultScreen.
4. **422 insufficient funds:** show an error on SendFormScreen with the message; amount and recipient are retained in the form (AC3.4.1, AC3.4.3).
5. **Other error:** show a generic error; amount and recipient are retained; the user may try again.

#### SendResultScreen

**Stories:** US3.1

**Props (from flow state):** `resultTransferId`, `amountHalalas`, `resultNewBalanceHalalas`, `resolvedRecipient.displayName`

**Display:** "Transfer sent" confirmation, transfer reference (`resultTransferId`), amount, recipient name, new balance in SAR (AC3.1.2).

**Navigation:** A "Done" button returns to WalletScreen and triggers a balance refresh.

---

### WalletSetupErrorScreen

**Stories:** US1.2 AC1.2.5

**State:** `retrying: bool`

**Display:** An error message explaining the wallet could not be set up. A **Retry** button.

**Interaction flow:**
1. Shown when WF2 fails (the safety-net wallet creation returned a server error).
2. Tapping **Retry** calls `GET /wallet` again (which re-triggers WF2 server-side).
3. **Success:** wallet is created; navigate to WalletScreen.
4. **Failure:** remain on this screen; button is re-enabled.

---

## API Integration Points

| Component | Endpoint | When |
|---|---|---|
| AuthGuard / SignInScreen | Sign-in service (C3) | Sign-in attempt |
| WalletScreen | `GET /wallet` (C1) | On mount, on refresh |
| WalletScreen | `GET /transfers` (C1) | On mount, on refresh |
| SendFormScreen | `POST /recipients/resolve` (C1) | After email input, before review |
| SendFlow submit | `POST /transfers` (C1) | After review confirmation |

---

## Sources

- `unit-of-work.md` in `inception/units-generation/`: U1 MobileApp scope
- `stories.md`: US1.2, US1.3, US2.1, US3.1, US3.2, US3.4, US4.1, US4.2
- `contract-summary.md` in `inception/contract-design/`: C1 (MoneyApi REST), C3 (sign-in)
- `mockups.md` in `inception/refined-mockups/`: screen layouts (S1–S12; U1 uses S1–S8)
