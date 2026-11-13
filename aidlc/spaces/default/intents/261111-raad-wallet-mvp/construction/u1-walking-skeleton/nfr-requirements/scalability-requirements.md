# Scalability Requirements: U1 Walking Skeleton

Conversation language: English.

## Capacity boundary

The approved MVP has up to 100 users and about 10 active concurrently. U1 proves the thin integrated path at that scale. No growth target above it, new service, cache, queue or additional deployment region is introduced here.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR7.3 | Support 100 registered test users and 10 concurrent active users while meeting the transfer latency requirement NFR6.1. No valid funded request may fail merely because the demonstrated load is reached. | Deployed load check records user population, achieved concurrency, latency and technical-error counts. |
| NFR3.1 | Concurrent requests must not create a second wallet or issue the opening balance twice for one owner. | Concurrent first-setup tests result in one wallet and one 100,000-halala credit. |
| NFR3.2 | The balance check and debit/credit/transfer-record write remain one all-or-nothing operation under concurrent access. | The money invariant tests prove total conservation and non-negative balances across overlapping transfer attempts. The dedicated complete replay/concurrency suite remains U2 work. |
| NFR7.4 | First-page history reads are bounded by C1's page-size limits, and profile lookup is bounded to the counterparties needed for that page. | Inspect the selected data-access design and test that one first-page request does not fetch the entire transfer history or holder directory. |
| NFR13.1 | The shared API retains the existing /money mapping boundary. A later service's mapping must not require a change to the money API contract. | Review the infrastructure interface. The separate stub-service extensibility demonstration belongs to later platform completion; U1 does not build that service. |

## Capacity planning handoff

Infrastructure Design chooses the data store and compute settings from these requirements. Its capacity evidence must explain how the selected settings handle the 10-user demo load, bound concurrency and avoid breaking the transaction invariants. NFR Design defines overload and timeout behavior using the existing C1/C5 errors.

There is no approved requests-per-second forecast, fixed percentage CPU target, unlimited growth claim or mandatory multi-region topology. Those are not substituted for the explicit concurrent-user acceptance target.

## Sources

- construction/u1-walking-skeleton/functional-design/functional-spec.md: wallet setup, atomic transfer and first history page.
- construction/u1-walking-skeleton/functional-design/rules.md: BR2.1, BR3.1 to BR3.3 and BR5.1.
- inception/requirements-analysis/requirements.md: NFR3, NFR6, NFR7 and NFR13.
- inception/contract-design/contract-summary.md: C1 bounded history and C5 path mapping.
- inception/units-generation/unit-of-work.md: U1 scale and deferred platform/service completion.
