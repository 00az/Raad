# Performance Requirements — U2 Money Service

Conversation language: English.

## Targets

| ID | Requirement | Measurement / acceptance |
|---|---|---|
| NFR6.1 | At least 95% of C1 transfer requests complete within 2 seconds at demo load. | Measure end-to-end at the public API boundary in `stg`, including authorization, recipient lookup, atomic persistence, and response serialization; test with 10 concurrent users. |
| NFR6.2 | At demo load, C1 wallet, recipient lookup, transfer, and history requests return without service errors. | Run the defined load check with 10 simultaneous users; expected business refusals are not service errors. |
| NFR6.3 | A valid history request returns at most the requested page size, default 20 and maximum 100, and must not scan an unbounded history. | Verify page size and query behavior against a seeded 1,000-entry history. |
| NFR6.4 | Each outbound dependency call has a finite timeout; individual calls must stop waiting within 1 second so the 2-second API budget retains time for safe error handling. | Inject a slow dependency and verify a structured timeout response without a stack trace or partial transfer. |

## Scope and Assumptions

Capacity is the approved MVP target: 100 users total and approximately 10 concurrent users. There is no requirement for a higher request rate or growth target. A timeout or latency failure must not compromise all-or-nothing transfer behavior. The shared platform owns public edge routing; the service measures its own work and exposes timing data without personal information.

## Sources

- `functional-spec.md` and `rules.md` in this Unit's Functional Design define the wallet, transfer, replay, and history behaviors constrained by these targets.
- `requirements.md` defines NFR5–NFR7, NFR9, and the environment and capacity assumptions.
- `contract-summary.md` defines C1, C2, and C5 wire-level behavior and the approved transfer and cursor constraints.
