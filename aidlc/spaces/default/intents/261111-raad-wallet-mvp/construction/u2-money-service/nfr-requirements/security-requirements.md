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
| NFR11.1 | Per user, retain only email and display name as personal attributes in WalletDirectory-owned current holders and immutable profile versions, plus required opaque associations. Ledger's replay outcomes contain only non-personal business fields and an opaque profile-version reference. Collect no identity document, card, or bank detail. | Review the data model and stored test records. |
| NFR11.2 | Never connect to payment rails or accept real card/bank details; all balances and transfers remain simulated SAR. | API schemas and dependency inventory contain no real-payment integration. |

## Error and Abuse Boundaries

| ID | Requirement | Acceptance |
|---|---|---|
| NFR9.1 | Every error uses the C1 structured error shape with a stable code and safe message; no stack trace, internal resource name, or personal data is returned. | Force validation, authorization, timeout, persistence, and unexpected failures and inspect every response body. |
| NFR12.1 | U2 is reachable publicly only through the shared platform edge and honors its per-caller rate-limit decisions. Return the contract's 429 response without bypass paths. | Burst tests through the edge refuse an over-limit caller while another caller remains unaffected. Numeric rate thresholds are owned by U4 and are set in its design. |
| NFR12.2 | Validate request body sizes, email normalization, integer shape, cursor bounds and key syntax before persistence. Distinguish malformed/non-integer amounts (400/no consumed key) from integer business-range refusals (422/final outcome after unknown-recipient precedence). | Invalid schema/oversized input causes no write; valid-schema business refusals save exactly the first result under the C1 matrix. |

## Replay profile and origin boundary

| ID | Requirement | Acceptance |
|---|---|---|
| NFR11.3 | Original replay profile fields come only from an immutable WalletDirectory version referenced by the authenticated caller's saved outcome. Current-profile edits never rewrite historical replay. Retain referenced versions for the outcome lifetime. | Test profile changes, unauthorized version access, missing/corrupt versions and pre-commit failures. Ledger and canonical Transactions contain no email/name, and unavailable replay data never triggers another movement. |
| NFR1.4 | C5 actual token/profile compatibility is verified against the selected SDK flow, with independent JWT and profile-subject checks. | Real provider capability/public PUT/GET plus negative mismatch/unavailability tests; synthetic JWT tests are labelled local evidence. |

## Scope

The MVP has no SAMA/PDPL certification or data-residency requirement. The service stores the minimum personal data above and uses the account's selected AWS region. Secrets and credentials are not embedded in source, images, logs, or deployment artifacts.
