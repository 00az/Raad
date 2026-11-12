# Architecture Decisions: RAAD Digital Wallet MVP (Domain Design)

Conversation language: English.

These records explain why the building blocks in `components.md` look the way they do. Each one gives the context, the decision, its consequences, the alternatives rejected and its security implications. No regulation applies to the MVP (requirements Q7, answer A), so compliance is not discussed separately. The answers referred to are in `domain-design-questions.md`; the requirement and story IDs are those of `requirements.md` and `stories.md`.

| ADR | Title | Status |
|---|---|---|
| ADR-001 | Split the money service into MoneyApi, Ledger and WalletDirectory | Accepted (Q2 A) |
| ADR-002 | Keep personal data in WalletDirectory and look names up when history is read | Accepted (Q4 A) |
| ADR-003 | Open the wallet at confirmation, with a safety net on a later request | Accepted (Q1 B, Q6 A) |
| ADR-004 | Treat the shared platform as infrastructure, not a building block | Accepted (Q3 A) |
| ADR-005 | Announce nothing on the shared event bus in the MVP | Accepted (Q5 A) |
| ADR-006 | Keep the transfer and its request key in one all-or-nothing change inside the Ledger | Proposed: decided in this stage without a question, to confirm at the gate |
| ADR-007 | Send every account action from the app straight to the sign-in service | Proposed: decided in this stage without a question, to confirm at the gate |

All records are dated 2026-11-11.

---

## ADR-001: Split the money service into MoneyApi, Ledger and WalletDirectory

**Status:** Accepted (Q2, answer A).

### Context

`RaadMoneyService` holds wallets, balances, transfers, history and the lookup of people by email (`team-practices.md`). The practices require test-first work and at least 95% line and branch coverage for the money-movement core only. Personal data must be limited to the email address and display name (NFR11) and kept out of logs (NFR10). A transfer must change two balances together or not at all (FR3.4).

### Decision

The money service has three building blocks:

- **MoneyApi** is the only way in. It checks the caller and the request, and combines the other two blocks.
- **Ledger** owns wallets, balances, transfers and request keys. It is the only block that changes a balance.
- **WalletDirectory** owns each holder's email address and display name, and finds a holder by email or by user id.

Ledger and WalletDirectory never call each other; MoneyApi combines them.

### Consequences

- Positive: the strictest rules and tests apply to a small Ledger that has no web, identity or personal-data code.
- Positive: the all-or-nothing transfer touches only the Ledger's data, so no change has to span two blocks.
- Positive: personal data sits in one block.
- Negative: MoneyApi makes two calls for a send (find the recipient, then transfer) and for a history page (read the page, then add names).
- Negative: opening a wallet touches two blocks, so the setup order in ADR-003 is needed.

### Alternatives Rejected

- **One WalletService block (Q2 B).** Simpler at first, but money rules, personal data and web concerns would mix. The 95% floor and test-first work would then cover the whole service, or rely on an inner line nobody named.
- **Two blocks, with names and emails stored in each ledger entry (Q2 C).** One fewer lookup, but personal data would sit in the money core and be copied into every transfer, where it cannot be corrected in one place.

### Security

A leak of Ledger data exposes amounts and opaque user ids only. MoneyApi is the single place that decides who may act on which wallet, so authorization has one place to review and test (FR2.4, FR5.6, NFR1).

---

## ADR-002: Keep personal data in WalletDirectory and look names up when history is read

**Status:** Accepted (Q4, answer A).

### Context

Each history entry shows the other person's name and email (AC4.1.1). Every send needs a lookup by email (FR3.1). The sign-in service already holds each user's email address and display name.

### Decision

- WalletDirectory keeps a copy of each user's email address and display name, written once at wallet setup from the verified sign-in. The sign-in service stays the source of truth.
- The Ledger stores only wallet ids, opaque user ids and amounts.
- A history page is read from the Ledger, and MoneyApi adds the other parties' names and emails from WalletDirectory in one batch lookup.

### Consequences

- Positive: personal data has one home in the money service, which makes it easy to protect now and to erase later.
- Negative: each history page costs one extra batch lookup (one per page of 20 entries).
- Negative: a copy of the sign-in service's data exists. The MVP has no way to change an email address or display name, so the copy cannot go stale; any later profile edit must update it.

