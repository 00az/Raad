# reliability design — u3-mobile-app

Conversation language: English.

## Financial intent and uncertainty
All money parses/formats through integer halalas, no float; test range100–50000, zero/negative, overprecision, long input and exact-balance boundaries. Preserve authoritative server result. Double-tap suppression plus durable immutable key before send prevents accidental second intent. U1 lost-response uncertainty blocks resubmit and requires reconciliation; only full U2 capability enables user-initiated same-key replay with identical payload. Restart restores protected pending intent without automatic send.
Offline/failing reads show timestamped stale data or explicit error when absent; never zero/success placeholders. UTC instants preserve deterministic server sort; device-local display and DST/locale changes cannot alter amount/key. Retry only the performance-design permitted methods. Test process death at before-send, possible-commit, after-response and session-switch boundaries.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
