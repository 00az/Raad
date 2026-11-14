# Logical Components — U2 Money Service

Conversation language: English.

## Component Inventory

| Component | Responsibility | State / failure domain | Isolation and blast radius |
|---|---|---|---|
| Shared Public Edge (external U4) | Public `/money` routing, firewall/rate limits, SigV4 invocation. | Per-environment edge and IAM role. | Edge failure blocks public API but cannot directly change ledger state. |
| MoneyApi Lambda | C1 request handling, C5 token verification, validation, orchestration, safe errors. | Stateless compute, bounded concurrency per environment. | A handler failure affects its request; retries use the same durable request key. |
| Ledger Store | Wallet balances, transfers, idempotency outcomes, event receipts, sent/received history views. | Environment-specific DynamoDB table, transactional writes and point-in-time recovery. | Transfer transaction confines mutation to sender, recipient, and their history; no cross-user read authority. |
| WalletDirectory Store | Unique user/email ownership, display names, normalized email index. | Environment-specific DynamoDB table. | Directory outage blocks recipient resolution and wallet setup; it cannot independently change balances. |
| C2 Event Consumer | Idempotent account-confirmed wallet/holder setup. | Per-environment event source, bounded retry, dead-letter destination. | Event delay/loss does not block confirmation; C1 `PUT /wallet` is the recovery path. |
| C5 Verifier Configuration | Issuer, audience, JWKS/verifier endpoint and environment profile. | Environment-scoped non-secret SSM parameter; public keys cached to expiry. | Missing/mismatched config fails closed for API traffic. |
| Correlation Secret | Protect correlation ID signing/verification where required by C1/C5. | Environment-scoped Secrets Manager secret. | Secret retrieval failure returns safe service error; no key material is logged. |
| CloudWatch Signals | Structured logs, low-cardinality metrics, dashboard, alarms. | Per-environment log groups and alarm resources. | Monitoring failure does not affect money data path; alarms cover inability to observe service health. |

## Data and Failure Boundaries

MoneyApi is the only writer of balances and transfer outcomes. The Ledger and WalletDirectory are separate logical stores but participate together in the wallet-setup transaction; a setup either creates the wallet, holder, and receipt as a consistent set or none. A transfer transaction uses only the Ledger Store and does not call another RAAD service. The edge owns public abuse controls; the service independently validates identity and data. C2 is asynchronous and never participates in a mobile request's success path.

## External Inputs

Infrastructure Design must supply each environment's edge role, C5 issuer/audience/JWKS settings, secret ARN, monitoring email, table names, event source/DLQ, and recovery configuration. These are not embedded as credentials in application code.

## Sources

`components.md`, `contract-summary.md`, `functional-spec.md`, all six U2 NFR Requirements artifacts, and `tech-stack-decisions.md` define the boundaries and applicable quality requirements.
