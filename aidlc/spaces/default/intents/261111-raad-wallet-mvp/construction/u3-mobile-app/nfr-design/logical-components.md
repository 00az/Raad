# logical components — u3-mobile-app

Conversation language: English.

## Components and failures
| Component | Responsibility | Failure isolation |
|---|---|---|
| Session/C4 adapter | Environment-bound credentials and endpoints | Invalid config/session blocks private navigation and network. |
| Money client | Pinned C1 schemas and bounded deadlines | Safe localized failures; no client-owned balances. |
| Intent store | Protected account/key/payload | Failure to persist blocks send; no automatic replay. |
| Screen state controllers | Epochs, pages and authoritative snapshots | Late response cannot cross account/navigation boundary. |
| Locale/accessibility layer | ar/en, RTL/LTR isolation and semantic state | Locale changes preserve intent; missing translation fails catalog checks. |
No server store or payment processor is added. Native iOS/Android release adapters require independent device proof.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
