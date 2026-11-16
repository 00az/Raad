# Observability Design — U2 Money Service

Conversation language: English.

## Metrics and Dashboards

Publish low-cardinality metrics by environment, operation, and status: request count, 4xx/5xx count, p50/p95 latency, Lambda throttles/concurrency, dependency latency/failures, DynamoDB throttles/transaction cancellations, successful transfers, safe business refusals, C2 retry attempts, and dead-letter count. Do not dimension metrics by user, email, amount, recipient, transfer ID, or idempotency key.

Create one dashboard per environment with these service metrics, the C1 p95 target (2 seconds), and production monthly availability (99.5%). Business refusals remain visible but do not count as server errors. Failed persistence and C2 dead-letter cases are separate signals.

## Logs and Correlation

Emit structured JSON logs with correlation ID, environment, operation, status, duration, and a non-reversible opaque caller reference. The public edge forwards or creates a correlation ID; the service validates its format and echoes it in C1 responses. Never log request/response bodies, email, display name, token, full user ID, amount, recipient, cursor, or raw idempotency key. Use CloudWatch Logs retention per environment, with shorter `dev` retention and the agreed production retention set in Infrastructure Design.

## Alarms and SLO Reporting

Alarm on server errors, p95 latency above 2 seconds, Lambda throttles, DynamoDB throttles, failed atomic transfer persistence, and C2 dead-letter movement. Define thresholds and evaluation windows from the approved 10-concurrent-user load check; avoid alerting on normal business refusals. Send notifications to the per-environment monitoring email only after the account owner supplies it. The email is an external setup input and must not be guessed.

Report availability monthly using the same eligible request definition as the 99.5% SLO. In `stg`, exercise each alarm and confirm the right channel receives it. No distributed tracing system is added for the MVP; correlation IDs link edge and service logs, and trace adoption can be reconsidered if cross-service diagnosis needs it.

## Sources

`observability-requirements.md`, `security-requirements.md`, `performance-requirements.md`, `contract-summary.md`, and `tech-stack-decisions.md` define the metrics, privacy, correlation, and alarm targets.
