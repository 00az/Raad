# Interaction Specification: RAAD Digital Wallet MVP

Conversation language: English.

This document says how the screens in `mockups.md` behave. It is built from the stories in `stories.md` (acceptance criteria `AC1.1.1` to `AC6.4.3`), the requirements in `requirements.md` and the answers in `refined-mockups-questions.md`. Visual values (colours, type, spacing) are in `design-system-mapping.md`; the accessibility checks are in `accessibility-checklist.md`.

## Flows

### Flow F1: Create an account and sign in for the first time

Persona: Wallet User (P1). Trigger: the user opens the app for the first time. Stories: US1.1, US1.2, US1.3.

1. S1 Sign in → taps **Create an account** → S2.
2. S2 → fills display name, email and password → taps **Create account** → the app asks the sign-in service to create the account; a code is emailed → S3 with the email filled in.
3. S3 → enters the code → taps **Confirm** → the account is confirmed → S1 with "Your email is confirmed. Please sign in."
4. S1 → enters email and password → taps **Sign in** → on the first sign-in the money service creates the wallet with 1,000.00 SAR (AC1.2.3) → S6 shows 1,000.00 SAR.

Success outcome: S6 shows a balance of 1,000.00 SAR and an empty "Latest transfers".

Error paths:
- Address already in use (AC1.1.2) → message under the email on S2 → the user signs in instead.
- Password breaks the rule (AC1.1.3) → rule text under the password on S2 → typed values stay.
- Wrong or expired code (AC1.2.2) → message on S3 → the user retries, or taps **Send the code again** (AC1.2.6) to get a new code by email; the old code stops working.
- Wallet creation fails (AC1.2.5) → the "We could not set up your wallet" screen with **Try again** → the retry ends with exactly one wallet (AC1.2.4).

### Flow F2: Sign in with an unconfirmed account

Stories: US1.3 (AC1.3.3), US1.2. Trigger: the user signed up but never entered the code.

1. S1 → correct email and password → the sign-in service refuses.
2. S1 shows exactly the message used for a wrong password: "The email address or password is not correct." It never says the account is unconfirmed.
3. The user taps **Have a confirmation code?** on S1 → S3 (the email field is empty; the user types it) → enters the code → S1.

The refusal reveals nothing about which case applied, and the way to confirm exists on the sign-in screen for every user (Q5, answer A).

### Flow F3: Send money

Persona: Wallet User (P1). Trigger: the user taps **Send** (tab) or **Send money** (S6 button). Stories: US3.1 to US3.9.

