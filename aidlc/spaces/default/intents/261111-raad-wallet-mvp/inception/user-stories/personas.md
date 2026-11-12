# Personas: RAAD Digital Wallet MVP

Conversation language: English.

These two personas follow Q3 (answer A) in `user-stories-questions.md`. They are built from `requirements.md` and the customer's statement of work (`Raad-SOW.md`); the details below the goals are working assumptions to correct, not research findings.

## Priority Ranking

1. Wallet User: the person every Must Have story serves.
2. Demo Reviewer: serves the stories that prove the SOW's success criteria on the deployed app.

## P1. Wallet User: Noura

| Field | Detail |
|---|---|
| Name | Noura, a Wallet User |
| Role | An adult in Saudi Arabia who holds a RAAD wallet on her phone and both sends and receives money. One person plays both the sender and the recipient, so there is no separate Sender or Recipient persona. |
| Goals | Send money to another RAAD user quickly and be sure the right amount went to the right person. See her balance and a clear list of what she sent and received. Use the app in the language she prefers. |
| Pain points | Fears a transfer that goes through twice or not at all. Cannot tell whether a slow transfer worked. Dislikes apps that bury her history or show a balance that may be wrong. |
| Tech comfort | Medium. Uses banking and chat apps daily on iOS or Android. |
| Frequency | Several times a week. |
| Context | On a phone, often on mobile data, sometimes with a weak connection. Reads Arabic or English. |
| Relationships | Pays and is paid by other Wallet Users, who are the same persona. |

Source: SOW "Customer Overview", "Customer Challenges" and "Success Criteria"; `requirements.md` FR1 to FR6.

## P2. Demo Reviewer: Khalid

| Field | Detail |
|---|---|
| Name | Khalid, a Demo Reviewer |
| Role | The customer's person who accepts the MVP. He checks the SOW's six success criteria on the deployed app, in `dev`, `stg` and `prd`. |
| Goals | Confirm, by using the app, that sign-in, balances, transfers, duplicate protection and history work as the SOW says, and that the application runs on AWS. See the landing page. |
| Pain points | A demo that works only on a developer's laptop. A result he cannot repeat. Unclear differences between environments. |
| Tech comfort | Medium. Not an engineer; follows a short written script. |
| Frequency | A few times during acceptance. |
| Context | A phone with the test build (TestFlight on iOS, Google Play internal testing on Android) and a browser for the landing page. |
| Relationships | Uses the app as two test Wallet Users, one sending to the other. |

Source: SOW "Expected Deliverables" 5 and "Success Criteria"; `requirements.md` FR7 and FR8; `team-practices.md` (Deployment).
