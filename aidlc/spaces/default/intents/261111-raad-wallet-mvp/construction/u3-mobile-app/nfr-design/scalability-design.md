# scalability design — u3-mobile-app

Conversation language: English.

## Bounded device state
One in-flight request per control, bounded page window, no write queue on navigation/restart. Cursor chain preserves server ordering and rejects duplicate load-more. Separate service capacity from rendering; no client cache authorizes a balance. Test 1000-entry history with bounded widget/request growth and both locales; no additional client throughput SLO.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
