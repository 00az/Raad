# Story Map: RAAD Digital Wallet MVP

Conversation language: English.

This map assigns every story in `stories.md` to the units in `unit-of-work.md`. A unit named on a row implements part of that story, and its Functional Design traces all of that story's acceptance criteria. Several units in one cell are separated by `;`.

`traceability.json` names one lead unit per story: the unit that owns the story's main rule or screen. This map lists every unit that implements part of it.

The approved plan sent US6.2 and US6.4 to the Operation stages instead of a unit. The traceability check requires every story to map to a unit, so both are now assigned to the units that build their parts. The Operation stages still run the final proof: environment provisioning for US6.2 and deployment execution for US6.4.

## Story Map

| Story | Title | Unit | Directory | What each unit implements |
|---|---|---|---|---|
| US1.1 | Sign up | U3; U4 | u3-mobile-app; u4-platform | U3: the sign-up screen and its messages. U4: one account per email ignoring capitals and spaces, the password rule, and only email and display name stored. |
| US1.2 | Confirm my email and get my wallet | U1; U2; U3; U4 | u1-walking-skeleton; u2-money-service; u3-mobile-app; u4-platform | U1: one wallet with 1,000.00 SAR at first sign-in through the safety net, never a second one, and a safe retry. U2: the account-confirmed entry point and the refusal of a taken address. U3: the code screen, **Send the code again** and the wallet-setup-failed screen. U4: confirmation settings, a new code replacing the old one, and the signal wiring. |
| US1.3 | Sign in | U1; U3; U4 | u1-walking-skeleton; u3-mobile-app; u4-platform | U1: the sign-in screen and the sign-in check on every money request. U3: the refusal message, the **Have a confirmation code?** link and the too-many-attempts message. U4: the same refusal for a wrong password and an unconfirmed account, and the sign-in rate limit. |
| US1.4 | Sign out | U3 | u3-mobile-app | U3: sign-out and clearing the screens. |
| US1.5 | Reset a forgotten password | U3; U4 | u3-mobile-app; u4-platform | U3: the reset screens. U4: the reset settings and the password rule. |
| US1.6 | Stay signed in | U3; U4 | u3-mobile-app; u4-platform | U3: silent renewal and the sign-in-again screen. U4: the session lengths. |
| US2.1 | See my balance | U1 | u1-walking-skeleton | U1: the balance in SAR from whole halalas, correct after a transfer, and only the caller's own wallet. |
| US2.2 | See when my balance may be out of date | U3 | u3-mobile-app | U3: the BalanceSnapshot, the out-of-date mark and the retry. |
| US3.1 | Send money to another RAAD user | U1 | u1-walking-skeleton | U1: the all-or-nothing transfer, the result screen with reference and new balance, and the property test of the total money. |
| US3.2 | Review and confirm before sending | U1 | u1-walking-skeleton | U1: the review screen with the recipient's name and email, the amount and the balance after. |
| US3.3 | Stay within the amount limits | U2; U3 | u2-money-service; u3-mobile-app | U2: the 100 to 50,000 halala limits in the Ledger. U3: the hint, the early check and the message, with typed values kept. |
| US3.4 | Be stopped when my balance is too low | U1; U3 | u1-walking-skeleton; u3-mobile-app | U1: the balance check inside the transfer, including the exact-balance case. U3: the message, with typed values kept. |
| US3.5 | Be stopped when the recipient is not valid | U2; U3; U4 | u2-money-service; u3-mobile-app; u4-platform | U2: the unknown-recipient and own-wallet refusals, and the email comparison. U3: the messages. U4: the lookup rate limit. |
| US3.6 | Never send the same transfer twice | U2; U3 | u2-money-service; u3-mobile-app | U2: request keys, replay and the simultaneous-repeat case. U3: one key per transfer and the double-tap rule. |
| US3.7 | Never overdraw with simultaneous transfers | U2 | u2-money-service | U2: the simultaneous-transfer tests against a real data store. U1's all-or-nothing transfer already includes the balance check that these tests prove. |
| US3.8 | Know what happened when the answer is lost | U2; U3 | u2-money-service; u3-mobile-app | U2: the replay that returns the first outcome. U3: the could-not-confirm screen, the PendingTransfer and the **Try again** rules. |
| US3.9 | Not send while offline | U3 | u3-mobile-app | U3: the send button off while offline, and back on when the connection returns. |
| US4.1 | See my transfer history | U1 | u1-walking-skeleton | U1: sent and received entries with names, newest first with a fixed order, only completed transfers, only the caller's own history, times in the phone's zone. |
| US4.2 | See money I have received | U1; U3 | u1-walking-skeleton; u3-mobile-app | U1: received transfers in the balance and history on opening the app. U3: pull to refresh, the **Refresh** button, and no automatic refresh or push. |
| US4.3 | Load a long history page by page | U2; U3 | u2-money-service; u3-mobile-app | U2: pages from a position marker, with nothing skipped or repeated. U3: **Load more** and its loading and failure rows. |
| US4.4 | See a clear message when there is nothing to show | U3 | u3-mobile-app | U3: the empty and error views of the history. |
| US5.1 | Use the app in Arabic or English | U3 | u3-mobile-app | U3: both languages, the mirrored layout, the switch and the number formats. |
| US5.2 | Use the app with a screen reader and larger text | U3 | u3-mobile-app | U3: the accessibility checklist. |
| US5.3 | See a loading, empty or error view on every data screen | U3 | u3-mobile-app | U3: the three views on every data screen. |
| US6.1 | Check the whole journey on dev | U1 | u1-walking-skeleton | U1: the API smoke script and the integration test against `dev`. |
| US6.2 | Check the app in every environment | U2; U3; U4; U5 | u2-money-service; u3-mobile-app; u4-platform; u5-landing-page | U2: the money service's stacks and smoke test in `dev`, `stg` and `prd`. U3: one app build per environment, pointing at that environment's API only. U4: the platform's stacks and smoke test in each environment. U5: the page and its smoke test in each environment. Environment provisioning (Operation) proves all three environments. |
| US6.3 | Read about RAAD on a landing page | U5 | u5-landing-page | U5: the page and its smoke test. |
| US6.4 | Accept the MVP against the SOW's success criteria | U1; U3 | u1-walking-skeleton; u3-mobile-app | U1: the 1,000.00 SAR opening balance, the same in every environment. U3: the Demo Reviewer's written acceptance script for the six SOW criteria with two test users. The `prd` deploy gate is part of each repo's pipeline (CI and deployment stages), and the run itself happens at deployment execution (Operation). |

