# logical components — u2-money-service

Conversation language: English.

## Inventory and ownership
| Component | State/failure domain | Responsibility and isolation |
|---|---|---|
| Shared U4 edge | Per environment | Origin-secret check, independent bearer verification, rate policy and SigV4; no balances. |
| MoneyApi | Stateless bounded compute | C1 validation/orchestration; independently authorized subject, safe responses. |
| Ledger transaction adapter | Ledger + canonical Transactions atomic boundary | Sole financial writer; balances, immutable outcomes/receipts/reference markers; one canonical transfer row and projected history indexes. |
| WalletDirectory adapter | Directory table | Unique ownership, personal profile and immutable versions; no balance writes. |
| C2 consumer | Per-environment retry/DLQ | Same setup workflow and receipt rules; no second credit. |
| C5 profile / secrets | SSM / Secrets Manager | Isolated verifier profile, origin and correlation secrets; fail closed. |
| U4 monitoring | Per-environment signals | UTC privacy-safe diagnostics and complete public SLO evidence. |

## Failure and handoff boundaries
Wallet commit and Directory readiness are sequential with repair, not a cross-component setup transaction. Profile version is durable before the Ledger references it; unreferenced versions on precommit failure are harmless and contain no financial event. Losing Directory availability blocks profile resolution and replay reconstruction, never makes a new transfer. Canonical transaction writes remain atomic across Ledger and Transactions in one account/region. C2 delivery is outside confirmation latency.
Infrastructure supplies real table names, role ARN, verifier/pool/client outputs, secret references, event source/DLQ, hostname/certificate and alarm channel. No fake values constitute deployable readiness. Shared C1/C2/C5 remain authoritative; revisions describe design obligations, not completed implementation.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design/functional-spec.md and rules.md; shared inception/contract-design/contract-summary.md and domain-design/components.md; U1 nfr-design/nfr-design-questions.md (free DNS decision b8664859). No target is lowered by this revision.
