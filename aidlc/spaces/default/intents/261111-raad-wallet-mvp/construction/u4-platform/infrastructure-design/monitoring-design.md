# monitoring design — u4-platform

Conversation language: English.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| Public requests/errors/latency | API Gateway/edge counts and CloudFront time-taken | Public p95<=2000ms; complete acceptance join | Includes cold initialization; handler duration is diagnostic only. |
| Profile errors/throttles | Safe GetUser counts by environment/operation | Any throttling at demo load fails acceptance | Detects shared provider quota pressure without personal data. |
| Rate decisions | Aggregated edge safe codes | Inspect429/503 and unaffected-caller behavior | No subject/hash metric dimension. |
| Events | Publisher/rule failures, workqueue age and both U2 DLQs | Any DLQ>=1/min; oldest age>1h warning, approaching24h critical | Publication is not processing success. |
| Observation health | Iterator age, query failure, heartbeat and reconciliation | Missing heartbeat3min; missing/conflicting records fail load acceptance after2min grace | Best-effort stream is not guaranteed complete. |

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| Server errors | >=1% with>=20 eligible requests in each of two consecutive5min windows | High | Environment SNS, jjii0@hotmail.com |
| Transfer technical failures | >=3 in each of two consecutive5min windows | High | Same |
| Public latency | p95>2000ms in two complete5min windows,>=20 samples each | Warning | Same |
| Runtime/store/provider throttles | >=1/min in two consecutive windows | High | Same |
| Collector missing | Heartbeat absent>=3min | High | Same |
| C2 delivery/processing DLQ | >=1 message in1min | High | Same; operator reconciliation |
| Cost | No provisioning permitted under current instruction | Design gate | No budget resource created |

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|---|---|---|
| Transfer latency | p95<=2000ms; every valid funded transfer succeeds | >=200 funded attempts/>=10min at100 registered/10 active; combined idle-start/sustained and sustained separately |
| Availability | prd>=99.5%, maintenance and dependency failures included | Calendar month |
| Idle coverage | One-minute authenticated nonfinancial wallet-read probes, reported separately from traffic SLI | Missing coverage unknown; no healthy empty month |
| Recovery | U2 RPO<=5min/RTO<=3h | Timed three-table restore drill |

## Logs & Tracing

| Item | Configuration |
|---|---|
| Collection | Encrypted Kinesis stream, one shard/24h. Exactly timestamp, time-taken, status, method, cache-behavior pattern, native edge ID and result type at100% sampling. No IP/raw URI/query/headers/cookies/body/profile. |
| Aggregation | Processor concurrency2; five-minute schedule/two-minute grace; deduplicate IDs, reject conflicting samples, bounded query/deadline. Idempotent source-window gauges; repeated schedule cannot add samples. |
| Acceptance | Harness retains run/phase/time/safe outcome/native response ID. One-to-one complete join; no-response is failure. Unknown operational coverage stays labelled unknown. |
| Correlation | Existing versioned shared HMAC-SHA256 profile; canonical UTF8 correlation input, hex digest/version. Retain every key version required over log lifetime, not only one previous if rotation is frequent. Raw correlation ID never logged. |
| Retention | 14days dev/30days stg-prd. Service encryption or justified existing KMS; scoped roles. No extra CMK only for cosmetic uniformity. |
| WAF privacy | Sampling disabled, no raw request/body/query/authorization logs. Safe counters and configuration audit only; no personal dimensions. |
| Recovery | Three complete healthy windows recover ordinary alarms. Missing/low-volume/incomplete=>INSUFFICIENT_DATA; separate heartbeat alarm. DLQ needs operator reconciliation. Actual stg breach/OK notifications required. |
| Dashboard | Requests/refusals/errors/public latency+sample count/lag/provider quota/throttles/concurrency/events/DLQ/recovery status; no distributed tracing backend. |

## Sources

U4 observability design; U1 native public measurement; U2 event/recovery design; C1/C2/C5. No live alarm, external message or resource creation performed.
