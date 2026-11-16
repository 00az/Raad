# Monitoring Design — U2 Money Service

Conversation language: English.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| Eligible C1 request availability | API edge and MoneyApi outcomes | Monthly production SLO 99.5%; define eligible request set consistently in dashboard | Tracks the approved availability target. |
| C1 request p95 latency | Edge and Lambda custom metric, by operation/status | Warn when p95 exceeds 2 seconds under the approved 10-concurrent-user test; evaluate over 5 minutes | Protects the transfer latency target. |
| Lambda errors and throttles | CloudWatch Lambda metrics | Alarm on sustained errors or any throttles during normal MVP traffic; tune after baseline | Finds handler faults and concurrency caps that block requests. |
| DynamoDB throttles / transaction cancellations | CloudWatch DynamoDB metrics plus service counters | Alarm on throttling; alert on sustained unexpected transaction cancellations after excluding known business conflicts | Detects persistence pressure and anomalous write contention. |
| Transfer persistence failures | MoneyApi custom metric | Any confirmed persistence failure, with 5-minute aggregation | Atomic money movement must fail safely and visibly. |
| C2 retries and DLQ messages | EventBridge/SQS metrics and consumer custom metric | Alarm on any DLQ visible message; trend retries by environment | Detects account setup events that exhausted retries. |
| Business refusals | MoneyApi outcome counters | Dashboard only; exclude normal business refusals from server error alarms | Distinguishes expected outcomes from service failure. |

All custom dimensions are restricted to environment, operation and status. Never dimension by user, email, amount, recipient, transfer reference or idempotency key.

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| API server errors | 5xx rate exceeds 1% for 5 minutes or at least 5 errors in 5 minutes | High | Environment SNS topic; email configured only after account owner supplies it |
| API latency | p95 over 2 seconds for 5 minutes | Medium | Environment SNS topic; supplied monitoring email |
| Lambda throttles | Any throttles sustained across 2 one-minute periods | High | Environment SNS topic; supplied monitoring email |
| DynamoDB throttling | Any read/write throttle over 2 one-minute periods | High | Environment SNS topic; supplied monitoring email |
| Transfer persistence failure | One confirmed failed atomic persistence operation, excluding expected business refusal | High | Environment SNS topic; supplied monitoring email |
| Account-confirmed DLQ | At least one visible message | High | Environment SNS topic; supplied monitoring email; inspect using event ID only |
| C2 retry growth | Retry count rises above the post-deploy baseline for 10 minutes | Medium | Environment dashboard and SNS topic |

Thresholds are initial operational triggers. Calibrate against the approved load test in `stg`; do not weaken the 2-second p95 or 99.5% SLO to quiet alerts. The SNS subscription remains a named external setup input until a real address is provided.

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|---|---|---|
| Eligible production API requests served successfully | 99.5% | Calendar month; publish eligible-request definition with dashboard |
| Transfer request p95 latency at target load | ≤2 seconds | 5-minute rolling windows during load test and ongoing production reporting |
| Persistent-data recovery point | RPO ≤5 minutes | Recovery exercise and after a material data-store change |
| Service recovery time | RTO ≤3 hours | Timed restore exercise; includes validation and traffic cutover |
| C2 event handling | Retry accepted events for up to 24 hours, then expose in DLQ | Per-event lifecycle |

## Logs & Tracing

Use JSON CloudWatch logs with correlation ID, environment, operation, status, duration and opaque caller reference. Do not log bodies, email, display name, token/claims, user ID, amount, cursor, recipient or raw idempotency key. Keep separate log groups by environment; use shorter retention in `dev`, and set `stg`/`prd` retention before deployment. Correlation IDs connect edge and service logs; distributed tracing is deferred for MVP.

## Dashboards

Create one dashboard per environment showing request volume, 4xx/5xx rates, p50/p95 latency against the 2-second target, Lambda concurrency/errors/throttles, DynamoDB throttles/cancellations, transfer success and refusal counts, C2 retries/DLQ depth, and production availability/SLO history. Display balances only as aggregate service outcomes; never expose individual user or transaction values.

## Sources

This monitoring design implements `observability-design.md`, `performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md` and `logical-components.md`. Metric boundaries follow `components.md` and `functional-spec.md`; event and API ownership follows `contract-summary.md`.
