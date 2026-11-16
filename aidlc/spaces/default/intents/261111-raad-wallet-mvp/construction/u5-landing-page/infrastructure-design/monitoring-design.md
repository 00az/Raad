# monitoring design — u5-landing-page

Conversation language: English.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| ar/en deployed smoke | Pipeline HTTPS fetch of actual documents/assets | Both succeed with expected language/contact/navigation | Deployment is incomplete if either fails. |
| Static accessibility | Automated scan plus manual browser evidence | Affirmed 320dp/200%/keyboard/screen-reader checklist | No executable code coverage percentage applies. |
| Isolation | Source/network/storage inventory | Zero auth/money calls, collection or tracking | Public page stays separate from financial state. |

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| Smoke failure | Either page/asset unavailable or invalid | Release blocker | CI result; U4 owns operational service alarms |
| TLS/DNS failure | Invalid host/certificate/protocol policy | Publication blocker | CI/release record |

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|---|---|---|
| Page availability/latency | No separate numerical SLA invented | Both language smoke after every deploy |
| Rollback | Previous artifact restores both pages | Release rollback exercise |

## Logs & Tracing

| Item | Configuration |
|---|---|
| Evidence | Revision/environment/actual URL/status and safe asset checks only. |
| Privacy | No visitor events or raw query/referrer/request-body logging; no tracing backend. |
| Manual checks | Native Arabic copy, browser/no-JS/no-mail-handler and assistive-technology results explicitly labelled unrun until executed. |

## Sources

U5 observability/security/reliability/performance designs and team static smoke requirement.
