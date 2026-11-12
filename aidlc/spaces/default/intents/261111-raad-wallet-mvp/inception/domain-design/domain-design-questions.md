# Domain Design: Questions

Conversation language: English.

Domain Design names the building blocks of RAAD, the code the two engineers will write, and says which block owns which piece of data. It does not decide how the blocks are grouped into deployable units (that is Units Generation) or which AWS services they use (later stages). The practices already fix the repos (`Raad`, `RaadMoneyService`, `RaadMobile`, `RaadWeb`) and that `RaadMoneyService` alone changes wallet balances, so those are not asked again.

My working draft, before your answers:

- **MobileApp** (in `RaadMobile`): every screen, the language, the unique request key for each transfer, and what the phone remembers (language, the last known balance, a transfer waiting for a check).
- **MoneyApi** (in `RaadMoneyService`): the one front door of the money service. It checks who is calling, reads the request against the API description, and combines the two blocks below for each use case.
- **Ledger** (in `RaadMoneyService`): the money core. It owns wallets, balances and transfers, and is the only block that changes a balance. It is built test-first.
- **WalletDirectory** (in `RaadMoneyService`): who owns which wallet, by email address and display name, so a sender can find a recipient.
- **LandingPage** (in `RaadWeb`): the static page.
- The shared platform in `Raad` (sign-in, the public API address, the firewall) is **infrastructure**, not one of these blocks. The blocks use it.

Each question below is a choice where more than one design works. The first option is my recommendation, with the reason. The trade in brackets only says whose call it usually is; anyone can answer any question.

## Q1. [Architect] Who creates a user's wallet?

`requirements.md` left this open. The stories need exactly one wallet, with 1,000.00 SAR, by the end of the user's first confirmed sign-in, and a safe retry if creation fails (AC1.2.3 to AC1.2.5).

A. The money service creates the wallet the first time the signed-in user's app asks for it. A repeat of the same request never creates a second wallet or a second 1,000.00 SAR. No other service is involved. (Recommended: nothing can go wrong between two services, and a failed attempt simply repeats on the next open.)
B. The sign-in service calls the money service the moment an account is confirmed. (More moving parts: if the call fails, a confirmed user has no wallet until someone repairs it.)
C. Both: A as the main path and B as a second chance.
X. Other (please specify)

[Answer]: B (**Mode:** chat; the failure case is followed up in Q6)

## Q2. [Architect] How should the money service be split into building blocks?

All of them run in the one money service repo. The split decides where the strictest rules and tests live: the practices require 95% coverage and test-first work for the money-movement core only.

A. Three blocks: MoneyApi (front door and combining), Ledger (balances, transfers, history entries) and WalletDirectory (owner name and email, recipient lookup). Ledger and WalletDirectory do not call each other; MoneyApi combines them. (Recommended: the strictest rules and tests cover only the small Ledger, and nothing hides in an unnamed layer.)
B. One block called WalletService that does everything.
C. Two blocks: MoneyApi and Ledger, with names and emails stored inside each ledger entry.
X. Other (please specify)

[Answer]: A (**Mode:** chat)

## Q3. [Architect] Is the shared platform in `Raad` a building block?

The platform holds the sign-in user pool, the public API address and its mappings, the firewall and rate limits, and the event bus. All of it is configuration written as infrastructure code, with no business rules of its own.

A. No. It is infrastructure that the blocks use, listed as external dependencies. The sign-in rules the stories need (the same refusal for a wrong password and an unconfirmed account, the same message on a code resend) are settings of that infrastructure. (Recommended: the stage defines a building block as code with its own rules and data.)
B. Yes. Model a Platform block that owns sign-in rules, routing and rate limits.
X. Other (please specify)

[Answer]: A (chosen in chat after a clarification; **Mode:** chat)

## Q4. [Architect] Where do the other person's name and email in the history come from?

The history shows, for each transfer, the other person's name and email (AC4.1.1). Names and emails can be copied into each ledger entry when the transfer is made, or looked up when the history is shown.

A. Looked up when the history is shown, from WalletDirectory. The Ledger stores only wallet numbers and amounts. (Recommended: one place holds personal data; the cost is one extra lookup per page.)
B. Copied into each ledger entry at send time. (Faster to read, but personal data is stored twice and cannot be changed in one place.)
X. Other (please specify)

[Answer]: A (**Mode:** chat)

## Q5. [Architect] Should the money service announce completed transfers to other services now?

The platform has a shared event bus for later services such as the AI assistant and Qattah. No story in the MVP needs an announcement.

A. No. Publish nothing in the MVP. Add a "transfer completed" announcement when the first later service needs it, as an additive change. (Recommended: no story needs it, and adding it later breaks nothing.)
B. Yes. Publish a "transfer completed" announcement on every successful transfer from the start.
X. Other (please specify)

[Answer]: A (**Mode:** chat)

## Q6. [Architect] With the sign-in service opening the wallet (Q1 B), what happens when that fails?

Q1 B means the sign-in service asks the money service to open the wallet when the account is confirmed. The money service still does the work, so it stays the only place that changes a balance, and the platform keeps no business rules (Q3 A). One case is not covered: if that request fails, the user is confirmed but has no wallet. The approved story requires that the app then shows an error with a retry, and that the retry ends with exactly one wallet (AC1.2.5). With B alone, the app has nothing to retry, because the account is already confirmed and the sign-in service will not ask again.

A. Keep B as the main path, and add a safety net: when the app asks for a wallet that does not exist, the money service opens it then. Both paths open the wallet by the user's id, so they can never make two wallets or give 1,000.00 SAR twice. This is Q1 option C. (Recommended: keeps the Q1 choice and makes the retry in AC1.2.5 work with no extra process.)
B. Keep B only, with a background retry: a failed request is repeated automatically until it succeeds, and until then the app shows "Your wallet is being set up. Please try again in a minute." AC1.2.5 changes from "the retry creates the wallet" to "the retry checks again".
C. Go back to Q1 A: only the money service opens the wallet, on the app's first request.
X. Other (please specify)

[Answer]: A (**Mode:** chat)
