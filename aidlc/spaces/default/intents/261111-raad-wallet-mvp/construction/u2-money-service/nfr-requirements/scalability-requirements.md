# Scalability Requirements — U2 Money Service

Conversation language: English.

## Capacity and Growth

| ID | Requirement | Acceptance |
|---|---|---|
| NFR7.1 | Support up to 100 registered MVP users, with approximately 10 active at once. | Load check at 10 simultaneous users completes with no service errors and satisfies NFR6.1. |
| NFR7.2 | The API compute layer is stateless between requests and may add capacity horizontally without splitting wallet ownership or relaxing transaction conditions. | Concurrent load test confirms each request is served without session affinity and all ledger invariants hold. |
| NFR7.3 | History retrieval remains page-bounded for at least 1,000 entries per test user. | A first page and subsequent cursor pages remain bounded, stable, and free of skipped or duplicate entries. |

## Concurrency Safety

| ID | Requirement | Acceptance |
|---|---|---|
| NFR7.4 | Simultaneous transfers from the same wallet serialize through conditional/atomic persistence; capacity changes must not enable overdrafts or duplicate keyed outcomes. | Run concurrent transfer tests against a real local data-store container; total funds remain constant and sender balances never fall below zero. |
| NFR13.1 | Adding a new approved RAAD service must require no change to MoneyService's API or its OpenAPI contract. | Attach a stub through a new shared-platform path mapping in `dev`; the stub answers without a MoneyService code or contract change. |

Traffic above the defined MVP load is not an acceptance target. Scaling triggers, partition design, and service quotas are set in Infrastructure Design and monitored before any increase beyond the approved demo scale.
