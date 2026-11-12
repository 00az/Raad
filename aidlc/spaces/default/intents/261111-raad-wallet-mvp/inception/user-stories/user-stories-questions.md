# User Stories: Story Plan and Questions

Conversation language: English.

This plan turns `requirements.md` (FR1 to FR8, NFR1 to NFR15) into user stories. Each story reads "As a [persona], I want [goal], so that [benefit]", has Given/When/Then acceptance criteria and a priority (Must, Should, Could or Won't have). Each question suggests an answer marked "(Recommended)". The trade in brackets only says whose call it usually is; anyone can answer any question.

## Plan Outline

- **Personas:** who the stories are for (Q3).
- **Story format:** INVEST, with 3 to 6 Given/When/Then criteria per story, including the sad path. Story IDs are `US{group}.{seq}`, criterion IDs are `AC{group}.{seq}.{n}`.
- **Breakdown:** how stories are grouped and cut (Q4, Q5).
- **Priority:** MoSCoW per story, which informs the MVP boundary decided in delivery planning (Q6).
- **Technical work:** how the build, deploy and monitoring requirements show up as stories (Q7).
- **Open assumptions:** requirements.md says User Stories asks about A2, A3, A4, A5, A6, A11, A12 and A13 first (Q1, Q2).

## Q1. [Product owner] Do you accept these five assumptions about sending and history?

These came from my draft, not from the SOW or your earlier answers, and they shape the acceptance criteria. Each stays an assumption until you say yes.

- Only completed transfers appear in the history; a refused transfer shows an error on screen and leaves no entry (A2).
- Sending money needs a network connection; offline, the app shows the last known balance marked out of date (A6).
- Before sending, the app shows the recipient's name and email and the amount, and the user confirms (A11).
- The app creates the unique key that makes a repeated request safe (A12).
- Sign-up and recipient lookup can reveal whether an email is registered; this is accepted for the MVP and limited by rate limits (A13).

A. Accept all five as written. (Recommended)
B. Accept all except one or more that I name in my own words.
C. Reject all five; I will say what should happen instead.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q2. [Security engineer] Do you accept these three sign-in assumptions?

- A user can reset a forgotten password with a code sent by email (A3).
- A password has at least 8 characters with a lower-case letter, an upper-case letter and a digit (A4).
- A session lasts about an hour and renews silently; after 30 days without opening the app the user signs in again (A5).

A. Accept all three as written. (Recommended)
B. Accept the reset and the password rule, and use a different session length (please say which).
C. Drop the password reset from the MVP; accept the other two.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q3. [Product owner] Which personas should the stories be written for?

The SOW describes one kind of user who both sends and receives money. Deployment on AWS is also a deliverable, and the customer's reviewer is the person who checks it.

A. Two personas: a Wallet User (signs up, sends and receives) and a Demo Reviewer (the customer's person who checks the SOW's success criteria on the deployed app). (Recommended)
B. Three personas: a Sender, a Recipient and a Demo Reviewer.
C. One persona only: the Wallet User.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q4. [Product owner] How should the stories be grouped?

The first slice (sign in, see balance, send one transfer, see it in history, on `dev`) is the walking skeleton and is built before anything else.

A. By user journey: sign-up and sign-in, balance, send money, receive money, history, language and accessibility, running on AWS. The first story in each of the first four groups together forms the walking skeleton. (Recommended)
B. By service: platform and sign-in, money service, mobile app, landing page.
C. By persona, then by feature.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q5. [Quality engineer] How small should the stories be?

Sending money is the biggest area (FR3 has twelve sub-requirements). One story per business rule gives each rule its own example and test, but makes more stories.

A. Medium: about 25 stories. Sending money is split by business rule (amount limits, not enough money, unknown recipient or yourself, repeated request, simultaneous transfers, lost response, confirmation). Other areas get one to three stories each. (Recommended)
B. Coarse: about 10 stories, one per requirement group, with the rules as acceptance criteria.
C. Fine: about 40 stories, one per requirement row.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q6. [Product owner] Which stories are Must Have for the MVP?

MoSCoW priorities inform the MVP boundary that delivery planning decides later. The SOW's success criteria are the Must Haves.

A. Must: sign-up and sign-in, balance, send money with all its safety rules, receive and history, and running on AWS (the SOW's six success criteria). Should: Arabic and right-to-left, password reset, the stale-balance mark, screen-reader support. Could: the landing page. Won't: everything under Out of Scope. (Recommended)
B. Everything in the requirements is Must Have.
C. Same as A, but Arabic and right-to-left is Must Have.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)

## Q7. [Delivery lead] How should the build, deploy, monitoring and quality requirements appear in the stories?

Some requirements (encryption, monitoring alarms, availability, CI gates) describe how the system runs rather than something a user does.

A. Write them as stories only where a person sees the result (for example, the Demo Reviewer opens the deployed app on `dev`). Trace the rest to later stages (NFR requirements, NFR design, infrastructure design, CI pipeline) as `Deferred`. (Recommended)
B. Also write enabler stories for the shared platform, the pipelines and the monitoring, with the engineers as the persona.
X. Other (please specify)

[Answer]: A (all recommended; **Mode:** chat)
