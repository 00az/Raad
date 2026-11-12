# User Stories: RAAD Digital Wallet MVP

Conversation language: English.

Stories are derived from `requirements.md` (FR1 to FR8, NFR1 to NFR15) and follow the plan answered in `user-stories-questions.md`: grouped by user journey (Q4), medium size (Q5), prioritised as Q6 describes, with build, deploy and monitoring requirements written as stories only where a person sees the result (Q7). The team's testing, deployment and code practices in `team-practices.md` shape the acceptance criteria. Personas are in `personas.md`.

## Decisions That Shape These Stories

The person confirmed the assumptions in `requirements.md` on the plan's Q1 and Q2 (both answered A). The stories therefore treat these as confirmed:

- Only completed transfers appear in the history; a refused transfer leaves no entry (A2).
- Sending needs a network connection (A6).
- The app shows a confirmation screen before sending (A11).
- The app creates the unique key for each transfer (A12).
- Sign-up and recipient lookup may reveal whether an email is registered, limited by rate limits (A13).
- Forgotten passwords are reset by an emailed code (A3), with the password rule in A4 and the session lengths in A5.

Three other assumptions in `requirements.md` were not put to the person and stay **unconfirmed**; the stories that rely on them say so:

- A8: amounts and dates use Western digits, and amounts are labelled "SAR" in English and "ر.س" in Arabic (relied on by AC5.1.4).
- A9: the landing page holds a name, a short description and where to get the app (relied on by US6.3).
- A10: the 1,000.00 SAR starting balance is also given in `prd` (relied on by AC6.4.2).

Terms used below. A **halala** is 1/100 of a SAR. The **starting balance** is 1,000.00 SAR. The **limits** are 1.00 SAR at least and 500.00 SAR at most per transfer, with no daily total.

## Walking Skeleton

The first slice is built and proven on `dev` before other stories start (see `team-practices.md`, Walking Skeleton). It is made of **US1.1, US1.2, US1.3, US2.1, US3.1 and US4.1**, and **US6.1** is the check that it works end to end. Sign-up, confirmation and sign-in are all in it because a test user cannot sign in without an account.

## Story Map

| Group | Journey step | Stories |
|---|---|---|
| US1 | Sign up and sign in | US1.1, US1.2, US1.3, US1.4, US1.5, US1.6 |
| US2 | See my balance | US2.1, US2.2 |
| US3 | Send money | US3.1, US3.2, US3.3, US3.4, US3.5, US3.6, US3.7, US3.8, US3.9 |
| US4 | Receive and review | US4.1, US4.2, US4.3, US4.4 |
| US5 | Language and accessibility | US5.1, US5.2, US5.3 |
| US6 | Running on AWS | US6.1, US6.2, US6.3, US6.4 |

## Priority Summary

| Priority | Stories |
|---|---|
| Must Have | US1.1, US1.2, US1.3, US1.4, US2.1, US3.1, US3.2, US3.3, US3.4, US3.5, US3.6, US3.7, US3.8, US3.9, US4.1, US4.2, US4.3, US6.1, US6.2, US6.4 |
| Should Have | US1.5, US1.6, US2.2, US4.4, US5.1, US5.2, US5.3 |
| Could Have | US6.3 |
| Won't Have (this time) | Everything under Out of Scope in `requirements.md`: real payments, top-up, requests for money, QR codes, push notifications, a daily limit, multi-factor sign-in, regulatory alignment, admin tools, refunds, account deletion, store release. |

The MVP boundary is decided in Delivery Planning; these priorities inform it. Twenty Must Have stories are the SOW's six success criteria and the rules that protect them. There are 28 stories in all: 20 Must Have, 7 Should Have and 1 Could Have.

---

## US1 Sign up and sign in

### US1.1 Sign up

