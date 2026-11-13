# Observability Requirements: U1 Walking Skeleton

Conversation language: English.

## Scope

The existing basic monitoring requirement is built with the application and infrastructure; there is no new observability stage. U1 supplies the dev signals and monitoring needed for its integrated path. Later units extend them to the remaining operations and environments.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR8.1 | Dev has a dashboard showing request volume, server errors, transfer latency and technical transfer failures for the skeleton path. | A smoke/load run produces visible, environment-specific signals. The dashboard distinguishes technical failures from expected business refusals. |
| NFR8.2 | The monitoring design provides alarms for server errors, slow responses and failed transfers, with notification to the designated email address. Slow-transfer monitoring uses the existing 2-second/95% target. | NFR Design defines the precise windows, minimum sample counts and trigger/reset thresholds; Infrastructure Design wires the supplied recipient. Alarm injection must prove delivery before deployed monitoring is claimed complete. |
| NFR8.3 | Every skeleton request can be followed through its edge/service logs by the C5 correlation ID. The response header and an error body's correlationId agree. | Exercise successful requests, service errors and edge-generated refusals; locate the matching permitted log records. |
| NFR10.2 | Operational data contains no password, code, token, email or display name. Metrics and alarm dimensions use bounded operation/environment/result categories rather than personal values. | Scan representative logs, metrics and alarm messages using the test profile's recognizable values. |
| NFR15.1 | Transfer and operational timestamps are UTC instants. Mobile display uses the device time zone without changing the underlying instant or transfer order. | Compare one stored transfer and its API response on devices set to two different time zones, and inspect the corresponding UTC log timestamps. |

## Service indicators

Measure transfer latency at the public API boundary defined in performance-requirements.md. Report valid-transfer technical success, business refusal and technical failure counts separately. Do not hide slow responses or outages behind a low request count.

The production availability indicator is retained for the later production target: successful service of valid wallet/API requests divided by eligible requests over each calendar month. Planned maintenance is not silently excluded. The operational design must identify how no-traffic periods are measured before production availability is claimed; no new public endpoint or synthetic-monitor service is selected in U1.

Correlation IDs are sufficient for the approved basic investigation path. Distributed request tracing, a tracing backend and transfer-completed event publication remain outside this scope.

## Outstanding implementation inputs

- NFR Design: concrete alarm windows, sample requirements and recovery thresholds.
- Infrastructure Design: monitoring destination email, resource wiring and retention settings for the selected logging system.
- Later deployment checks: stg alarm-delivery evidence required by inception NFR8.

These are explicit handoffs; this requirements document does not claim that any alarm has already fired or that an email destination has been supplied.

## Sources

- construction/u1-walking-skeleton/functional-design/functional-spec.md: U1 operations and verification journeys.
- construction/u1-walking-skeleton/functional-design/rules.md: transfer outcomes and own-history boundary.
- inception/requirements-analysis/requirements.md: NFR5, NFR6, NFR8, NFR10 and NFR15; no distributed tracing.
- inception/contract-design/contract-summary.md: C1 errors, C5 correlation-ID handling and personal-data restrictions.
- inception/units-generation/unit-of-work.md: U1 versus later-unit monitoring/environment scope.
