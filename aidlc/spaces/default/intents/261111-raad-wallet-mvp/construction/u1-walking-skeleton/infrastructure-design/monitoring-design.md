# Monitoring Design — U1 Walking Skeleton

Conversation language: English.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| Public API request count and status | API Gateway and edge adapter | Report counts by environment, component, bounded operation and result; never by caller | Shows traffic and failures at the public boundary. |
| Public transfer duration | CloudFront real-time access log time-taken, converted from seconds to milliseconds; deduplicated by native x-edge-request-id | p95 at or below 2,000 ms for both combined idle-start/sustained and sustained acceptance populations, after complete request-level reconciliation | Includes outer CloudFront/API Gateway processing, origin waiting, adapter/service initialization and response handling. A Lambda handler timer is only a component diagnostic. |
| Valid funded transfer success | MoneyApi and edge outcome counters | Every valid funded transfer in the performance run succeeds | Keeps business refusals and technical failures distinct from valid success. |
| Technical transfer failures and unknown outcomes | MoneyApi result counters and edge upstream timeout/unreachable counters | Any failure or unknown outcome is visible; a transfer timeout is never reported as a confirmed abort | Flags uncertain money outcomes without suggesting a retry. |
| Edge 5xx count | API Gateway/edge adapter | Three or more in each of two consecutive one-minute windows | Detects public-path failures with minimum sample gating. |
| Slow transfer fraction | Deduplicated CloudFront public-duration samples, grouped by edge completion timestamp | More than 5% over 2,000 ms in each of two consecutive five-minute event windows, with at least 20 unique observed responses per window | Detects sustained public-path degradation; labels best-effort telemetry coverage and missing/ineligible windows explicitly. |
| Admitted requests and capacity refusals | Edge adapter and MoneyApi | Investigate at 80% of the configured concurrency limit for three consecutive one-minute periods; any refusal at the approved load is investigated | Checks the candidate 20-request envelope and exposes admission pressure. |
| Dependency failures and duration | MoneyApi dependency instrumentation | Diagnostic only; operation deadlines remain those in performance-design.md | Finds store, profile and key-discovery bottlenecks without hiding public latency. |
| Correlation-key match rate | Edge and MoneyApi structured logs | Expected same key version and value for paired requests | Confirms logs can be joined without storing the caller-provided correlation ID. |

Metric dimensions are limited to `Environment`, `Component`, `Operation` and bounded `Result`/`ErrorCode`. Do not emit email, name, token, wallet ID, transfer ID, caller correlation ID, native CloudFront request ID, arbitrary URL or raw exception as a dimension. Public p95 comes from the deduplicated CloudFront samples, never a sum of component percentiles. Operational alarms describe observed best-effort samples; only the acceptance report's reconciled population can substantiate the target for its test run.

Measure the complete five-action cross-table transfer commit as the Ledger dependency duration. A detected missing canonical Transactions row, missing lookup reference or ownership mismatch is a technical integrity failure, not an empty or partial successful history. Route it through the existing technical-failure signal with a bounded safe result code. Investigation uses authorized reads by transferId to compare the canonical row, both reference entries and both history views; it never resubmits an uncertain transfer or copies transaction payloads into telemetry.

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| Server errors | At least 3 edge 5xx responses in each of 2 consecutive 1-minute periods, with at least 3 requests in each breaching period; recover after 2 consecutive non-breaching periods | Warning | Environment SNS topic subscribed to the team monitored email |
| Slow transfers | More than 5% of transfer responses exceed 2,000 ms in each of 2 consecutive 5-minute periods, with at least 20 responses per period; recover after 2 eligible non-breaching periods | Warning | Environment SNS topic subscribed to the team monitored email |
| Technical transfer failure | At least 1 technical transfer failure or unknown outcome in a 1-minute period; includes edge upstream timeout/unreachable. Recover after 2 consecutive non-breaching periods. | High | Environment SNS topic subscribed to the team monitored email |

Use CloudWatch alarms with explicit evaluation periods. The public-latency aggregation below supplies unique event-window counts/fractions and checks consecutive source windows; repeated scheduled invocations must not double-count samples or satisfy the minimum sample count. Configure missing data as `missing`, never as success; low-volume, failed-query or stale telemetry windows remain insufficient data. Send notifications on alarm entry and recovery, not on every evaluation. Email alarm payloads contain environment, alarm category, UTC window, aggregate value and an authenticated dashboard link only. Do not include correlation IDs, user identifiers or financial amounts. Provision the email address as an environment parameter, confirm its SNS subscription, and inject a controlled synthetic signal for each alarm before claiming delivery works.

## Public-boundary Measurement

