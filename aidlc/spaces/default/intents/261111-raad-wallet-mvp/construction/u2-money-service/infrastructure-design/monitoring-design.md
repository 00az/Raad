# monitoring design — u2-money-service

Conversation language: English.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---|---|
| Requests/refusals/errors | MoneyApi safe EMF counters by environment/operation/result | Account for every response | Business refusal does not hide technical failure. |
| Public latency | U4 native CloudFront observations plus complete acceptance join | p95<=2000ms at demo load, cold samples retained | Handler duration is diagnostic only. |
| Integrity/replay | Fixed Ledger codes for missing row/profile/ordinal and conflicts | Technical failures visible | No partial successful history or new replay movement. |
| C2 failures | Workqueue age, both DLQs, consumer errors/rule delivery failures | Any DLQ>=1/min | Delivery acceptance is not processing success. |
| Recovery | Timed drill | RPO<=5min/RTO<=3h | PITR alone does not prove targets. |

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| Server errors | >=1% and>=20 requests in each of two5min windows | High | Shared SNS, jjii0@hotmail.com |
| Technical transfer failures | >=3 in each of two5min windows | High | Same |
| Public latency | p95>2000ms in two complete5min windows,>=20 samples each | Warning | Same |
| Runtime/store throttles | >=1/min in two windows | High | Same |
| Delivery/processing DLQ | >=1 in1min | High | Same; operator reconciliation |
| Missing observation heartbeat | Absent>=3min | High | Same |

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|---|---|---|
| Transfer latency/success | p95<=2000ms, every valid funded transfer succeeds | >=200 funded attempts/>=10min at100 registered/10 active; combined idle-start/sustained and sustained separately |
| Availability | prd>=99.5%; maintenance/dependency failures included | Calendar month; idle wallet probes separately labelled |
| Recovery | RPO<=5min/RTO<=3h | Actual coherent three-table restore drill |

## Logs & Tracing

| Item | Configuration |
|---|---|
| Allowlist | UTC/environment/component/operation/safe code/duration/protected correlation version/key; eventId for event diagnostics only. No profile/body/token/money/key/cursor. |
| Retention |14days dev/30days stg-prd, encrypted, named-role access. |
| Missing/recovery | Incomplete/low-volume=>INSUFFICIENT_DATA, separate heartbeat alarm. Three complete healthy windows recover ordinary alarms; DLQ needs operator reconciliation. |
| Dashboard | Counts/refusals/errors/public p50/p95+coverage/cold diagnostics/throttles/transaction conflicts/events/restore status. No tracing backend. |
| Evidence | Actual stg breach/recovery email to confirmed subscription remains unrun; fake/API/device checks do not substitute. |

## Sources

U2 observability/reliability designs and U4 monitoring; C1/C2/C5.
