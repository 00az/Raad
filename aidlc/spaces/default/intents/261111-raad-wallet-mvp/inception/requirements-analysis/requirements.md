# Requirements: RAAD Digital Wallet MVP

Conversation language: English.

Sources are named in the Source column: `SOW` is `Raad-SOW.md` (the customer's statement of work), `Q1` to `Q9` are the answers in `requirements-analysis-questions.md`, `Practices` is `team-practices.md` from `practices-discovery/`, and `Request` is the project description ("Build the RAAD digital wallet MVP from the SOW and deploy it to AWS"). A requirement with no source is not in this document.

## Intent Analysis

RAAD is a digital wallet. A customer wants a minimum viable product that lets people sign in, see a balance in Saudi riyals (SAR) and send simulated money to another RAAD wallet, then see that transfer in their history. The product runs on AWS.

What the customer is trying to achieve, in order of weight:

- Balances are right after every transfer, and no request moves money twice. The SOW names both as the main challenges (SOW "Customer Challenges", "Success Criteria").
- Only the signed-in owner can see a wallet or send from it (SOW "Security").
- A person can finish the whole journey on a phone: sign up, sign in, see balance, send, see history (SOW "Expected Deliverables" 2 to 4).
- The result is deployed and running on AWS (SOW deliverable 5, Request).

Request type: new product, greenfield. Scope: multi-component (shared platform, money service, mobile app, landing page). Complexity: standard. The SOW is short; the nine answers in `requirements-analysis-questions.md` closed its gaps. Depth: Standard.

## Functional Requirements

### FR1 Accounts and sign-in

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR1 | A person can create an account, sign in and sign out of the app, and can reach a wallet only after signing in. | Every check below passes. | SOW "Security", Q1 |
| FR1.1 | A new user signs up in the app with an email address, a display name and a password. | Given the sign-up form with valid values, when the user submits it, then an account exists in the unconfirmed state and a one-time code is emailed to that address. | Q1 |
| FR1.2 | The user confirms the email address with the one-time code before the first sign-in. | Given an unconfirmed account, when the user enters the correct code, then the account is confirmed. Given a wrong or expired code, then the account stays unconfirmed and the app says the code is not valid. | Q1 |
| FR1.3 | A confirmed user signs in with email address and password. | Given correct credentials, then the app opens the user's wallet. Given wrong credentials or an unconfirmed account, then the app refuses and does not say which part was wrong. | Q1, SOW "Security" |
| FR1.4 | The user can sign out, and a signed-out app shows no wallet data. | After sign-out, going back in the app shows the sign-in screen and no balance or history. | SOW "Security" |
| FR1.5 | Every confirmed user has exactly one wallet, in SAR, with a starting balance of 1,000.00 SAR. The wallet exists by the end of the user's first confirmed sign-in. If it cannot be created then, the app shows an error with a retry and no wallet screen. | After the first confirmed sign-in the balance is 1,000.00 SAR. Repeating sign-up steps, or a retry of wallet creation, never gives a second wallet or a second starting balance. A forced failure of wallet creation shows the error and retry, and the retry succeeds with one wallet. | Q3, SOW "Project Constraints" |
| FR1.6 | One email address maps to one account. Email addresses are compared without regard to case or surrounding spaces. | Signing up with `A@x.com` after `a@x.com ` exists is refused with a message that the address is already in use. | Q2 |

### FR2 Wallet balance

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR2 | A signed-in user sees the current balance of their own wallet. | Every check below passes. | SOW deliverable 4, "Success Criteria" |
| FR2.1 | The balance is shown in SAR with two decimals. It is stored and calculated in whole halalas (1 SAR = 100 halalas). | A balance of 123,456 halalas is shown as 1,234.56 SAR. No stored or calculated amount is a decimal or floating-point number. | Practices (project rule on halalas), SOW "Project Constraints" |
| FR2.2 | The balance is correct after every transfer, for the sender and the recipient. | After a transfer of N halalas, the sender's balance is lower by N and the recipient's is higher by N, and no other balance changes. | SOW "Success Criteria" |
| FR2.3 | When the balance cannot be fetched, the app shows the last known balance marked as out of date, with the time it was last updated, and offers a retry. | Given the network is off after a successful load, the app shows the old balance, an "out of date" mark and the time, and does not show a blank or zero balance. | Corner checklist (stale data) |
| FR2.4 | A user can read only their own wallet. | A request for another user's wallet, with a valid sign-in, is refused and returns no data about that wallet. | SOW "Security" |

### FR3 Send money

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR3 | A signed-in user can send simulated SAR from their wallet to another RAAD wallet. | Every check below passes. | SOW "Success Criteria", Q2, Q4 |
| FR3.1 | The sender names the recipient by the recipient's registered email address. | Given a registered email, the transfer goes to that user's wallet. Given an address that is not registered, the app says no RAAD user has that address and no transfer is made. | Q2 |
| FR3.2 | A transfer amount is at least 1.00 SAR and at most 500.00 SAR, in whole halalas. There is no daily total. | 100 halalas and 50,000 halalas are accepted. 99, 50,001, zero, negative and any amount with a fraction of a halala are refused with a message that names the limits. Two transfers in one day that add up to more than 500.00 SAR are both accepted. | Q4 |
| FR3.3 | Before sending, the app shows the recipient's name and email, the amount and the sender's balance after the transfer, and the user confirms. | No transfer is sent until the user confirms on this screen. | Assumption A11 (not yet confirmed), corner checklist (destructive action) |
| FR3.4 | A transfer takes the amount from the sender and adds it to the recipient together, or does neither. | If any step fails, both balances are unchanged and no history entry is created. | SOW "Customer Challenges", "Security" |
| FR3.5 | A transfer that would take the sender below zero is refused. | Given a balance of 300.00 SAR, a transfer of 300.01 SAR is refused with a message that the balance is too low, and both balances are unchanged. A transfer of 300.00 SAR is accepted and leaves 0.00 SAR. | SOW "Customer Challenges" |
| FR3.6 | A user cannot send money to their own wallet. | A transfer to one's own email address is refused with a message and changes nothing. | Corner checklist (identity of things) |
| FR3.7 | Every transfer request carries a unique key. Sending the same key again returns the original result and moves money once. The app creates the key (Assumption A12, not yet confirmed). | Sending the same request twice, one after the other or at the same moment, changes the balances once, creates one history entry and returns the same result both times. | SOW "Security" ("duplicate transactions"), "Success Criteria" |
| FR3.8 | Two transfers out of one wallet at the same time can never take its balance below zero. | Given a balance of 500.00 SAR, two simultaneous transfers of 300.00 SAR give one success and one refusal for low balance, and the balance is 200.00 SAR. | SOW "Customer Challenges" |
| FR3.9 | The send button cannot be pressed twice while a transfer is in flight, and a repeated press never creates a second transfer. | A second tap before the result arrives does not send a second request, and if one is sent it carries the same key (FR3.7). | Corner checklist (double submit) |
| FR3.10 | When the app cannot tell whether a transfer went through (timeout or lost connection), it says so, tells the user to check their history before trying again, and allows a retry that reuses the same key. | After a lost response, retrying with the same key gives either the original success or a fresh success, never two transfers. | Corner checklist (network, retries) |
| FR3.11 | After a successful transfer the app shows a confirmation with the amount, the recipient, the reference and the new balance. | The confirmation appears with those four items, and the balance matches FR2.2. | SOW deliverable 2 |
| FR3.12 | Every refusal tells the user what is wrong and keeps what they typed. | Each refusal above shows a message in the user's language, and the amount and recipient fields still hold their values. | Corner checklist (invalid input) |

### FR4 Receiving money

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR4 | A recipient sees money they have received in their balance and history without any other action. | Every check below passes. | SOW deliverable 2, Q5 |
| FR4.1 | The recipient's balance and history show the transfer the next time the user opens the app or pulls down to refresh. | After a transfer, the recipient opens the app (or refreshes) and sees the higher balance and a history entry for it. | Q5 |
| FR4.2 | The app sends no push notification and does not refresh by itself in the MVP. | No push registration exists and the screens refresh only on open and on the user's refresh. | Q5 |

### FR5 Transfer history

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR5 | A signed-in user can see the history of the transfers they sent and received. | Every check below passes. | SOW deliverable 4, "Success Criteria" |
| FR5.1 | Each entry shows the direction (sent or received), the other person's name and email, the amount in SAR, the date and time, and the reference. | A completed transfer appears on both users' histories, as "sent" for the sender and "received" for the recipient, with the same amount and reference. | Q2 |
| FR5.2 | Entries are ordered newest first. Entries made at the same moment have a fixed order. | Reloading the list never changes the order of entries. | Corner checklist (collections) |
| FR5.3 | The history loads a page at a time. | A user with 1,000 entries sees the first page promptly and loads more on request, and no entry is skipped or shown twice across pages. | Corner checklist (very many items) |
| FR5.4 | Only completed transfers appear. A refused or failed transfer creates no entry. | After a refusal, the history is unchanged. | Assumption A2 (not yet confirmed) |
| FR5.5 | A user with no transfers sees a message that says so, which is different from a failure to load. | A new account shows "no transfers yet"; a failed load shows an error with a retry. | Corner checklist (empty, loading, error) |
| FR5.6 | A user can read only their own history. | A request for another user's history is refused and returns no data. | SOW "Security" |

### FR6 The app

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR6 | The mobile app runs on iOS and Android and offers the sign-in, balance, send and history screens of FR1 to FR5. | Every check below passes, and the walking skeleton's integration test (FR7.2) passes on one iOS simulator and one Android emulator. | SOW deliverable 2, Practices |
| FR6.1 | The app is available in Arabic and English. Arabic shows right to left. The user can switch language inside the app. | Every screen renders correctly in both languages, with no clipped or mirrored-wrong text, and the switch takes effect without signing in again. | Q6 |
| FR6.2 | Every screen that loads data has separate loading, empty and error views. | Each of the balance and history screens shows the three views under the matching conditions. | Corner checklist (screens) |
| FR6.3 | Screens work with a screen reader, with larger system text sizes, and do not use colour alone to show a status. | The sign-in, wallet and send screens pass a manual screen-reader walk-through on both platforms, and text at 200% still shows all controls. | Corner checklist (accessibility) |
| FR6.4 | The app never lets a transfer be sent without a network connection. | With the network off, the send button is off and says why. | Assumption A6 (not yet confirmed) |

### FR7 Running on AWS

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR7 | The application is deployed and runs on AWS. | Every check below passes. | SOW deliverable 5, "Success Criteria", Request |
| FR7.1 | The shared platform, the money service and the landing page are deployed to the `dev`, `stg` and `prd` environments, and the mobile app is built for each environment. | Each environment answers its smoke test (Practices, Testing Posture). | Practices (Deployment) |
| FR7.2 | A test user can complete the whole journey against `dev`: sign in on the phone, see the SAR balance, send one transfer to another RAAD wallet and see it in the history. | The walking skeleton's verification (an API smoke script and a Flutter integration test) passes against `dev`. | Practices (Walking Skeleton), SOW "Success Criteria" |

### FR8 Landing page

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| FR8 | A public landing page introduces RAAD. | The page loads over HTTPS in each environment and its smoke test passes. | Practices (repo table, `RaadWeb`) |
| FR8.1 | The page is static, in Arabic and English, and holds only the product name, a short description and where to get the app. It has no sign-in and no wallet data. | The page makes no call to the money service or to sign-in. | Practices, Assumption A9 |

## Non-Functional Requirements

| ID | Requirement | Pass/fail check | Source |
|---|---|---|---|
| NFR1 | Security: sign-in. Every call that reads or changes a wallet requires a valid sign-in, and checks that the caller owns the wallet. | A call with no sign-in, an expired sign-in or someone else's sign-in is refused and returns no wallet data. | SOW "Security" |
| NFR2 | Security: encryption. All traffic between the app, the API and the services uses TLS 1.2 or later, and all stored data is encrypted at rest with keys managed on AWS. | A plain-HTTP request is refused or redirected; the data stores report encryption on; a scan finds no unencrypted store. | SOW "Security", Q7 |
| NFR3 | Money correctness. Amounts are whole halalas everywhere. For any sequence of transfers the total money across all wallets stays the same (apart from the starting balance given at wallet creation) and no balance goes below zero. | The property-based test in Practices (Testing Posture) passes, and the money-movement core holds at least 95% line and branch coverage. | SOW "Technical Requirements", Practices |
| NFR4 | Duplicate protection. A repeated request never moves money twice, including under simultaneous requests (FR3.7, FR3.8). | The replay test and the concurrency test in Practices pass against a real container of the data store. | SOW "Security", "Success Criteria" |
| NFR5 | Availability. The API and the wallet are available at least 99.5% of each calendar month in `prd`. | The monthly availability figure from the monitoring (NFR8) is at least 99.5%. | Q8 |
| NFR6 | Response time. At least 95% of transfer requests get a response within 2 seconds, measured at the API, at the demo load in NFR7. | The load check at demo load shows a 95th-percentile response time of 2 seconds or less. | Q8 |
| NFR7 | Capacity. The MVP supports up to 100 users, with about 10 using the app at once. | The load check runs 10 simultaneous users with no errors and meets NFR6. | Q8 |
| NFR8 | Monitoring. Each environment has a dashboard and alarms on server errors, slow responses and failed transfers. Alarms send an email to one address. | Raising each condition in `stg` moves the matching alarm to the alarm state and sends the email. | SOW "Technical Requirements" ("basic monitoring"), Q9 |
| NFR9 | Error handling. Every API error returns a structured error with a stable code and a message safe to show. No stack trace, internal name or personal data leaves the service. Every outbound call has a timeout. | A forced failure in each service returns the structured error and nothing else in the body. | SOW "Technical Requirements" ("error handling") |
| NFR10 | Logging. Logs hold no passwords, tokens or personal details beyond an opaque user id. Each request log line carries a correlation id. | A scan of the logs from the test run finds none of the test user's email, password or token. | Practices (project rule on logs) |
| NFR11 | Data minimisation. The only personal data kept per user is the email address and the display name. No identity document, card or bank detail is collected. | The data model holds no other personal field. | Q7, Practices (project rule on payment data) |
| NFR12 | Abuse limits. The public API has a firewall and rate limits per caller, so a single caller cannot flood sign-in or transfers. | A burst above the limit from one caller gets refused responses, and other callers are unaffected. | SOW "Secure API communication", Practices (platform) |
| NFR13 | Extensibility. Adding a service (for example the AI assistant or Qattah) needs no change to the money service's API. It needs only a new path mapping and its own repo. | A stub service attached only by a new path mapping answers through the public API domain in `dev`, with no change to the money service's code or its API spec. | SOW "Scalability and maintainability", Practices (platform) |
| NFR14 | Quality gates. Each repo meets the coverage floors, linting, type checks, dependency audit and cdk-nag rules in Practices, and its full check suite passes in CI before a merge. | The CI run on `main` of each repo is green. | Practices (Testing Posture, Code Style, Deployment) |
| NFR15 | Time. Times are stored in UTC and shown in the device's time zone. | A transfer made at 23:30 in Riyadh shows 23:30 on a phone set to Riyadh time and the same instant on a phone set to another zone. | Corner checklist (time) |

## Constraints

- The currency is Saudi riyal (SAR) only, and money is simulated. No real payment system is connected and no card or bank detail is accepted (SOW "Project Constraints", Practices).
- The MVP covers wallet-to-wallet transfers only (SOW "Project Constraints").
- The solution is built in a short period, so it stays simple (SOW "Project Constraints").
- It is built and deployed on AWS, with all infrastructure as AWS CDK code in Python, in one AWS account and in `us-east-1` for now (SOW "Technical Requirements", Practices).
- The stack, repos, branching, testing and deployment practices in `team-practices.md` are fixed for this work. Money is stored as whole halalas (Practices).
- The first Unit is the walking skeleton in FR7.2, built before other work starts (Practices).

## Assumptions

Each assumption stays an assumption, not a confirmed requirement, until the person confirms it in a later stage's questions (User Stories asks about A2, A3, A4, A5, A6, A11, A12 and A13 first). Where an assumption has a check, the check is what the build is tested against if the person confirms it.

| ID | Assumption | Reason |
|---|---|---|
| A1 | Each user has one wallet, in SAR only, created at sign-up. | The SOW names wallet-to-wallet transfers in one currency and nothing about several wallets. |
| A2 | A refused or failed transfer is not recorded in the history. Check: after a refused transfer, the history list is unchanged (FR5.4). | The SOW asks for a history of transfers; recording refusals adds a status model the MVP does not need. The user sees the refusal on screen. |
| A3 | A user can reset a forgotten password with a code sent by email. Check: given a confirmed account, a reset with the emailed code sets a new password, the old password then fails to sign in and the new one succeeds; a wrong or expired code changes nothing. | Without it, a forgotten password locks a user out for good. The sign-in service offers it with no extra build. |
| A4 | The password must be at least 8 characters with a lower-case letter, an upper-case letter and a digit. Check: `Abcdef12` is accepted; `abcdef12`, `ABCDEF12`, `Abcdefgh` and `Abcde12` are refused at sign-up and at reset with a message that names the rule. | A common minimum when the SOW gives none. |
| A5 | Sign-in lasts about an hour and renews silently. A user who has not opened the app for 30 days signs in again. Check: with a test clock, a call after 61 minutes is served by a silent renewal with no sign-in screen, and a call 31 days after the last use returns the user to the sign-in screen. | Short sessions limit harm from a lost phone, and the SOW gives no figure. |
| A6 | The app needs a network connection to send money, and shows a stale-marked last known balance when offline (FR2.3, FR6.4). | An offline transfer would need a queue and a way to settle conflicts; that is more than the MVP needs. |
| A7 | There is no admin or support screen, no refund or reversal, no top-up from a bank or card, and no account deletion. | None is in the SOW's deliverables, and each adds money flows the MVP excludes. |
| A8 | Amounts and dates use Western digits (0 to 9) in both languages, and amounts are labelled "SAR" in English and "ر.س" in Arabic. | A single rule keeps one value in one form across the screens; the person can choose Arabic-Indic digits instead. |
| A9 | The landing page holds a name, a short description and where to get the app. Its text is supplied by the customer or written by the team in Arabic and English. | The SOW does not mention a landing page; Practices lists the repo, and no content was specified. |
| A10 | The starting balance of 1,000.00 SAR is given in every environment, `prd` included, because all money is simulated. | Q3 does not separate environments, and `prd` is also a demonstration. |
| A11 | The recipient's name and email are shown to the sender before sending (FR3.3). | Without this, a mistyped address can send money to a stranger. The SOW asks for secure, understandable transactions. |
| A12 | The app creates the unique key for each transfer request (FR3.7). The service never needs the app to supply anything else to detect a repeat. | The app is the only party that knows a second request is a retry of the first. |
| A13 | Sign-up and recipient lookup may reveal whether an email address is registered, while sign-in does not say which credential was wrong. This is accepted for the MVP, limited by the per-caller rate limits in NFR12. Check: a burst of recipient lookups above the NFR12 limit from one caller is refused. | A transfer needs the sender to know whether the recipient exists (FR3.1), and the MVP has no contact book to hide behind. |

## Out of Scope

- Real payments, cards, bank accounts, top-up from outside, cash-out, any currency other than SAR.
- Requests for money, QR codes, scheduled or recurring transfers, bill payment, group pooling (Qattah) and the AI assistant (`RaadAiService`). The last two come after the MVP (Practices).
- A daily transfer limit (Q4).
- Push notifications and automatic refresh (Q5).
- Sign-in with a phone number, SMS codes, multi-factor sign-in and biometric unlock (Q1).
- Regulatory certification or alignment with SAMA or the Saudi PDPL, and Middle East data residency (Q7).
- Request tracing across services and a separate observability stage (Q9).
- An admin or support tool, refunds, reversals, account deletion (A7).
- Public App Store or Google Play release. Testers get builds through TestFlight and Google Play internal testing (Practices).
- Growth beyond the demo scale in NFR7. The design keeps room to grow, but no target above 100 users is set (Q8).

## Assumptions & Open Questions

Assumptions are listed under the Assumptions heading above (A1 to A13).

Open questions, for later stages:

- Which email address receives the monitoring alarms (NFR8)? Needed by infrastructure design.
- How many verification and reset emails can each environment send? The default AWS email sending has low daily limits and may need a sender setup; infrastructure design decides this (FR1.2, A3).
- Who writes and checks the Arabic wording of the app and the landing page (FR6.1, FR8.1)?
- Does `RaadMoneyService` or the shared sign-in service own the creation of the wallet at first sign-in (FR1.5)? Domain design decides this; the requirement is only that exactly one wallet exists with one starting balance.
- If the customer later asks for Middle East data residency (Q7 option B), which region replaces `us-east-1`? Infrastructure design revisits the region, as Practices says.

## Sources

- `Raad-SOW.md` in `aidlc/spaces/default/knowledge/documents/`: the customer's statement of work.
- `requirements-analysis-questions.md` in this stage's directory: Q1 to Q9, answered by the person.
- `team-practices.md` in `inception/practices-discovery/`: affirmed team practices (repos, environments, stack, testing, deployment, project rules).
- `.kiro/knowledge/aidlc-product-agent/corner-checklist.md`: the sweep for unusual conditions, applied to the components the request names (sign-in, wallet, transfer, history, app screens, deployment).
- Project description: "Build the RAAD digital wallet MVP from the SOW and deploy it to AWS".