**As a** Wallet User, **I want** to create an account with my email address, a display name and a password, **so that** I can have a wallet of my own.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR1.1, FR1.6, NFR11
- **Depends on:** none
- **Walking skeleton:** yes
- **Acceptance criteria:**
  - **AC1.1.1** Given the sign-up form, when I enter a valid email address, a display name and the password `Abcdef12`, then an unconfirmed account exists and a one-time code is emailed to that address.
  - **AC1.1.2** Given an account already exists for `a@x.com`, when I sign up with ` A@X.com ` (different case and surrounding spaces), then sign-up is refused with a message that the address is already in use and no second account is made.
  - **AC1.1.3** Given the sign-up form, when I enter a password that breaks the rule (`abcdef12`, `ABCDEF12`, `Abcdefgh` or `Abcde12`), then sign-up is refused with a message that names the rule, and the email and display name I typed are still in the form.
  - **AC1.1.4** Given a successful sign-up, then the only personal data stored about me is my email address and display name (no identity document, card or bank detail is asked for).
- **INVEST:** Independent of other stories; small (one form, one rule set); testable through the sign-up API and one widget test.

### US1.2 Confirm my email and get my wallet

**As a** Wallet User, **I want** to confirm my email address with the code I was sent, **so that** my account is activated and my wallet is ready to use.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR1.2, FR1.5
- **Depends on:** US1.1
- **Walking skeleton:** yes
- **Acceptance criteria:**
  - **AC1.2.1** Given an unconfirmed account, when I enter the correct code, then the account is confirmed.
  - **AC1.2.2** Given an unconfirmed account, when I enter a wrong or expired code, then the account stays unconfirmed and the app says the code is not valid.
  - **AC1.2.3** Given I sign in for the first time after confirming, then I have exactly one wallet in SAR with a balance of 1,000.00 SAR.
  - **AC1.2.4** Given I confirm and sign in again, or the first sign-in is retried, then I still have one wallet and the balance is not credited a second time.
  - **AC1.2.5** Given wallet creation fails at my first sign-in, then the app shows an error with a retry and no wallet screen, and the retry ends with exactly one wallet.
  - **AC1.2.6** (added at Refined Mockups on the person's instruction, Q5 option B) Given an unconfirmed account whose code has expired or been lost, when I choose "Send the code again" on the confirmation screen, then a new code is emailed to that address, the old code stops working, and the screen shows the same message whether or not the address is registered, so it does not reveal which addresses exist. Resends are limited by the same rate limit as sign-in.
- **INVEST:** Depends only on US1.1; small; testable with a forced wallet-creation failure and a repeated first sign-in.

### US1.3 Sign in

**As a** Wallet User, **I want** to sign in with my email address and password, **so that** only I can reach my wallet.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR1.3, NFR1
- **Depends on:** US1.2
- **Walking skeleton:** yes
- **Acceptance criteria:**
  - **AC1.3.1** Given a confirmed account, when I enter the correct email address and password, then the app opens my wallet.
  - **AC1.3.2** Given a confirmed account, when I enter a wrong password, or an email with no account, then sign-in is refused with the same message in both cases, which does not say which part was wrong.
  - **AC1.3.3** Given an unconfirmed account, when I try to sign in with the correct password, then sign-in is refused with exactly the same message as in AC1.3.2, so the refusal does not reveal that the password was right. The screen for entering the emailed code is reachable from the sign-in screen for any email address, so a user with an unconfirmed account can still confirm it. (This resolves FR1.3 against FR1.2; Refined Mockups shows the entry point for the person to confirm.)
  - **AC1.3.4** Given I am not signed in, or my sign-in has expired, when a request for any wallet data is made, then it is refused and no wallet data is returned.
  - **AC1.3.5** Given more sign-in attempts from one caller than the rate limit allows in a short time, when I try again, then further attempts are refused while other callers are unaffected.
- **INVEST:** Small; testable through the API and a widget test; the rate-limit criterion is checked on `stg`.

### US1.4 Sign out

**As a** Wallet User, **I want** to sign out, **so that** nobody who picks up my phone can see my wallet.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR1.4
- **Depends on:** US1.3
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC1.4.1** Given I am signed in, when I choose sign out, then the app shows the sign-in screen.
  - **AC1.4.2** Given I have signed out, when I use the back gesture or reopen the app, then no balance or history is shown until I sign in again.
- **INVEST:** Small, independent of the money stories, testable with one integration test.

### US1.5 Reset a forgotten password

**As a** Wallet User, **I want** to reset my password with a code sent to my email address, **so that** I can get back into my wallet if I forget it.

- **Priority:** Should Have
- **Persona:** Wallet User (P1)
- **Requirements:** A3 and A4 in `requirements.md` (confirmed on Q2; no FR or NFR row of its own)
- **Depends on:** US1.2
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC1.5.1** Given a confirmed account, when I ask for a reset and enter the emailed code and a new password that follows the rule, then my password changes, the old password no longer signs me in and the new one does.
  - **AC1.5.2** Given I enter a wrong or expired code, then my password does not change and the app says the code is not valid.
  - **AC1.5.3** Given I enter a new password that breaks the rule, then the reset is refused with a message that names the rule.
- **INVEST:** Independent once an account exists; small; testable through the sign-in service.

### US1.6 Stay signed in

**As a** Wallet User, **I want** the app to keep me signed in while I use it regularly, **so that** I am not asked for my password every time I open it.

- **Priority:** Should Have
- **Persona:** Wallet User (P1)
- **Requirements:** A5 in `requirements.md` (confirmed on Q2; no FR or NFR row of its own)
- **Depends on:** US1.3
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC1.6.1** Given I signed in, when I use the app 61 minutes later (test clock), then the app renews my session without showing the sign-in screen.
  - **AC1.6.2** Given I last used the app 31 days ago (test clock), when I open it, then the app shows the sign-in screen.
- **INVEST:** Small; testable with a controllable clock.

---

## US2 See my balance

### US2.1 See my balance

**As a** Wallet User, **I want** to see the current balance of my wallet in SAR, **so that** I know how much I can send.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR2.1, FR2.2, FR2.4, NFR1
- **Depends on:** US1.2, US1.3
- **Walking skeleton:** yes
- **Acceptance criteria:**
  - **AC2.1.1** Given my wallet holds 123,456 halalas, when I open the app, then the balance is shown as 1,234.56 SAR.
  - **AC2.1.2** Given a new wallet, when I open the app, then the balance is 1,000.00 SAR.
  - **AC2.1.3** Given a transfer of N halalas from me to another user, when I look at my balance and the other user looks at theirs, then mine is lower by N, theirs is higher by N and no other balance changes.
  - **AC2.1.4** Given I am signed in, when a request is made for another user's wallet, then it is refused and returns no data about that wallet.
  - **AC2.1.5** Given any amount in the app, the service and the data store, then it is a whole number of halalas and never a decimal or floating-point value.
- **INVEST:** Small; testable by API calls and a property test over balance arithmetic.

### US2.2 See when my balance may be out of date

**As a** Wallet User, **I want** the app to tell me when the balance it shows is old, **so that** I do not trust a number that may be wrong.

- **Priority:** Should Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR2.3
- **Depends on:** US2.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC2.2.1** Given the balance loaded earlier and the network is now off, when I open the wallet, then the app shows the old balance with an "out of date" mark and the time it was last updated, and offers a retry.
  - **AC2.2.2** Given the balance has never loaded, when the network is off, then the app shows an error with a retry, not a zero or a blank balance.
  - **AC2.2.3** Given the network comes back, when I retry, then the balance refreshes and the mark disappears.
- **INVEST:** Small; testable by switching the network off in a widget or integration test.

---

## US3 Send money

### US3.1 Send money to another RAAD user

**As a** Wallet User, **I want** to send simulated SAR to another RAAD user by their email address, **so that** they receive the money right away.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.1, FR3.4, FR3.11, FR2.2, NFR3
- **Depends on:** US2.1
- **Walking skeleton:** yes
- **Acceptance criteria:**
  - **AC3.1.1** Given I have 1,000.00 SAR and a registered user at `b@x.com` has 1,000.00 SAR, when I send 100.00 SAR to `b@x.com`, then my balance is 900.00 SAR and theirs is 1,100.00 SAR.
  - **AC3.1.2** Given the transfer succeeded, then the app shows a confirmation with the amount, the recipient, a reference and my new balance.
  - **AC3.1.3** Given any step of a transfer fails, then both balances are unchanged and no history entry is created.
  - **AC3.1.4** Given any sequence of transfers among any set of wallets, then the total money across all wallets stays the same apart from starting balances, and no balance is below zero.
- **INVEST:** The first money story, built test-first in the money core; small once the other rules are separate stories; testable by API, property and widget tests.

### US3.2 Review and confirm before sending

**As a** Wallet User, **I want** to see who I am paying and how much before the money moves, **so that** a mistyped address does not send money to a stranger.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.3
- **Depends on:** US3.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.2.1** Given I entered a registered recipient and an amount, when I tap send, then a confirmation screen shows the recipient's name and email, the amount and my balance after the transfer.
  - **AC3.2.2** Given the confirmation screen, when I do not confirm, then no transfer request is sent and no balance changes.
  - **AC3.2.3** Given the confirmation screen, when I confirm, then the transfer is sent once.
- **INVEST:** Small; testable with a widget test that checks no request leaves before confirmation.

### US3.3 Stay within the amount limits

**As a** Wallet User, **I want** the app to keep each transfer between 1.00 and 500.00 SAR, **so that** one slip cannot move a large part of my balance.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.2, FR3.12
- **Depends on:** US3.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.3.1** Given an amount of 100 halalas (1.00 SAR) or 50,000 halalas (500.00 SAR), when I send it, then the transfer is accepted.
  - **AC3.3.2** Given an amount of 99 halalas, 50,001 halalas, zero, a negative amount, or an amount with a fraction of a halala, when I try to send it, then it is refused with a message that names the limits.
  - **AC3.3.3** Given two transfers of 400.00 SAR on the same day, when I send them, then both are accepted because there is no daily total.
  - **AC3.3.4** Given a refusal, then the amount and recipient I typed are still in the form.
- **INVEST:** Small; boundary values make it testable at the API and in the form.

### US3.4 Be stopped when my balance is too low

**As a** Wallet User, **I want** a transfer that is larger than my balance to be refused, **so that** my wallet never goes below zero.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.5, FR3.12
- **Depends on:** US3.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.4.1** Given a balance of 300.00 SAR, when I send 300.01 SAR, then the transfer is refused with a message that my balance is too low and both balances are unchanged.
  - **AC3.4.2** Given a balance of 300.00 SAR, when I send 300.00 SAR, then the transfer is accepted and my balance is 0.00 SAR.
  - **AC3.4.3** Given a refusal, then the history is unchanged and the amount and recipient I typed are still in the form.
- **INVEST:** Small; testable at the boundary.

### US3.5 Be stopped when the recipient is not valid

**As a** Wallet User, **I want** the app to tell me when the recipient does not exist or is me, **so that** I do not waste a transfer or send money to myself.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.1, FR3.6, FR3.12, A13
- **Depends on:** US3.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.5.1** Given an email address that no RAAD user has registered, when I try to send to it, then the app says no RAAD user has that address and no transfer is made.
  - **AC3.5.2** Given my own email address, when I try to send to it, then the transfer is refused with a message and nothing changes.
  - **AC3.5.3** Given a recipient email typed with different capitals or surrounding spaces, when I send, then it finds the same user as the registered address. (This applies the case and space rule of FR1.6 to the recipient lookup in FR3.1. `requirements.md` states it only for sign-up, so this is a clarification the person can reverse.)
  - **AC3.5.4** Given more recipient lookups from one caller than the rate limit allows in a short time, then further lookups are refused while other callers are unaffected.
- **INVEST:** Small; A13 (email lookup may reveal that an address is registered) is accepted and limited by AC3.5.4.

### US3.6 Never send the same transfer twice

**As a** Wallet User, **I want** a repeated request to move my money only once, **so that** a double tap or a retry never charges me twice.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.7, FR3.9, NFR4
- **Depends on:** US3.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.6.1** Given a transfer request with a unique key, when the same request is sent a second time, one after the other, then the service returns the first result, the balances change once and one history entry exists.
  - **AC3.6.2** Given the same request is sent twice at the same moment, then the balances change once and both calls return the same result.
  - **AC3.6.3** Given I tap send twice before the result arrives, then the app sends one request, or two requests with the same key, and the balances change once.
  - **AC3.6.4** Given a new transfer, then the app creates a new unique key for it, so two separate transfers of the same amount to the same person are both made.
- **INVEST:** Built test-first in the money core; testable with replay and concurrency tests on a real local data-store container.

### US3.7 Never overdraw with simultaneous transfers

**As a** Wallet User, **I want** two transfers made at the same moment to be safe, **so that** my wallet cannot go below zero even if I use two phones.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.8, NFR3, NFR4
- **Depends on:** US3.4
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.7.1** Given a balance of 500.00 SAR, when two transfers of 300.00 SAR to different recipients are sent at the same moment, then one succeeds, one is refused for a low balance, and my balance is 200.00 SAR.
  - **AC3.7.2** Given many simultaneous transfers among the same wallets, then no balance goes below zero and the total money is unchanged.
- **INVEST:** Test-first in the money core; testable by a concurrency test against a real data-store container, not a mock.

### US3.8 Know what happened when the answer is lost

**As a** Wallet User, **I want** the app to tell me honestly when it cannot tell whether my transfer went through, **so that** I check before trying again and do not lose track of my money.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR3.10
- **Depends on:** US3.6
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.8.1** Given the response to a transfer times out or the connection drops, then the app says it could not confirm the transfer and tells me to check my history before trying again.
  - **AC3.8.2** Given the app offers a retry after such a loss, when I retry, then it reuses the same key, and the result is the original success or one fresh success, never two transfers.
  - **AC3.8.3** Given a lost response for a transfer that did go through, when I open my history, then it contains the transfer once.
- **INVEST:** Small once US3.6 exists; testable by cutting the connection in an integration test.

### US3.9 Not send while offline

**As a** Wallet User, **I want** the send button to be off when the app has no connection, **so that** I never queue a transfer I cannot see the result of.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR6.4
- **Depends on:** US3.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC3.9.1** Given the network is off, when I open the send screen, then the send button is off and a message says why.
  - **AC3.9.2** Given the network comes back, then the send button turns on again without restarting the app.
- **INVEST:** Small; testable in a widget test.

---

## US4 Receive and review

### US4.1 See my transfer history

**As a** Wallet User, **I want** to see a list of the transfers I sent and received, **so that** I can check what happened to my money.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR5.1, FR5.2, FR5.4, FR5.6, NFR1, NFR15
- **Depends on:** US3.1
- **Walking skeleton:** yes
- **Acceptance criteria:**
  - **AC4.1.1** Given a completed transfer, then it appears on both users' histories, as "sent" for the sender and "received" for the recipient, with the other person's name and email, the same amount, the date and time, and the same reference.
  - **AC4.1.2** Given several entries, then they are listed newest first, entries made at the same moment have a fixed order, and reloading never changes the order.
  - **AC4.1.3** Given a refused transfer, then my history is unchanged.
  - **AC4.1.4** Given I am signed in, when a request is made for another user's history, then it is refused and returns no data.
  - **AC4.1.5** Given a transfer made at 23:30 in Riyadh, then a phone set to Riyadh time shows 23:30 and a phone in another time zone shows the same instant in its own time.
- **INVEST:** Small; testable by API and widget tests.

### US4.2 See money I have received

**As a** Wallet User, **I want** my balance and history to show money that someone sent me when I open the app or refresh, **so that** I can see it has arrived.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR4.1, FR4.2
- **Depends on:** US4.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC4.2.1** Given someone sends me 50.00 SAR, when I open the app or pull down to refresh, then my balance is 50.00 SAR higher and a "received" entry appears in my history.
  - **AC4.2.2** Given I leave the app open and idle, then it does not refresh by itself and I receive no push notification.
- **INVEST:** Small; testable with two test users.

### US4.3 Load a long history page by page

**As a** Wallet User, **I want** a long history to load a page at a time, **so that** the app stays quick however many transfers I have made.

- **Priority:** Must Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR5.3
- **Depends on:** US4.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC4.3.1** Given 1,000 entries, when I open the history, then the first page appears promptly and more load when I ask.
  - **AC4.3.2** Given I load page after page, then no entry is skipped or shown twice, even if a new transfer arrives between pages.
- **INVEST:** Small; testable with a seeded history.

### US4.4 See a clear message when there is nothing to show

**As a** Wallet User, **I want** an empty history to say so and a failed load to say it failed, **so that** I know whether I have no transfers or something went wrong.

- **Priority:** Should Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR5.5
- **Depends on:** US4.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC4.4.1** Given a new account with no transfers, then the history shows "no transfers yet".
  - **AC4.4.2** Given the history fails to load, then the app shows an error with a retry, not "no transfers yet".
- **INVEST:** Small; testable in a widget test.

---

## US5 Language and accessibility

### US5.1 Use the app in Arabic or English

**As a** Wallet User, **I want** to use the app in Arabic or English and switch between them, **so that** I can read it in the language I prefer.

- **Priority:** Should Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR6.1
- **Depends on:** US1.3
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC5.1.1** Given the app in Arabic, then every screen is laid out right to left with no clipped text.
  - **AC5.1.2** Given the app in English, then every screen is laid out left to right.
  - **AC5.1.3** Given I switch language in the app, then the change takes effect at once without signing in again.
  - **AC5.1.4** (depends on unconfirmed assumption A8; confirm it before building this) Given amounts and dates in both languages, then they use Western digits (0 to 9) and the amount is labelled "SAR" in English and "ر.س" in Arabic.
- **INVEST:** Spans every screen but can be delivered after the Must stories; testable by screenshot and widget tests in both directions.

### US5.2 Use the app with a screen reader and larger text

**As a** Wallet User who needs assistive tools, **I want** the sign-in, wallet and send screens to work with a screen reader and larger text, **so that** I can use my wallet independently.

- **Priority:** Should Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR6.3
- **Depends on:** US1.3, US2.1, US3.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC5.2.1** Given a screen reader on iOS and on Android, then a person can sign in, read the balance and send a transfer using only the reader.
  - **AC5.2.2** Given system text at 200%, then every control on those screens is still visible and usable.
  - **AC5.2.3** Given a status such as an error or "out of date", then it is shown with text or an icon and not by colour alone.
- **INVEST:** Verified by a manual walk-through on both platforms.

### US5.3 See a loading, empty or error view on every data screen

**As a** Wallet User, **I want** each screen that loads data to show whether it is loading, empty or failed, **so that** I always know what is happening.

- **Priority:** Should Have
- **Persona:** Wallet User (P1)
- **Requirements:** FR6.2
- **Depends on:** US2.1, US4.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC5.3.1** Given the balance screen, then it shows separate loading, error and loaded views under the matching conditions.
  - **AC5.3.2** Given the history screen, then separate loading, empty and error views exist and each appears under its matching condition. The wording and retry behaviour of the history empty and error views are specified once, in US4.4 (and the balance's in US2.2); this story only checks that every data screen has the three views.
- **INVEST:** Small; testable in widget tests.

---

## US6 Running on AWS

### US6.1 Check the whole journey on `dev`

**As a** Demo Reviewer, **I want** to sign in on a phone, see a SAR balance, send one transfer to another RAAD wallet and see it in the history, all against the `dev` environment on AWS, **so that** I can confirm the first slice works end to end.

- **Priority:** Must Have
- **Persona:** Demo Reviewer (P2)
- **Requirements:** FR7.2
- **Depends on:** US1.3, US2.1, US3.1, US4.1
- **Walking skeleton:** yes (this is its check)
- **Acceptance criteria:**
  - **AC6.1.1** Given the `dev` environment, when a test user signs in on one iOS simulator and on one Android emulator, then, on each, the SAR balance is shown, a transfer to a second test user can be sent, and the transfer appears in the history.
  - **AC6.1.2** Given the same journey, then an API smoke script run against the deployed `dev` API passes.
  - **AC6.1.3** Given the journey runs through the real sign-in, API and data store of `dev`, then no step uses a mock or a local stand-in.
- **INVEST:** The check for the walking skeleton; testable by the smoke script and a Flutter integration test. The person authorises the exact verification command at Construction.

### US6.2 Check the app in every environment

**As a** Demo Reviewer, **I want** the platform, the money service and the landing page deployed to `dev`, `stg` and `prd`, and a test build of the app for each, **so that** I can accept the MVP in the environment that matters.

- **Priority:** Must Have
- **Persona:** Demo Reviewer (P2)
- **Requirements:** FR7.1
- **Depends on:** US6.1
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC6.2.1** Given each of `dev`, `stg` and `prd`, then the deployed platform, money service and landing page pass their smoke tests.
  - **AC6.2.2** Given each environment, then a test build of the app (TestFlight on iOS, Google Play internal testing on Android) points at that environment's API only.
- **INVEST:** Depends on the deployment pipelines; testable by smoke tests. The final acceptance against the SOW is in US6.4.

### US6.3 Read about RAAD on a landing page

**As a** Demo Reviewer, **I want** a public landing page that introduces RAAD in Arabic and English, **so that** I can see where to get the app.

- **Priority:** Could Have
- **Persona:** Demo Reviewer (P2)
- **Requirements:** FR8.1
- **Depends on:** none
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC6.3.1** (depends on unconfirmed assumption A9; confirm the content before building this) Given each environment, then the landing page loads over HTTPS and shows the product name, a short description and where to get the app, in Arabic and English.
  - **AC6.3.2** Given the landing page, then it makes no call to the money service or to sign-in and shows no wallet data.
- **INVEST:** Independent of every other story; small; testable by the page's smoke test.

### US6.4 Accept the MVP against the SOW's success criteria

**As a** Demo Reviewer, **I want** to run the SOW's six success criteria against the `prd` environment with two test users, **so that** I can accept the MVP knowing it does what the customer asked.

- **Priority:** Must Have
- **Persona:** Demo Reviewer (P2)
- **Requirements:** FR7.1, FR7.2 (the SOW's "Success Criteria" are the source; no requirement of its own)
- **Depends on:** every other Must Have story (US1.1 to US1.4, US2.1, US3.1 to US3.9, US4.1 to US4.3, US6.1, US6.2)
- **Walking skeleton:** no
- **Acceptance criteria:**
  - **AC6.4.1** Given `prd` and two test users, when the Demo Reviewer follows the written acceptance script, then all six SOW success criteria pass: secure login, a transfer to another wallet, a correct balance after the transfer, a refused duplicate, a visible history, and the application running on AWS.
  - **AC6.4.2** (depends on unconfirmed assumption A10) Given a new test user in `prd`, then the wallet starts with 1,000.00 SAR, as in `dev` and `stg`.
  - **AC6.4.3** Given a version that has not passed on `stg`, then it is not deployed to `prd`; a person approves each `prd` deploy of a version that has passed.
- **INVEST:** Deliberately last: it is the acceptance of the whole MVP, so it depends on the Must Have stories by design. Testable by the reviewer's script, run once the others are done.

---

## Requirements Handled Outside These Stories

Per Q7 (answer A), these non-functional requirements describe how the system runs and are traced to later stages instead of being turned into enabler stories: NFR2 (encryption), NFR5 to NFR8 (availability, response time, capacity, monitoring), NFR9 (error handling), NFR10 (logging), NFR12 (abuse limits, partly checked by AC1.3.5 and AC3.5.4), NFR13 (extensibility) and NFR14 (quality gates). `traceability.json` names the stage for each.

## Sources

- `requirements.md` in `inception/requirements-analysis/`: FR1 to FR8 and NFR1 to NFR15, the assumptions A1 to A13 and Out of Scope.
- `team-practices.md` in `inception/practices-discovery/`: walking skeleton, testing posture (test-first in the money core), deployment and the repo layout.
- `user-stories-questions.md` in this stage's directory: the answers to Q1 to Q7.
- `personas.md` in this stage's directory.
- `Raad-SOW.md` in `aidlc/spaces/default/knowledge/documents/`: the customer's statement of work.