1. S7 → types the recipient's email and the amount → taps **Continue**.
2. The app checks the form (amount in range; email not the user's own; network on). If it fails, the message shows under the field and the values stay (AC3.3.2, AC3.5.2).
3. The app asks the money service whether the recipient exists. If not, S7 shows "No RAAD user has this email address." (AC3.5.1). If yes, S8 shows the recipient's name and email, the amount and the balance after the transfer (AC3.2.1).
4. S8 → taps **Confirm** → the app creates a fresh unique request key and sends the transfer once (AC3.6.3, AC3.6.4). The buttons turn off and the confirm button shows "Sending…".
5. The money service answers:
   - Done → S9 success with the amount, the recipient, the reference and the new balance (AC3.1.2). **Done** goes to S6, which refreshes.
   - Refused for balance, amount or recipient → back to S7 with the message and all values kept (AC3.4.3). The History does not change (AC4.1.3).
   - No answer or lost connection → S9 "We could not confirm the transfer" (AC3.8.1). **Check my History** opens S10 and refreshes it (AC3.8.3). **Try again** returns to S8 with the recipient and amount locked; nothing is sent until the user taps **Confirm** again, and that tap sends the same request key (AC3.8.2). If the user edits the details with **Change details**, or leaves the flow, the old key is dropped and a new one is made for the next **Confirm**; S7 then shows "Check your History first. Your earlier transfer may have gone through." until the user has opened S10 once. A key is never sent with different details (AC3.6.4).

Success outcome: S9 shows the confirmation; S6 and S10 show the new balance and the new entry.

Error paths: described in step 5. A second tap during step 4 does nothing (AC3.6.3). If the connection drops before step 4, the Continue and Confirm buttons turn off with "Sending needs a connection." (AC3.9.1).

### Flow F4: See what arrived

Stories: US4.2. Trigger: someone sent money to the user.

1. The user opens the app, pulls down on S6 or S10, or presses the **Refresh** button in their top bar.
2. The balance and the list refresh. A "Received from" entry appears with a plus sign (AC4.2.1).

There is no push notification and no automatic refresh while the app sits idle (AC4.2.2).

### Flow F5: Reset a forgotten password

Stories: US1.5. Trigger: the user taps **Forgot password?** on S1.

1. S4 → enters the email → taps **Send code** → S5 with "If an account exists for this address, we sent a code."
2. S5 → enters the code and a new password → taps **Change password** → S1 with "Your password was changed. Please sign in."

Error paths: wrong or expired code (AC1.5.2) and a password that breaks the rule (AC1.5.3), shown on S5 with the typed values kept.

### Flow F6: Session ends and renews

Stories: US1.6. Trigger: the app is used for more than an hour, or not opened for 30 days.

- Within 30 days of the last use, the app renews the session silently when it expires; the user sees nothing (AC1.6.1).
- After 30 days without opening the app, S1 appears with "For your security, please sign in again." (AC1.6.2).
- If the session cannot be renewed while the user is typing on S7, the app goes to S1. The typed values are not kept (the criterion that would keep them was removed from US1.6).

### Flow F7: Change language

Stories: US5.1. Trigger: the user opens S11 and picks a language.

The whole app switches language and direction at once, on the same screen, without signing in again (AC5.1.3). The choice is kept on the phone. Before the user has chosen, the app follows the phone's language if it is Arabic or English and uses English otherwise.

### Flow F8: Sign out

Stories: US1.4. S11 → **Sign out** → S1. The back gesture then cannot return to a wallet screen (AC1.4.2).

## Global Behaviour

| Topic | Rule | Source |
|---|---|---|
| Loading feedback | Placeholders for initial loads of S6 and S10; a spinner inside the button for actions. After 5 seconds of waiting, the button text changes to "Still working…". | UX guide, AC5.3.1 |
| Timeouts | Every request times out after 15 seconds and is treated as "no answer". | NFR9 (every outbound call has a timeout) |
| Offline | A banner "No connection." appears at the top of any screen that needs the network; wallet data already loaded stays visible and is marked out of date (AC2.2.1). Sending is off (AC3.9.1). | US2.2, US3.9 |
| Retry | Every error view has a **Try again** control. Retrying a transfer reuses the request key (AC3.8.2); every other retry is a plain repeat. | US3.8 |
| Typed values | Any refusal or failure keeps everything the user typed. | FR3.12 |
| Money display | Amounts show as `1,234.56 SAR` in English and `1,234.56 ر.س` in Arabic, with Western digits, a minus sign for sent and a plus sign for received. Held in whole halalas everywhere. | A8, FR2.1 |
| Dates | Date and time in the phone's time zone, for example `11 Nov 2026, 14:05`. | NFR15 |
| Motion | Transitions last under 300 ms. If the phone asks to reduce motion, they are turned off. | Interaction patterns |
| Screen capture | Not restricted in the MVP. | (no requirement) |
| Environment chip | A small `DEV` or `STG` chip appears on S1 and S11 in those builds and never in `prd`. | Proposed, see Open Questions |

## Component Specifications

### AmountField

| Field | Value |
|---|---|
| Component | AmountField |
| Description | Enter an amount in SAR as whole halalas. |
| Category | input |

States:

| State | Description | Trigger |
|---|---|---|
| default | Shows `0.00`; hint "From 1.00 to 500.00 SAR" below. | screen opens |
| focus | Outlined in the accent colour; numeric keypad. | tap |
| filled | Shows the amount with two decimals. | digits typed |
| error | Red outline with an icon and a message under the field. | out of range, balance too low |
| disabled | Greyed, not editable. | sending in progress |

Props:

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| valueHalalas | integer | yes | 0 | The amount in whole halalas. |
| minHalalas | integer | yes | 100 | Smallest accepted amount (1.00 SAR). |
| maxHalalas | integer | yes | 50000 | Largest accepted amount (500.00 SAR). |
| errorText | string | no | none | Message shown under the field. |

Responsive behaviour: the same on all sizes; the field spans the content width, never narrower than 200 dp.

Accessibility:

| Requirement | Implementation |
|---|---|
| Role | Text field with a numeric keyboard. |
| Keyboard interaction | Digits only; backspace removes the last digit; no decimal key. |
| Label | Visible label "Amount (SAR)"; the spoken value reads "one hundred riyals" form, for example "100 riyals and 0 halalas" in English. |
| Contrast | Text 16.6 to 1 on the surface; outline 3.9 to 1. |
| Screen reader | Announces the label, the value and any error text. |
| Focus management | When an error appears after Continue, focus moves to the first field with an error. |

### RecipientField

| Field | Value |
|---|---|
| Component | RecipientField |
| Description | Enter the recipient's email address. |
| Category | input |

States: default, focus, filled, error (own address, no such user, too many lookups), disabled (while sending).

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| value | string | yes | empty | The email as typed. |
| errorText | string | no | none | Message under the field. |

Behaviour: email keyboard; automatic capitals and suggestions off; surrounding spaces and capitals are ignored when the address is checked (AC3.5.3); the typed text is kept as the user wrote it.

Accessibility: visible label above the field; the error text is announced when it appears; ARIA-equivalent semantic label "Recipient's email address".

### BalanceCard

| Field | Value |
|---|---|
| Component | BalanceCard |
| Description | Shows the wallet balance and how fresh it is. |
| Category | display |

States:

| State | Description | Trigger |
|---|---|---|
| loading | Grey placeholder shapes. | first load |
| loaded | Balance and "Updated just now" or the time. | data arrives |
| stale | Old balance, clock icon, "Out of date. Last updated 14:05." and **Try again**. | refresh fails after a good load |
| error | "We could not load your balance." and **Try again**; no figure. | first load fails |

Props: `balanceHalalas` (integer, optional), `updatedAt` (instant, optional), `status` (loading | loaded | stale | error).

Accessibility: the whole card reads as one item, "Balance, 1,234.56 riyals, updated just now"; the stale state is announced as "Out of date" and shown with text and an icon, not colour alone.

### TransferListItem

| Field | Value |
|---|---|
| Component | TransferListItem |
| Description | One sent or received transfer in a list. |
| Category | display |

Props: `direction` (sent | received), `otherName`, `otherEmail`, `amountHalalas`, `occurredAt`, `reference`.

States: default only (entries are not editable and not tappable in the MVP).

Accessibility: reads as "Sent to Khalid, khalid at example dot com, 100 riyals, 11 November 2026 at 14:05, reference RAAD-7K2M9QXD". Direction is shown by the arrow, the words and the sign, never by colour alone.

### PrimaryButton

| Field | Value |
|---|---|
| Component | PrimaryButton |
| Description | The one main action on a screen. |
| Category | input |

States: default, pressed, focus, disabled (with the reason in text near it), loading (spinner and "…ing" label, taps ignored).

Rules: one primary button per screen; minimum height 48 dp and width of the content; label is a verb ("Sign in", "Send money", "Confirm").

Accessibility: role button; focus ring 2 dp in the accent colour; a disabled button's reason is in the text near it, not only in its colour.

### StatusBanner

| Field | Value |
|---|---|
| Component | StatusBanner |
| Description | A message about the connection or a notice at the top of a screen. |
| Category | feedback |

Kinds: offline ("No connection."), notice ("Your email is confirmed. Please sign in."), error ("The email address or password is not correct."). Each has an icon, text and, where useful, an action.

Accessibility: announced politely when it appears; never relies on colour alone.

### ConfirmationCodeField

| Field | Value |
|---|---|
| Component | ConfirmationCodeField |
| Description | Enter the emailed code. |
| Category | input |

Behaviour: numeric keypad; accepts a pasted code; spaces are ignored; the confirm button turns on when the field is not empty. Error text "This code is not valid. Check it and try again." under the field, the typed value kept.

## Message Catalogue (drafts)

The English text is the draft for the build. The Arabic is a draft that a native Arabic reader must check before release.

| Key | English | Arabic (draft) |
|---|---|---|
| sign_in_refused | The email address or password is not correct. | البريد الإلكتروني أو كلمة المرور غير صحيحة. |
| sign_in_too_many | Too many attempts. Please wait a few minutes and try again. | محاولات كثيرة. يرجى الانتظار بضع دقائق ثم المحاولة مرة أخرى. |
| offline | No connection. Check your network and try again. | لا يوجد اتصال. تحقق من الشبكة وحاول مرة أخرى. |
| password_rule | At least 8 characters, with a lower-case letter, an upper-case letter and a digit. | 8 أحرف على الأقل، مع حرف لاتيني صغير وحرف لاتيني كبير ورقم. |
| code_resent | We sent a new code. | أرسلنا رمزًا جديدًا. |
| check_history_first | Check your History first. Your earlier transfer may have gone through. | تحقق من السجل أولًا. قد يكون تحويلك السابق قد تم. |
| email_in_use | This email address is already in use. Sign in instead? | هذا البريد الإلكتروني مستخدم بالفعل. هل تريد تسجيل الدخول؟ |
| code_invalid | This code is not valid. Check it and try again. | هذا الرمز غير صالح. تحقق منه وحاول مرة أخرى. |
| amount_range | The amount must be between 1.00 and 500.00 SAR. | يجب أن يكون المبلغ بين 1.00 و500.00 ر.س. |
| balance_low | Your balance is too low for this transfer. | رصيدك غير كافٍ لهذا التحويل. |
| own_address | You cannot send money to yourself. | لا يمكنك إرسال الأموال إلى نفسك. |
| no_such_user | No RAAD user has this email address. | لا يوجد مستخدم في رعد بهذا البريد الإلكتروني. |
| sending_needs_connection | Sending needs a connection. | الإرسال يحتاج إلى اتصال بالإنترنت. |
| transfer_sent | Transfer sent | تم إرسال التحويل |
| transfer_unconfirmed | We could not confirm the transfer. Your money may or may not have been sent. Check your History before you try again. | تعذر تأكيد التحويل. قد يكون المبلغ أُرسل أو لم يُرسل. تحقق من السجل قبل المحاولة مرة أخرى. |
| balance_stale | Out of date. Last updated {time}. | غير محدّث. آخر تحديث {time}. |
| history_empty | No transfers yet. | لا توجد تحويلات بعد. |
| history_error | We could not load your history. | تعذر تحميل السجل. |
| balance_error | We could not load your balance. | تعذر تحميل الرصيد. |
| wallet_setup_failed | We could not set up your wallet. Nothing was lost. Please try again. | تعذر إعداد محفظتك. لم يُفقد شيء. يرجى المحاولة مرة أخرى. |
| reset_code_sent | If an account exists for this address, we sent a code. | إذا كان هناك حساب بهذا البريد، فقد أرسلنا رمزًا. |

The password rule applies to letters of the Latin alphabet because Arabic script has no letter case. This is the person's rule (A4) and the Arabic draft says so; the native reader confirms the wording and whether Arabic-script passwords are to be allowed alongside the rule. All digits in the Arabic column are Western digits (0 to 9), as assumption A8 (accepted on Q9) requires.

## Open Questions

- **Resend limits.** "Send the code again" follows the sign-in rate limit (AC1.3.5). The exact number of resends per hour is set in NFR requirements.
- **Arabic-script passwords.** The password rule (A4) asks for Latin upper- and lower-case letters. Whether a password in Arabic script is also allowed is for the native reader and the person to confirm.
- **Environment chip.** Proposed in the global behaviour table; not in the requirements.
- **Request timeout.** 15 seconds is a design choice; NFR6 sets the response-time target (2 seconds for 95% of transfers) and the timeout must stay above it. NFR design confirms the figure.