### Alternatives Rejected

- **Copy names and emails into each ledger entry at send time (Q4 B).** Faster reads, but personal data in the money core and in every transfer.
- **Ask the sign-in service for every lookup, with no copy.** No duplicated data, but every send and history page would depend on the sign-in service's administration interface and its request limits, and the money service would need administrator rights over user accounts.

### Security

A lookup by email returns only an exact match of the whole address, never a list or a partial match. This limits what assumption A13 reveals, and the platform rate-limits lookups per caller (AC3.5.4).

---

## ADR-003: Open the wallet at confirmation, with a safety net on a later request

**Status:** Accepted (Q1, answer B; follow-up Q6, answer A).

### Context

Every confirmed user must have exactly one wallet with 1,000.00 SAR by the end of their first confirmed sign-in. If opening fails, the app must show an error with a retry, and the retry must end with exactly one wallet (FR1.5, AC1.2.3 to AC1.2.5). The person chose that the sign-in service starts the opening when an account is confirmed (Q1 B). On its own, that leaves a confirmed user with no wallet and nothing to retry when the opening fails (Q6).

### Decision

MoneyApi has one wallet-setup procedure that is safe to run any number of times for the same user. It has two triggers:

1. The sign-in service's account-confirmed signal.
2. Any signed-in request from a user who has no WalletDirectory entry yet (the safety net).

The procedure opens the wallet in the Ledger first, then registers the holder in WalletDirectory:

- The Ledger opens at most one wallet per user id and credits the opening balance only on the first opening.
- The email address and display name come from the sign-in service, never from the body of a request.
- The confirmation signal never makes the user's confirmation fail. A failed setup is logged and completed by the safety net.

The money service still does all the work, so it stays the only service that changes a balance (`team-practices.md`).

### Consequences

- Positive: the wallet usually exists before the user first signs in.
- Positive: any failure heals on the user's next request, which is the retry AC1.2.5 asks for.
- Positive: a holder found by email always has an open wallet, because the holder is registered second.
- Negative: two entry points to secure and test.
- Negative: the sign-in service in `Raad` must reach MoneyApi in `RaadMoneyService`, while the practices deploy `Raad` first. How that is wired is an open question for infrastructure design.
- Negative: a confirmed user whose setup failed cannot receive money until their next signed-in request (see `components.md`, Assumptions & Open Questions).

### Alternatives Rejected

- **The money service opens the wallet on the first request only (Q1 A).** The simplest design, but the person chose to open at confirmation.
- **The sign-in service at confirmation only (Q1 B alone).** Leaves a confirmed user with no wallet and no retry, which breaks AC1.2.5.
- **A background retry until it works (Q6 B).** Keeps one trigger, but needs a retry queue and a "being set up" state, and changes AC1.2.5.
- **The sign-in side opens the wallet itself.** The platform would then change balances, which breaks the rule that only the money service does.

### Security

- The confirmation entry point accepts calls only from the sign-in service and is never reachable through the public API address. Anyone else able to call it could open wallets holding 1,000.00 SAR each.
- The safety net opens a wallet only for the caller named in the verified sign-in.
- If an email address is already held by a different user id, registration is refused and reported, never merged.

---

## ADR-004: Treat the shared platform as infrastructure, not a building block

**Status:** Accepted (Q3, answer A).

### Context

`Raad` holds the sign-in user pool, the public API address and its path mappings, the firewall and rate limits, and the event bus, all as infrastructure code (`team-practices.md`). None of it has business rules or data of its own.

### Decision

The platform appears in `components.md` only as external dependencies. The sign-in behaviours the stories need are settings of the sign-in service:

- the same refusal for a wrong password and an unconfirmed account (AC1.3.2, AC1.3.3);
- the password rule (A4) and the session lengths (A5);
- the code resend that shows the same message for any address (AC1.2.6);
- the rate limits on sign-in and recipient lookups (AC1.3.5, AC3.5.4).

### Consequences

- Positive: the catalogue holds only code with business rules, which makes the real rules easy to find.
- Positive: Units Generation still gives the platform a unit of its own, and infrastructure design designs it.
- Negative: the sign-in behaviours are not visible as a block. They are listed here and in each story, and checked by the platform's smoke test and the app's integration tests.