## Stories Across Several Units

These stories are split between units; the table above says which part each unit owns.

- **Account flows:** US1.1, US1.3, US1.5 and US1.6 share their behaviour between the app's screens (U3) and the sign-in settings (U4). US1.3 also uses U1's sign-in check.
- **Wallet setup (US1.2):** all four of U1 to U4 take part. U1 opens the wallet through the safety net, U2 adds the confirmation entry point, U4 wires the signal, and U3 adds the screens.
- **Money rules:** US3.3, US3.5, US3.6 and US3.8 put the rule in the money service (U2) and the message or key handling in the app (U3). US3.4 keeps its rule in U1's transfer.
- **History:** US4.2 and US4.3 split between the data (U1 or U2) and the app's refresh and paging controls (U3).

## Implementation Order Within Each Unit

The order inside a unit only; the order between units is decided in Delivery Planning.

| Unit | Order of stories inside the unit |
|---|---|
| U1 | US1.3 sign-in and the test-user script; US1.2 wallet opening through the safety net, with US6.4's opening balance; US2.1 balance; US3.2 and US3.1 review and send; US3.4 balance check; US4.1 and US4.2 history; US6.1 the end-to-end check on `dev` |
| U2 | US3.3 limits and US3.5 recipient refusals; US3.6 request keys and US3.8 replay; US3.7 simultaneous-transfer tests; US4.3 paging; US1.2 the account-confirmed entry point; US6.2 the stacks and smoke test for every environment |
| U3 | US1.1, US1.2, US1.3, US1.5, US1.6 and US1.4 account screens; US3.3, US3.4, US3.5, US3.6, US3.8 and US3.9 money messages and rules; US2.2, US4.2, US4.3 and US4.4 balance and history states; US5.3, US5.1 and US5.2 views, languages and accessibility; US6.2 the build per environment; US6.4 the acceptance script |
| U4 | US1.1, US1.3, US1.5 and US1.6 sign-in settings; US3.5 lookup rate limit; US1.2 resend and the signal wiring; US6.2 the stacks and smoke test for every environment |
| U5 | US6.3 the page; US6.2 the site in every environment |

## Coverage Check

- Every story in `stories.md` (28) is assigned to one or more units.
- Every unit has rows: U1 has 10, U2 has 8, U3 has 21, U4 has 7 and U5 has 2.

## Sources

- `stories.md` in `inception/user-stories/`: US1.1 to US6.4.
- `unit-of-work.md` and `units-generation-questions.md` in this stage's directory.
