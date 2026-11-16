# logical components — u4-platform

Conversation language: English.

## Components
| Component | Boundary and failure domain |
|---|---|
| Public CloudFront/custom certificate/external DNS | Public TLS, mapped origins and origin-header overwrite; DNS-provider continuity dependency. |
| API edge/WAF/rate adapter | Independent JWT, safe routing/SigV4 and exact verified-caller counters; no financial writes. |
| Cognito pool/native SDK protection | C3 account lifecycle, provider tokens/profile and regional WAF; direct SDK path requires separate proof. |
| C2 bus/consumer/DLQ | Async accepted delivery/recovery; confirmation not coupled to money readiness. |
| Config/secrets | Per-environment C4/C5 and protected origin/correlation references. |
| Monitoring pipeline | Allowlisted public observations/metrics/alarm delivery; incomplete observations never healthy proof. |
Money tables, Directory and transaction adapter remain U2-owned. Infrastructure chooses concrete resources consistent with existing CDK; cost and missing real hostname inputs block paid/live provisioning, not unrelated design work.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
