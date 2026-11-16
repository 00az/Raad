# observability design — u4-platform

Conversation language: English.

## Shared alarm and SLO policy
Apply U2 observability-design exact windows: technical5xx>=1% with>=20eligible requests per5min in2windows, technical transfer failures>=3/5min in2windows, complete publicp95>2000ms with>=20samples/5min in2windows; throttles>=1/min in2windows; anyDLQ>=1/min. Collector heartbeat absent3min alarms. Three complete healthy windows recover ordinary alarms; DLQ needs operator reconciliation. Insufficient samples/completeness =>INSUFFICIENT_DATA, separate observation-health alarm, never a passing SLO.
Per-environment dashboard: requests/refusals/technicalerrors/publiclatency/cold-start diagnostics/throttles/transactions/DLQ/observationcoverage and monthlyavailability. Real-time CloudFront logs selected100% but best-effort delivery; reconcile every eligible response, deduplicate requestID, conflicting/lost/late data after2min fails latency acceptance. Logs are not a guaranteed-complete source by themselves.
Availability traffic SLI counts eligible requests, includes maintenance/technicaldependencyfailure; separate minute nonfinancial authenticated wallet probes establish idle coverage without blending traffic counts. Unknown intervals/months stay unknown.

## Privacy and delivery
UTC JSON allowlist with approved HMAC-protected correlation; never raw caller-controlled identifiers, bodies, queries, credentials/email/name. No personal/high-cardinality metric dimensions; no tracing backend. Proposed retention14daysdev/30stg-prd validated in infrastructure. Alarm destination jjii0@hotmail.com; actual confirmation and stg breach/recovery email evidence required. Public contact abdulaziz.alrubai@outlook.com is separate. Do not send notification tests until the explicitly authorized deployment/verification action.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
