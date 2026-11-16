# monitoring design — u3-mobile-app

Conversation language: English.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| Requests / attempts | Test instrumentation with no private payload | One in-flight operation/control; no automatic transfer retry | Prevents accidental duplicate financial intent. |
| History rendering | 1000-entry widget/integration scenario | Pages <=100, no skipped/duplicate entries; bounded retained state | Avoids full-history fetch. |
| App test coverage | Flutter coverage report | >=80% measured lines | Separate from manual/device evidence. |

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| Build/test/config failure | Any required check fails | Release blocker | Repository CI; no new notification subscription |
| API/provider outage | Safe localized loading/error/uncertain/stale state | User-visible status | U4 owns operational alarms |

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|---|---|---|
| API latency | U1/U2/U4 own public 2000-ms p 95 | App elapsed timing reported separately |
| App uptime | No independent uptime SLA invented | Device checks |
| Accessibility / locale | Complete ar/en behavior and affirmed checklist | Each release on both platforms |

## Logs & Tracing

| Item | Configuration |
|---|---|
| Diagnostics | No password, code, token, email/name, bodies, amount, key or cursor; no analytics/crash backend added. |
| Evidence | Exact app/backend revision, contract pin, environment and device; iOS/Android and fake/live labelled separately. |
| Screens | Loading, empty, refused, error, uncertain and timestamped stale states; no fabricated zero balance. |
| Acceptance | Actual accessibility and live provider/API checks remain unrun until evidence exists. |

## Sources

U3 observability/security/performance/reliability design and team testing posture.
