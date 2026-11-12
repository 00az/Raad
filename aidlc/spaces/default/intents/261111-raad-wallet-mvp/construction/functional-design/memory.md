# Functional Design — Stage Diary

Stage started: 2026-11-12T17:55:00Z
Unit: u1-walking-skeleton

## Context loaded
- unit-of-work.md: U1 responsibilities — sign-in check, wallet safety net, balance, recipient lookup, one transfer, first history page, sign-in pool + API domain in Raad, app screens for sign-in/wallet/send/history
- unit-of-work-story-map.md: U1 stories: US1.2 (wallet open via safety net), US1.3 (sign-in), US2.1 (balance), US3.1 (transfer), US3.2 (review), US3.4 (balance check), US4.1 (history), US4.2 (received), US6.1 (smoke/integration test), US6.4 (opening balance)
- stories.md: acceptance criteria for each story loaded
- requirements.md: FR1–FR8, NFR1–NFR15
- components.md: MobileApp, MoneyApi, Ledger, WalletDirectory entities and boundaries
- contract-summary.md: C1 (MoneyApi REST), C3 (sign-in behavior profile)

## Artifacts written
- entities.md: Wallet, Transfer, WalletHolder entities (Ledger/WalletDirectory scope for U1)
- rules.md: BR groups 1 (sign-in), 2 (wallet), 3 (transfer), 4 (history)
- functional-spec.md: workflows for sign-in check, wallet setup, balance, send flow, history
- frontend-components.md: SignInScreen, WalletScreen, SendFlow (form/review/result), HistoryScreen
- traceability.json: all U1 ACs mapped
