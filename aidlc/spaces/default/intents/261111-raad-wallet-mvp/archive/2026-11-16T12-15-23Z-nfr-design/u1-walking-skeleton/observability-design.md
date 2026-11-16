# Observability Design: U1 Walking Skeleton

Conversation language: English.

## O1 — Measurement ownership

The platform edge measures total public request duration from complete request receipt through response completion, status and bounded route/operation. MoneyApi measures operation/result and dependency duration; Ledger records committed/aborted/unknown technical outcome without personal data. Do not sum component p95 values to invent end-to-end p95. The edge must emit the total-latency histogram used by the transfer SLI, including verification and upstream waiting. Infrastructure Design maps that boundary to actual instrumentation and proves it with a controlled delayed request.

Track request count, response status, public transfer-latency distribution, valid-transfer successes, business refusals, technical transfer failures and unknown outcomes separately. A known business refusal is not a technical transfer failure, and a 5xx/timeout is not a successful transfer. Edge failures before MoneyApi entry remain visible in edge request/server-error counts; a missing service log is not a successful request. Client-observed no-response results are captured by the safe load/smoke report because server logs alone cannot prove delivery to the caller.

Where an authorized investigation has the completed transferId, reconcile the API result with the one immutable Transactions row and both parties' history items. Wallet IDs are references and never substitute for a transfer identity. U1 has no saved request-key outcome to consult; an uncertain response is not a definitive refusal or proof of rollback. A diagnostic operation must never re-execute the transfer.

## O2 — Logs, metrics and UTC

Structured JSON log fields are the security-design.md S4 allowlist. UTC timestamps use an explicit offset and refer to real instants. Transfer completedAt and operational time remain UTC; the app formats the same transfer instant in the device time zone without changing order.

X-Correlation-Id follows C5 from edge to MoneyApi, response header and error body. Preserve a valid caller value, but treat it as untrusted text: it is non-unique, may be reused and may contain a recognizable personal value even within the permitted syntax. It is never a metric dimension or alarm field. For logs, use an environment-keyed one-way HMAC of the correlation ID as correlationKey at every layer; an authorized local troubleshooting tool computes the same value from a reported response ID without logging that ID. The selected secrets store supplies the environment-specific HMAC key to the logging integration. C5 request/response values remain unchanged. Infrastructure Design must prove that both edge and service logs can produce the same protected correlationKey; a raw platform request ID may be used as an additional non-caller-controlled diagnostic identifier. If the selected edge cannot meet this, flag the capability gap before implementation rather than enabling raw correlation logging. HMAC key rotation preserves a bounded previous key for investigating the retained logs; key versions are logged, keys are not.

Metrics have only environment, component, operation and bounded result/error categories as dimensions. No email, display name, token, opaque user ID, transfer ID, correlation ID or arbitrary URL is a dimension. Log no payloads, raw SDK errors or credential/profile values. Use route templates, never raw URLs containing user input. Transfer totals are operational counts, not an additional personal-data ledger. Distributed tracing and a tracing backend remain outside scope.

Dev operational logs initially retain 14 days; audit/money records remain separate and are not expired by this logging policy. Fourteen days is a proposed operational configuration, not a new product/data-retention promise. Infrastructure Design sets explicit retention on every selected log destination. Metrics/dashboard retention follows the chosen monitoring service and must be documented. Never put personal data into long-lived metrics.

## O3 — Initial dev alarms

Evaluate the following rules per environment, using UTC windows. These are initial operational settings to be approved with this design; they do not replace the 10-minute acceptance load check or add an availability SLA to dev.

| Alarm | Trigger | Minimum data | Recovery |
|---|---|---|---|
| Server errors | At least 3 edge 5xx responses in each of 2 consecutive 1-minute periods | At least 3 requests in each breaching period | 2 consecutive non-breaching 1-minute periods |
| Slow transfers | More than 5% of transfer responses exceed 2,000 ms in each of 2 consecutive 5-minute periods | At least 20 transfer responses per period | 2 consecutive eligible non-breaching 5-minute periods |
| Technical transfer failure | At least 1 technical transfer failure or unknown outcome in a 1-minute period | At least 1 transfer attempt; include edge upstream timeout/unreachable outcomes | 2 consecutive non-breaching 1-minute periods |

For the slow alarm, use the public transfer-response histogram including cold/error responses and show valid-transfer success beside it; errors never improve the acceptance result. Where multiple layers observe one failure, the alarm uses the edge outcome as its request count and does not double-count MoneyApi's diagnostic count. The selected platform must map unavailable/timeout outcomes to a measured 5xx or an explicit edge failure metric. Count a connection failure that prevents any edge response in the external test report separately.

Treat missing samples and an ineligible low-volume slow window as “insufficient data,” not a breach or evidence of health. Count alarms may return to non-breaching after empty windows, but the dashboard must explicitly label no traffic and must not derive availability from those windows. Send email on entry to alarm and recovery; do not repeatedly email an unchanged state. Payloads contain only environment, alarm category, window, aggregate value and an authenticated dashboard link. No user, correlation ID or financial amount is included.

The monitoring email is supplied in Infrastructure Design, through environment configuration; it is not invented or committed here. Delivery confirmation/subscription and a controlled injection of each alarm category are required before claiming monitoring works. Verify slow alarms with sufficient samples for both breaching windows and recovery windows. The email is the team's escalation destination; no new on-call rota or paging service is added. Later stages still owe stg notification evidence under inception NFR8.

## O4 — Dashboard and diagnostic procedure

Show request volume and status breakdown, technical transfer success/refusal/failure counts, public p50/p95 latency, fraction over 2 seconds with sample count, active/admitted requests and admission refusals, dependency failures, and the three alarm states. Show environment and selected time window prominently. Include a “no traffic / insufficient samples” label rather than displaying zero latency as success.

To investigate: identify the environment and response correlation ID from the user's safe report; compute correlationKey with the authorized tool; follow edge and MoneyApi logs; examine aggregate dependency/status metrics; inspect committed transfer records only through authorized access. An uncertain transfer must not be re-executed as a diagnostic action. A dashboard is observability evidence only after real dev traffic is visible, privacy scans pass and alarm delivery is tested.

## O5 — Verification and later handoff

Tests prove consistent protected log correlation for service success, edge refusal and service failure; matching public response/error correlation IDs; no fixture personal values in logs/metrics/alerts; UTC persistence/device-local display; sample gating; alarm entry/recovery; and notification delivery. Fault injection uses synthetic fixtures and controlled low-volume outages/delays. It never changes real financial systems or deletes dev data.

The production availability SLI remains successful eligible valid requests divided by eligible requests per calendar month, with maintenance included. A separate no-traffic measurement design is required before production is claimed; U1 introduces no synthetic monitoring service or endpoint. All thresholds and privacy transformations above are design decisions, not executed results.

## Sources

- construction/u1-walking-skeleton/nfr-requirements/observability-requirements.md: NFR8.1–8.3, NFR10.2 and NFR15.1.
- construction/u1-walking-skeleton/nfr-requirements/performance-requirements.md: NFR6.1–6.3 and boundary latency.
- construction/u1-walking-skeleton/nfr-requirements/security-requirements.md: NFR10.1 and personal-data restrictions.
- construction/u1-walking-skeleton/nfr-requirements/reliability-requirements.md: dev recovery policy and uncertain outcomes.
- construction/u1-walking-skeleton/functional-design/functional-spec.md: operations, transfers and UTC history.
- inception/contract-design/contract-summary.md: C1 safe errors, C5 correlation ID and privacy requirements.
