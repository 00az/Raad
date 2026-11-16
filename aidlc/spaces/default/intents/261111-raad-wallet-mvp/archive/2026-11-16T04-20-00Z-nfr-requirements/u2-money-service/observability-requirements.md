# Observability Requirements — U2 Money Service

Conversation language: English.

## Signals, Dashboard, and Alarms

| ID | Requirement | Acceptance |
|---|---|---|
| NFR8.1 | Each environment has a service dashboard with request volume, 4xx/5xx rates, p50/p95 latency, throttles, dependency failures, transfer successes, and safe business-refusal counts. | The dashboard separates expected business refusals from unexpected service failures. |
| NFR8.2 | Each environment alarms on server errors, slow responses, and failed transfer persistence/processing. | In `stg`, controlled conditions move the corresponding alarm to ALARM and a notification reaches the configured monitoring email. The email is an explicit environment input and remains unset until supplied. |
| NFR8.3 | C1 latency is measured at the API boundary and reports p95 against the 2-second target; production availability is reported monthly against 99.5%. | Dashboard and monthly report use the same eligible request definition and environment labels. |
| NFR8.4 | C2 retry exhaustion, invalid event payloads, and dead-letter movement are visible and alarmed using event ID and environment only. | A synthetic failed event produces an alarm with no email, display name, token, or full user ID in telemetry. |
| NFR10.1 | Logs carry correlation ID, environment, operation, status, duration, and a safe opaque caller reference. | Automated log scan finds no password, token, email, display name, or full user ID. |

## Operational Signals

Transfer metrics must not include amount, recipient address, or any user-level dimension. Alert thresholds and the monitoring destination are configured per environment in Infrastructure Design; they are not invented in this requirements document.
