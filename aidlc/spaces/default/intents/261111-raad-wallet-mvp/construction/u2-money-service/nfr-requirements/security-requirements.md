# Security Requirements — U2 Money Service

Conversation language: English.

## Identity and Authorization

| ID | Requirement | Acceptance |
|---|---|---|
| NFR1.1 | Every wallet, recipient, transfer, and history operation requires a valid C5 token; reject missing, invalid, or expired tokens. | Requests without a valid token return the stable authentication error and no wallet data. |
| NFR1.2 | Derive the owner exclusively from the verified subject claim. Never accept a caller-selected user or wallet ID as authority. | Attempts to read or change another user's wallet are refused without returning data. |
| NFR1.3 | Verify token signature, issuer, audience, and environment against the non-secret C5 verifier configuration; reject cross-environment identity. | Wrong issuer, audience, or environment fails closed. |

## Data Protection and Privacy

| ID | Requirement | Acceptance |
|---|---|---|
| NFR2.1 | All service API traffic uses TLS 1.2 or later. | Plain HTTP is refused or redirected at the owning edge; service invocations are authenticated and encrypted in transit. |
| NFR2.2 | Every persistent service store is encrypted at rest with AWS-managed or customer-managed KMS keys. | Infrastructure checks report encryption enabled for each store. |
| NFR11.1 | Per user, retain only email and display name in WalletHolder in addition to the opaque identity key required to associate owned money records. Collect no identity document, card, or bank detail. | Review the data model and stored test records. |
| NFR11.2 | Never connect to payment rails or accept real card/bank details; all balances and transfers remain simulated SAR. | API schemas and dependency inventory contain no real-payment integration. |

## Error and Abuse Boundaries

| ID | Requirement | Acceptance |
|---|---|---|
| NFR9.1 | Every error uses the C1 structured error shape with a stable code and safe message; no stack trace, internal resource name, or personal data is returned. | Force validation, authorization, timeout, persistence, and unexpected failures and inspect every response body. |
| NFR12.1 | U2 is reachable publicly only through the shared platform edge and honors its per-caller rate-limit decisions. Return the contract's 429 response without bypass paths. | Burst tests through the edge refuse an over-limit caller while another caller remains unaffected. Numeric rate thresholds are owned by U4 and are set in its design. |
| NFR12.2 | Validate request body sizes, email normalization, integer halala amounts, cursor bounds, and idempotency-key shape before persistence. | Invalid or oversized inputs are rejected without unbounded work or state changes. |

## Scope

The MVP has no SAMA/PDPL certification or data-residency requirement. The service stores the minimum personal data above and uses the account's selected AWS region. Secrets and credentials are not embedded in source, images, logs, or deployment artifacts.
