# Refined Mockups: Questions

Conversation language: English.

These questions settle what the screens of the RAAD app and the landing page look like. The stories (`US1.1` to `US6.4`) already say what each screen must do, and the practices fix the tools (Flutter for the app, plain HTML and CSS for the landing page), so none of that is asked again. Each question suggests an answer marked "(Recommended)". The trade in brackets only says whose call it usually is; anyone can answer any question.

## Q1. [Designer] Does RAAD have a logo, colours or fonts I should use?

Without brand assets, the app uses the standard Flutter look (Material 3) with one accent colour. Changing that colour or adding a logo later is a small change if it is kept in one place.

A. No brand assets yet. Use Material 3 with one accent colour I propose (a deep indigo), a text-only "RAAD رعد" wordmark, and keep the colour in one theme file so it is easy to change. (Recommended)
B. Yes. I will give you the logo, colours and fonts, and the mockups should wait for them.
C. No brand assets, and the app should look native on each phone: iOS-style on iPhone and Material on Android.
X. Other (please specify)

[Answer]: X. Use the attached RAAD logo (a chrome lightning bolt beside the Arabic "رعد" and the Latin "RAAD", on black, with blue and warm glints), and take the colour theme from it ("put our logo in attached"; **Mode:** chat)

## Q2. [Designer] How does a signed-in user move between the main screens?

The stories need three places: the balance, sending money, and the history. Language, sign-out and the change-language switch also need a home.

A. A bottom tab bar with three tabs: Wallet (balance and latest transfers), Send, and History. Language and sign-out sit under a profile icon at the top of the Wallet tab. (Recommended)
B. One home screen with the balance, a large Send button and the history underneath. No tab bar.
C. A side menu opened from a menu icon.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q3. [Designer] What does the Wallet screen show?

This is the first screen after sign-in, and the one the Demo Reviewer sees first.

A. The balance in a card at the top, a Send button under it, and the five latest transfers below with a "See all" link to History. (Recommended)
B. The balance and the Send button only. History is on its own tab.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q4. [Designer] How is sending a transfer laid out?

The stories require a form, a review and confirm step (US3.2), and a result with a reference and the new balance (AC3.1.2).

A. Three screens: (1) one form with the recipient's email and the amount, (2) a review screen with the recipient's name and email, the amount and the balance after, and a Confirm button, (3) a result screen. (Recommended)
B. Four screens: recipient first, then amount, then review, then result.
C. One screen with the form, and a pop-up dialog for the review and the result.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q5. [Designer] Where does a user with an unconfirmed account enter the emailed code?

AC1.3.3 requires that sign-in gives the same refusal for a wrong password and for an unconfirmed account, so the screen for the code must be reachable without sign-in telling the user which case applied.

A. A "Have a confirmation code?" link on the sign-in screen opens a screen asking for the email address and the code. The sign-up flow goes to the same screen straight after sign-up. (Recommended)
B. Same as A, with a "Send the code again" button on that screen.
C. Only the sign-up flow, straight after sign-up, with no link on the sign-in screen.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q6. [Designer] Which devices and screen orientations does the app support?

The practices test on one iOS simulator and one Android emulator. Supporting tablets and landscape adds layouts to design and test.

A. Phones in portrait only. On a tablet the phone layout is shown centred, and landscape is turned off. (Recommended)
B. Phones in portrait and landscape.
C. Phones and tablets, in portrait and landscape.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q7. [Quality engineer] Which accessibility standard should the screens meet?

The stories ask for screen-reader support and larger text (US5.2). A named standard gives the tester a checklist.

A. WCAG 2.1 level AA for the app and the landing page: contrast of at least 4.5 to 1 for text, touch targets of at least 44 by 44 points, labels on every field, and status never shown by colour alone. (Recommended)
B. Only what the stories say (screen reader, 200% text, no colour-only status).
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q8. [Designer] What does the landing page ask visitors to do?

There is no public store release in the MVP (testers get builds through TestFlight and Google Play internal testing), so there are no store pages to link to.

A. One page: the RAAD name, a one-paragraph description, and a "Request test access" button that opens an email to an address you give me. In Arabic and English with a language switch. (Recommended)
B. The same page, with "App Store" and "Google Play" badges marked "coming soon" and no button.
C. The same page with no button or badges. It only introduces RAAD.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q9. [Product owner] Do you accept these three assumptions from the requirements?

These were not put to you earlier, and the stories that depend on them are marked "confirm before building".

- Amounts and dates use Western digits (0 to 9) in both languages, and amounts are labelled "SAR" in English and "ر.س" in Arabic (A8).
- The landing page holds only a name, a short description and where to get the app, written by the customer or the team in Arabic and English (A9).
- The starting balance of 1,000.00 SAR is also given in `prd`, because all money is simulated (A10).

A. Accept all three as written. (Recommended)
B. Accept all except one or more that I name in my own words.
C. Reject all three; I will say what should happen instead.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)
