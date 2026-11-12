# Requirements Analysis: Questions

These questions fill the gaps the SOW leaves open about what RAAD must do. The
SOW says what the MVP is for (wallet-to-wallet transfers in SAR with simulated
money) and the practices already settled how it is built and deployed, so none
of that is asked again. Each question suggests an answer marked "(Recommended)".
The trade in brackets only says whose call it usually is; anyone can answer any
question.

## Q1. [Product owner] How do users get an account and sign in?

The SOW requires secure sign-in before a user can see a wallet or send money. This decides the sign-up screens and what the shared sign-in service must support.

A. Users sign up in the app with an email address and a password, confirm the email with a one-time code, then sign in with email and password. (Recommended)
B. Same as A, and every sign-in also asks for a one-time code sent by email.
C. Users sign up and sign in with a Saudi mobile number and a one-time code sent by SMS. No passwords.
D. No sign-up screen: we create the test users ahead of time and give them their credentials.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q2. [Product owner] How does a sender pick the person they are paying?

The sender has to name the recipient's wallet. This decides what a user must give when they sign up, and what the recipient is told about the sender.

A. By the recipient's registered email address. (Recommended)
B. By the recipient's mobile number.
C. By a short username each user chooses when they sign up.
D. By scanning or typing a wallet code shown in the recipient's app.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q3. [Product owner] Where does a new user's simulated money come from?

The SOW says transfers use simulated funds, not real money. Someone has to put that money into the first wallet, or there is nothing to send.

A. Every new wallet starts with a fixed balance of 1,000 SAR when it is created. (Recommended)
B. Every new wallet starts at 0 SAR, and the app has an "add test money" button that adds a fixed amount.
C. Both: a starting balance, plus an "add test money" button.
D. Wallets start at 0 SAR and we load test balances ourselves for the test users.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q4. [Product owner] What limits apply to a single transfer?

The SOW sets no limits. Without any, a bug or a typo can move a whole balance in one tap. Amounts are always whole halalas (1 SAR = 100 halalas), so the smallest possible transfer is 0.01 SAR.

A. At least 1.00 SAR and at most 5,000.00 SAR per transfer, with no daily total. (Recommended)
B. Same as A, with a daily total of 10,000.00 SAR per user.
C. At least 0.01 SAR, and no maximum other than the sender's balance.
X. Other (please specify)

[Answer]: X. At least 1.00 SAR and at most 500.00 SAR per transfer, with no daily total ("limit from 1 to 500 SAR"; **Mode:** chat)

## Q5. [Product owner] How does the recipient find out money has arrived?

The SOW asks for sending and receiving. The recipient's balance and history always update; this question is only about whether the app tells them.

A. No alert. The balance and history are correct the next time the recipient opens the app or pulls down to refresh. (Recommended)
B. The open app also refreshes the balance and history by itself every few seconds.
C. A push notification to the recipient's phone (needs Apple and Google push setup for each environment).
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q6. [Designer] Which language should the app use?

RAAD is a Saudi product with an Arabic name. Supporting right-to-left Arabic from the start is cheap; adding it after the screens are built is not.

A. Arabic and English, with right-to-left layout for Arabic, and the user can switch. (Recommended)
B. English only for the MVP.
C. Arabic only for the MVP.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q7. [Security engineer] Which data-protection and regulatory rules must the MVP follow?

The SOW asks for encryption in transit and at rest and for authorized access only. It names no regulation. The practices put every environment in `us-east-1` for now and leave the region to infrastructure design, so this answer decides whether a Saudi data-residency rule limits that choice.

A. It is a demo with simulated money. We follow the SOW's security controls, store only the email address and display name for each user, and treat no regulation (for example SAMA or the Saudi PDPL) as a requirement. (Recommended)
B. Same as A, and user data must stay in the Middle East, which limits the AWS Regions we can use.
C. The MVP must follow the Saudi PDPL and SAMA rules for a payments product. Please say which ones in your own words.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q8. [Operations engineer] How many users and how much availability does the MVP need to handle?

The SOW asks for reliability and "future growth" without numbers. These numbers become the performance and availability targets that the design and the load check are measured against.

A. Demo scale: up to 100 users, about 10 using the app at once, available 99.5% of each month, and 95% of transfers answered within 2 seconds. (Recommended)
B. Pilot scale: up to 10,000 users, about 200 at once, available 99.9% of each month, and 95% of transfers answered within 1 second.
C. We do not want numbers yet; design sensibly and measure later.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q9. [Operations engineer] What does "basic monitoring" mean for the MVP?

The SOW asks for basic monitoring and error handling, and the plan has no separate monitoring stage, so the monitoring has to be part of the build.

A. A dashboard for each environment, plus alarms on server errors, slow responses and failed transfers that send an email to one address you give us. (Recommended)
B. Logs and metrics only. Someone looks at them by hand; nothing alarms.
C. Same as A, with request tracing across the services added.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Assumptions the draft makes (tell me if any is wrong)

These are not questions. I will write them into the requirements as assumptions unless you correct them.

- Users have one wallet each, in SAR only, created when the account is created.
- Only transfers that complete appear in the history. A rejected transfer (for example not enough money) shows an error on screen and is not recorded as a history entry.
- The history shows both sent and received transfers, newest first, with the other person, the amount, the date and time, and a reference. It loads a page at a time.
- Sending the same transfer request twice, for example after a poor connection, moves the money once and returns the first result. The app creates the request's unique key.
- There is no admin or support screen, no refunds or reversals, no top-up from a real bank or card, and no real payment provider (already forbidden in the project rules).
- The app needs a network connection to show a balance or send money. It shows the last known balance, marked as out of date, when the connection fails, and never lets a transfer be sent offline.
- A user can only see their own wallet and history, and can only send from their own wallet.
