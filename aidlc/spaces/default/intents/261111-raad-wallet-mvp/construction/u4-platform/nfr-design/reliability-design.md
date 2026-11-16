# reliability design — u4-platform

Conversation language: English.

## Failures and event delivery
C2 accepted confirmation events retry for24h then DLQ and alarm; confirmation itself must not fail solely on publish failure. Consumer uses U2 idempotent wallet-then-directory readiness; PUT safety net repairs loss/partial setup without another opening credit. Test not-accepted publication, accepted retries/duplicates, wrong environment and conflicting receipt.
Missing targets/C5/secret fail closed with stable C1/C5 errors. Outputs environment/URL must agree for all consumers. No fabricated ready status. Config rollback retains existing persistent resources.

## Production recovery
>=99.5% calendar-month service availability; U2 RPO<=5min/RTO<=3h, all3tables/profile versions/outcomes/receipts and retained config restored coherently with measured drill. Dev disposable only explicit reset. No active-active claim. U2 reconciliation is mandatory before cutover; PITR timestamp/stack success is not recovery proof. No implementation/deployment compliance is asserted by these designs.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
