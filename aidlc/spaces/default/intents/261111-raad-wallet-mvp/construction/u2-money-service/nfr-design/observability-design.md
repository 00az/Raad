# observability design — u2-money-service

Conversation language: English.

## Signals and privacy
Use shared U4 alarm windows and public SLO calculations below; preserve U1 public-boundary completeness checks. Metrics dimensions only environment/operation/status; counts, technical error rate, public latency, Lambda/Dynamo throttles, atomic failures, C2 retries/DLQ, and observation loss. Business refusals are separate. Structured UTC logs allow environment/operation/status/duration and protected correlation only. Apply the approved cross-runtime HMAC profile to caller-controlled correlation before logging; no raw user IDs, email/name, payload, amount, token, key, cursor, or fingerprint. No distributed tracing backend.

## Alarm policy
Technical 5xx rate >=1% with >=20 eligible requests in each of two consecutive 5-minute windows; also >=3 technical transfer failures per 5 minutes in two windows. Public p95 >2000 ms requires >=20 eligible samples/window and complete reconciliation, two consecutive 5-minute windows. Insufficient samples/completeness => INSUFFICIENT_DATA, never healthy; separate missing-observation/heartbeat alarm. Lambda or Dynamo throttles >=1 in two consecutive 1-minute windows; any DLQ message >=1 in one minute. Missing collector heartbeat >=3 minutes alarms. Recovery requires three consecutive complete healthy windows; DLQ recovery additionally requires operator reconciliation, never automatic deletion.
Deliver to jjii0@hotmail.com; subscription confirmation and stg fault/recovery delivery are unverified release evidence. Retain dev logs 14 days and stg/prd 30 days as proposed implementation settings, subject to infrastructure validation; no personal log retention.

## Availability and evidence
Monthly production report uses the approved eligible-request definition, includes maintenance, counts platform/dependency technical failures as unavailable; safe business refusals are successful service responses. During idle periods, execute a once-per-minute nonfinancial authenticated wallet-read probe using a restricted fixture account; report synthetic coverage separately and mark coverage gaps unknown. Do not blend synthetic counts into traffic SLI or assert a healthy empty month. Public latency missing/duplicate/conflicting observations fail acceptance after two-minute reconciliation grace. Dashboards show all windows/sample counts/completeness and measured recovery drill status.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design/functional-spec.md and rules.md; shared inception/contract-design/contract-summary.md and domain-design/components.md; U1 nfr-design/nfr-design-questions.md (free DNS decision b8664859). No target is lowered by this revision.