### Alternatives Rejected

- **A Platform block that owns sign-in rules, routing and rate limits (Q3 B).** It would own no entities and no logic of its own, and would blur the line between code the team writes and infrastructure it deploys.
- **Each service runs its own sign-in and routing.** It would contradict the practices, which require one shared user pool and one API domain, and every user would need an account per service.

### Security

The sign-in protections (no account enumeration, rate limits, the password rule) live in one place, the sign-in service's settings, which infrastructure design reviews.

---

## ADR-005: Announce nothing on the shared event bus in the MVP

**Status:** Accepted (Q5, answer A).

### Context

The platform provides an event bus for later services such as the AI assistant and Qattah. No MVP story needs an announcement.

### Decision

No block publishes or subscribes in the MVP. A "transfer completed" announcement is added as an additive change when the first later service needs it.

### Consequences

- Positive: less to build and test now, and no event contract to version before anyone uses it.
- Negative: the AI assistant will need either the announcement or a new read endpoint before it can work. That is planned with it.

### Alternatives Rejected

- **Publish a "transfer completed" announcement from the start (Q5 B).** Work with no consumer, and an event contract fixed before its first user exists.
- **Let later services read the Ledger's data store directly.** It breaks data ownership and the practice that other services ask `RaadMoneyService` for anything to do with money.

### Security

In the MVP, transfer data leaves the money service only through MoneyApi's checked responses.

---

## ADR-006: Keep the transfer and its request key in one all-or-nothing change inside the Ledger

**Status:** Proposed. This was decided in this stage without a question; confirm it at the gate.

### Context

- A transfer must move money from one wallet to another all or nothing (FR3.4).
- Simultaneous transfers must never overdraw a wallet (FR3.8).
- A repeated request key must return the first result and move money once (FR3.7).
- Refused transfers must not appear in the history (FR5.4).

### Decision

The Ledger owns two entities:

- **Transfer**, a completed movement of money.
- **TransferRequest**, one record per sender and request key, holding the request's details and its first outcome.

Checking the rules, recording the TransferRequest, changing both balances and recording the Transfer happen in one all-or-nothing change of the Ledger's own data. A refused request is recorded only as a TransferRequest, never as a Transfer.

### Consequences

- Positive: no failure can move money without recording the key, or record the key without moving the money.
- Positive: the history reads only Transfers, so a refusal cannot leak into it.
- Positive: the replay and concurrency tests the practices require test one block.
- Negative: the Ledger's data store must support an all-or-nothing change across several records with a condition on the balance. This is a requirement on the store chosen in infrastructure design.

### Alternatives Rejected

- **Keep request keys in MoneyApi.** The key check and the money movement would be two separate changes, and a failure between them could move money twice or not at all.
- **Store refused requests as Transfers with a status.** The history would have to filter them, and one missed filter would show refusals.

### Security

Replaying a captured request cannot move money again, and a key reused with different details is refused (AC3.6.4).

---

## ADR-007: Send every account action from the app straight to the sign-in service

**Status:** Proposed. This was decided in this stage without a question; confirm it at the gate.

### Context

Sign-up, confirmation, code resend, sign-in, sign-out, session renewal and password reset all need the sign-in service. Passwords and tokens must never reach logs (NFR10). The approved screens S1 to S5 are drawn as app screens (`mockups.md`).

### Decision

MobileApp calls the sign-in service directly for every account action. MoneyApi never receives a password; it receives only the sign-in token, which it verifies on every request.

### Consequences

- Positive: the money service never handles passwords.
- Positive: the sign-in service's own protections apply unchanged.
- Negative: the app depends on two back ends (the sign-in service and MoneyApi) and must handle the errors of each.
- Negative: part of the account screens' behaviour is configuration of the sign-in service (ADR-004).

### Alternatives Rejected

- **Route account actions through MoneyApi.** One back end for the app, but passwords would pass through the money service and could reach its logs, and the money service would rebuild protections the sign-in service already has.
- **Use the sign-in service's hosted web pages in a browser view.** Less app code, but the pages would not match the approved native screens and would need their own Arabic and right-to-left work.

### Security

Passwords travel only between the phone and the sign-in service, over TLS (NFR2). Tokens are kept only in the phone's secure storage (`components.md`, MobileApp).