| Facet | Selected design |
|---|---|
| Clock and duration | Use CloudFront real-time log `timestamp` as the UTC response-completion time and `time-taken * 1000` as duration in milliseconds. AWS defines this interval from receipt of the viewer request until the last response byte is placed in the output queue. It includes the complete origin path and initialization, excludes later viewer-network delivery/TCP buffering, and can conservatively include request ingress before a complete JSON body. Do not subtract guessed ingress time or substitute first-byte/origin-only timing. |
| Collection | Attach a 100%-sampling real-time log configuration to the configured `/money/v1/transfers` cache behavior, with caching disabled and forwarding unchanged. CloudFront delivers to one encrypted environment-specific Kinesis stream. A platform-owned telemetry Lambda ingests the selected fields into a dedicated CloudWatch log group with 14-day retention. This stream carries telemetry only, not transfers or confirmation events. |
| Field/privacy allowlist | Select only `timestamp`, `time-taken`, `sc-status`, `cs-method`, `cache-behavior-path-pattern`, `x-edge-request-id` and `x-edge-result-type`. Do not select IP, raw URI/query, headers, cookies, user agent, body, profile or caller correlation fields. Validate values and normalize method/status/result into fixed categories before writing safe JSON logs; derive environment from trusted resource configuration. Treat the native CloudFront ID as diagnostic data only. |
| Deduplication and aggregation | Invoke the same telemetry Lambda in aggregation mode through an environment-scoped EventBridge Scheduler schedule at two minutes past each five-minute boundary. Query the safe log group for the last two completed five-minute event windows, grouped by edge completion time. Deduplicate native CloudFront IDs, reject conflicting/malformed samples, and compute each window's unique count, fraction above 2,000 ms and p95 from the individual values. Abort rather than truncate a query that exceeds its configured record limit or deadline. Never sum or average component/window p95 values to produce a combined p95. |
| Alarm input | Publish one aggregate snapshot per eligible source window and a pair evaluation for the last two consecutive source windows. Repeated publication uses the same source-window identity/timestamp and gauge statistics (Maximum, not summed sample counts). A pair breaches only when both windows have at least 20 unique observations and both slow fractions exceed 5%; recovery requires two consecutive eligible non-breaching windows. A mixed/ineligible pair or collector/query failure publishes no healthy result and is displayed as insufficient data. No response status, cold start or slow observed sample is filtered out to improve the alarm. |
| Delivery limits | The two-minute collection grace is an operating setting, not an AWS delivery guarantee. Track stream/consumer lag, query failures, late samples and observation counts on the dashboard. Logs are best effort even at 100% sampling; live coverage outside controlled tests is labelled unknown. Late arrivals remain available for diagnosis and recomputation and are never silently described as healthy traffic. No complete-accounting or exact alert-delivery-time claim is made from this stream. |
| Acceptance population | The load harness retains one safe attempt record per send: run ID, phase (idle-start/sustained), UTC times, outcome, client elapsed time and native `x-amz-cf-id` response header. Keep credentials, bodies and caller correlation IDs out. Join every response one-to-one to the deduplicated CloudFront record; unexpected, duplicate-conflicting, missing or unclassifiable records prevent a passing report. Any no-response attempt is a technical failure, never a fast success. Wait at most two minutes after the run for log reconciliation; otherwise report incomplete telemetry and block acceptance, without resending an uncertain transfer. |
| Acceptance statistic | Compute nearest-rank p95 directly from matched public-duration values separately for the complete combined idle-start/sustained population and the sustained population. Both must be at most 2,000 ms, with every valid funded transfer successful. Report all refusals/failures, observation coverage and client-network timings separately. A missing public sample cannot be replaced by the shorter Lambda duration or dropped from the denominator. |
| Instrumentation proof | In a controlled dev fixture, publish a fresh adapter Lambda version with an injected pre-handler initialization delay above 2 seconds and invoke it through the real CloudFront URL. Its CloudFront duration must include the delay while the handler diagnostic does not. Also inject an origin/upstream delay before handler entry and verify it is included. Reconcile every probe, show separate phase p95, then drive two eligible slow windows and two eligible recovery windows through the same collector/aggregation/alarm path. Disable delivery or omit a sample to prove acceptance blocks and the dashboard cannot show a healthy complete population. Remove the fault injection before normal verification. |

The adapter's duration and Lambda initialization/runtime metrics remain diagnostics for attribution. They never provide the public SLI or replace the reconciled CloudFront duration. Standard access logs are not selected for this alarm path because their delivery can be substantially delayed.

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

For public p50/p95 panels use the deduplicated telemetry records over the selected event window, with observed sample count, source-window timestamps and collection lag beside them. Keep adapter/component timing in separately labelled panels. Never present an observed subset as a complete public workload.

## Sources

- `construction/u1-walking-skeleton/nfr-design/observability-design.md`: metric ownership, privacy, alarms, dashboard and verification.
- `construction/u1-walking-skeleton/nfr-design/performance-design.md`: public latency target and accepted load shape.
- `construction/u1-walking-skeleton/nfr-design/security-design.md`: log allowlist, response privacy and protected correlation.
- `construction/u1-walking-skeleton/nfr-design/reliability-design.md`: uncertain transfer outcomes and disposable dev recovery.
- [CloudFront real-time logs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/real-time-logs.html): boundary duration, completion timestamp, selectable fields, sampling, Kinesis delivery and best-effort limitations.
- [CloudFront standard logging reference](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/standard-logs-reference.html): standard-log delivery delays.
