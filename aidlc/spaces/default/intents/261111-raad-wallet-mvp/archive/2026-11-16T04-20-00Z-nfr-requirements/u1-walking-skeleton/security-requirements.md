# Security Requirements: U1 Walking Skeleton

Conversation language: English.

## Scope and trust boundaries

The skeleton uses confirmed test accounts, the shared sign-in service, the public money API edge, MoneyApi, Ledger, WalletDirectory and the mobile app on dev. Funds are simulated and SAR is the only currency. The approved demo has no SAMA/PDPL certification requirement, Middle East residency requirement, real payment integration or MFA work.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR1.1 | Every wallet read, history read, setup and transfer requires a valid access token. The edge and MoneyApi each apply C5's signature, issuer, audience binding, expiry, not-before-if-present, token-type and RS256 checks. | Negative tests cover missing, invalid, expired, wrong-type, wrong-environment and incorrectly signed tokens at both boundaries. No wallet data is returned. |
| NFR1.2 | MoneyApi takes the caller only from the independently verified subject. Request fields and spoofed identity headers cannot select a source wallet or another user's history. | Exercise identity/header spoofing and cross-user access attempts; every attempt returns no unauthorized data. |
| NFR1.3 | Wallet-setup email and display name come only from the verified sign-in profile source named by C5, with the subject checked when the own-profile endpoint is used. | Prove C3 capability checks P1, P2 and P13 on dev in U1 Infrastructure Design, and test the selected profile source. |
| NFR1.4 | Verifier configuration is immutable deployment input for the environment. Missing, malformed or cross-environment values fail closed. Key discovery follows C5's bounded refresh and cache policy. | Test invalid configuration, unknown key identifiers, rotation, discovery failure with a usable cache and discovery failure without one. The last case returns 503 TOKEN_VERIFIER_UNAVAILABLE, not an authentication failure. |
| NFR2.1 | App, sign-in, edge and service traffic uses TLS 1.2 or later. Plain HTTP cannot authorize or move money. | Inspect endpoint configuration and probe HTTP/TLS behavior without exposing credentials. |
| NFR2.2 | Persisted wallet, dedicated Transactions table, holder and operational data is encrypted at rest using AWS-managed key infrastructure. | Infrastructure assertions and deployed-resource inspection show encryption enabled for every selected persistent store, including Transactions. |
| NFR2.3 | Mobile access and refresh tokens use phone secure storage. Passwords, codes and tokens never enter the repository, API URLs, telemetry or logs. | Inspect storage integration and run a secret/log scan using recognizable test values. |
| NFR10.1 | No password, token, code, email address or display name appears in logs, metric dimensions, alarms or traces. Opaque user identifiers and correlation IDs are permitted under the existing rules. | Scan logs and alert payloads from successful, refused and failed requests for the test credentials and profile values. |
| NFR11.1 | Email and display name are the only personal attributes collected. Ledger keeps opaque identifiers and money data; WalletDirectory owns profile data. Transactions rows retain transferId and wallet references, never email, display name, credentials or tokens. | Inspect schemas, request handling and stored test records, including both wallet references on one immutable transaction row. No card, bank, identity-document or additional profile field is accepted. |
| NFR12.1 | U1 retains its basic public API firewall and fails safely on edge refusal. It does not introduce U4's complete account-operation, recipient-lookup or per-caller rate-limit implementation. | Check that U1's edge is protected and that configured refusals carry C1-safe errors. Trace the complete per-caller protections to U4 and their service-side integration to U2. |
| NFR14.1 | No credentials are committed. Laptop AWS access uses the affirmed sign-in mechanism and deployment uses short-lived CI credentials. Infrastructure security checks remain mandatory. | Run repository secret checks and the established dependency/CDK checks; inspect CI authentication configuration when it is built. |

## Error disclosure

C1 errors contain stable code, safe message and correlationId, with optional field errors. The app branches on code, never provider text. Responses and logs reveal no stack trace, internal route, token or personal detail. Unknown recipient handling follows the approved C1 boundary and the accepted account-enumeration decision; this stage does not introduce a new privacy behavior.

## Deferred work

Sign-up, confirmation/resend, password reset, session renewal and full account-operation abuse limits remain assigned to U3/U4. The event-confirmation path remains U2/U4. The monitoring destination and concrete infrastructure choices remain inputs to their existing design stages.

Functional Design specifies explicit PUT wallet setup and repair, exact C1 public fields and the Idempotency-Key header, and verified identity from C5. These requirements inherit that behavior. U1 remains a partial C1 pre-release without saved replay outcomes; this does not alter the completed C1 guarantee assigned to U2.

## Sources

- construction/u1-walking-skeleton/functional-design/functional-spec.md: sign-in, setup, money and history boundaries.
- construction/u1-walking-skeleton/functional-design/rules.md: BR1.1, BR1.2, BR5.1 and BR6.1.
- inception/requirements-analysis/requirements.md: NFR1, NFR2, NFR9 to NFR12 and NFR14; Q7 demo constraints.
- inception/contract-design/contract-summary.md: C1 caller identity/errors, C3 profile and P-checks, C5 token verification.
- aidlc/spaces/default/memory/team.md and project.md: credential, logging, simulated-money and security-check rules.
- inception/units-generation/unit-of-work.md: U1 versus U2/U3/U4 responsibilities.
