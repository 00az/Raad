# logical components — u5-landing-page

Conversation language: English.

## Inventory
| Component | Responsibility and failure isolation |
|---|---|
| ar/en documents | Public intro, language switch and approved contact; no financial authority. |
| Local stylesheet/assets | Accessible reflow/focus/RTL and cacheable presentation; no external tracking dependency. |
| Static publication/CDN | Per-environment immutable deploy/rollback, controlled hostname/TLS policy. |
No runtime API, authentication, database, analytics or payment component. A failed publication cannot mutate money.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
