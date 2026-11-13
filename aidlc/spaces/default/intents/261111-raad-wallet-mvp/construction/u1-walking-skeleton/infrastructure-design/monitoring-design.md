# Monitoring Design — U1 Walking Skeleton

Conversation language: English.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| Public API request count and status | API Gateway and edge adapter | Report counts by environment, component, bounded operation and result; never by caller | Shows traffic and failures at the public boundary. |
| Public transfer duration | Edge adapter complete-request timer, emitted as a CloudWatch distribution | p95 at or below 2,000 ms for the combined idle-start and sustained load populations and for the sustained population; retain cold-start samples | Measures the approved end-to-end latency target without summing component percentiles. |
| Valid funded transfer success | MoneyApi and edge outcome counters | Every valid funded transfer in the performance run succeeds | Keeps business refusals and technical failures distinct from valid success. |
| Technical transfer failures and unknown outcomes | MoneyApi result counters and edge upstream timeout/unreachable counters | Any failure or unknown outcome is visible; a transfer timeout is never reported as a confirmed abort | Flags uncertain money outcomes without suggesting a retry. |
| Edge 5xx count | API Gateway/edge adapter | Three or more in each of two consecutive one-minute windows | Detects public-path failures with minimum sample gating. |
| Slow transfer fraction | Edge transfer-duration distribution | More than 5% over 2,000 ms in each of two consecutive five-minute windows, with at least 20 responses per window | Detects sustained latency degradation while keeping insufficient samples distinct. |
| Admitted requests and capacity refusals | Edge adapter and MoneyApi | Investigate at 80% of the configured concurrency limit for three consecutive one-minute periods; any refusal at the approved load is investigated | Checks the candidate 20-request envelope and exposes admission pressure. |
| Dependency failures and duration | MoneyApi dependency instrumentation | Diagnostic only; operation deadlines remain those in performance-design.md | Finds store, profile and key-discovery bottlenecks without hiding public latency. |
| Correlation-key match rate | Edge and MoneyApi structured logs | Expected same key version and value for paired requests | Confirms logs can be joined without storing the caller-provided correlation ID. |

Metric dimensions are limited to `Environment`, `Component`, `Operation` and bounded `Result`/`ErrorCode`. Do not emit email, name, token, wallet ID, transfer ID, caller correlation ID, arbitrary URL or raw exception as a dimension. Publish the edge duration as a distribution and use CloudWatch percentile statistics; the alarm uses the same complete public sample population as the acceptance report.

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| Server errors | At least 3 edge 5xx responses in each of 2 consecutive 1-minute periods, with at least 3 requests in each breaching period; recover after 2 consecutive non-breaching periods | Warning | Environment SNS topic subscribed to the team monitored email |
| Slow transfers | More than 5% of transfer responses exceed 2,000 ms in each of 2 consecutive 5-minute periods, with at least 20 responses per period; recover after 2 eligible non-breaching periods | Warning | Environment SNS topic subscribed to the team monitored email |
| Technical transfer failure | At least 1 technical transfer failure or unknown outcome in a 1-minute period; includes edge upstream timeout/unreachable. Recover after 2 consecutive non-breaching periods. | High | Environment SNS topic subscribed to the team monitored email |

Use CloudWatch alarms with explicit evaluation periods and metric math for the counts/fractions. Configure missing data as `missing`, never as success; low-volume slow windows remain insufficient data. Send notifications on alarm entry and recovery, not on every evaluation. Email alarm payloads contain environment, alarm category, UTC window, aggregate value and an authenticated dashboard link only. Do not include correlation IDs, user identifiers or financial amounts. Provision the email address as an environment parameter, confirm its SNS subscription, and inject a controlled synthetic signal for each alarm before claiming delivery works.

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|---|---|---|
| Valid funded transfer public latency | p95 no greater than 2,000 ms; evaluate both the combined idle-start plus sustained population and the sustained population independently | 10-minute accepted dev load run, with at least 200 valid funded transfer attempts and all cold/failed samples retained |
| Valid funded transfer completion | 100% of valid funded transfer attempts in the acceptance run complete successfully | Same run; record technical failures and unknown outcomes separately |
| Production availability | Existing 99.5% monthly availability requirement remains for production; this Unit does not establish it | Calendar month after production measurement and no-traffic handling are designed |

Dev has no availability SLA, RTO or RPO. Empty windows and missing samples are not evidence of health. Run the documented 100-user / 10-active-user load shape; record achieved concurrency, request counts, p95, fixture run ID and safe raw timings. Do not claim capacity or SLO compliance before deployed results exist.

## Logs & Tracing

Use CloudWatch Logs structured JSON with explicit UTC timestamps and a 14-day dev retention on every log group. Allowed fields are timestamp, environment, component, bounded operation, safe result/error code, duration, `correlationKeyVersion`, `correlationKey`, and a platform-generated request ID when available. Do not log request/response bodies, authorization headers, access/refresh tokens, email, display name, passwords, confirmation codes, raw SDK exception payloads or raw caller correlation IDs. Sanitize allowed text and use fixed safe error codes.

The platform creates a random 256-bit HMAC-SHA-256 key per environment in Secrets Manager. The platform owns creation and rotation; the edge adapter and MoneyApi get separate read-only role permissions. Both use the active version and the same HMAC input encoding, and log the version with the resulting hex `correlationKey`. Keep the immediately previous version available for the 14-day retained-log window. A local authorized investigation tool computes the same HMAC from a correlation ID supplied by the caller; the raw value is never logged. Prove edge/service matches for success, refusal and failure before relying on the workflow.

No distributed tracing backend is introduced. A CloudWatch dashboard shows request volume/status, valid transfer success, business refusals, technical failures and unknown outcomes, public p50/p95, fraction over two seconds with sample count, active/admitted requests, capacity refusals, dependency failures and alarm states. Make environment and UTC window visible. Display “no traffic” or “insufficient samples” rather than zero latency or a green health state.

## Sources

- `construction/u1-walking-skeleton/nfr-design/observability-design.md`: metric ownership, privacy, alarms, dashboard and verification.
- `construction/u1-walking-skeleton/nfr-design/performance-design.md`: public latency target and accepted load shape.
- `construction/u1-walking-skeleton/nfr-design/security-design.md`: log allowlist, response privacy and protected correlation.
- `construction/u1-walking-skeleton/nfr-design/reliability-design.md`: uncertain transfer outcomes and disposable dev recovery.
