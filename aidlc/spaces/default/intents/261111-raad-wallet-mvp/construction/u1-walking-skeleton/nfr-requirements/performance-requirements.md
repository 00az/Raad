# Performance Requirements: U1 Walking Skeleton

Conversation language: English.

## Scope and measurement

U1 proves sign-in, balance, recipient resolution, a simulated transfer and the first history page on dev. These requirements carry forward the existing demo-scale targets. They set no production capacity above 100 users and introduce no new user-facing feature.

API latency runs from public-edge receipt of a complete request to completion of the response. It includes edge verification, MoneyApi verification, dependency work and response serialization. It excludes interactive sign-in, user confirmation time and mobile-network transit. Record app journey timings separately; do not present them as the API measurement.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR6.1 | At least 95% of transfer requests receive a response within 2 seconds at the API at the NFR7 demo load. | Measure the transfer latency distribution with 10 concurrent active test users. Record sample count, percentile and test conditions. |
| NFR6.2 | A fast refusal or server error must not be counted as a successful valid transfer to make the latency result pass. | Report expected business refusals and technical failures separately. Valid, funded transfers must succeed and meet the latency target; report unexpected failures alongside latency. |
| NFR6.3 | C1's 15-second client request timeout is a failure bound, not a replacement for the 2-second target. Every outbound call has a finite timeout within the overall request budget. | Exercise a delayed dependency and show bounded completion. NFR Design allocates concrete dependency timeouts; no outbound call may wait indefinitely. |
| NFR7.1 | The system supports up to 100 registered demo users, with about 10 active simultaneously. | Prepare a representative 100-user test population and exercise 10 simultaneous user sessions against dev. Record the actual operations and concurrency achieved. |
| NFR7.2 | The skeleton reads only the first history page. The C1 page default is 20 entries and its maximum is 100; U1 does not add later-page navigation. | Exercise the first-page response and record its bounded result size. History paging remains U2/U3 work. |
| NFR9.1 | Safe setup/read operations have no more than the one client retry permitted by C1. Transfers are not retried automatically. | Inject a timeout or transient server failure and count client attempts. Respect Retry-After where C1 requires it. Full transfer replay remains U2/U3 work. |

## Verification conditions

Use the real dev sign-in, API and selected data store for the deployed load check. Keep balances sufficiently funded and separate performance fixtures from the API and simulator smoke journeys. Record cold-start observations and the measurement window; do not silently discard slow samples. NFR Design defines the final load procedure and any separate warm-up run before implementation.

There is no additional numerical latency target for sign-in, wallet reads, recipient lookup or history in the approved inception requirements. Measure them for diagnosis and apply the bounded timeout/error behavior; do not invent an additional acceptance SLO.

## Dependencies and accepted risks

The functional specification and rules describe the U1 workflows and money invariants. Their accepted review concerns about setup, public field mapping and fixture initialization remain open risks. This document does not edit those artifacts or claim that the concerns have been fixed. The measured implementation must identify which C1 operations and payloads the test actually used.

## Sources

- construction/u1-walking-skeleton/functional-design/functional-spec.md: U1 workflows and end-to-end check.
- construction/u1-walking-skeleton/functional-design/rules.md: transfer atomicity and balance checks.
- inception/requirements-analysis/requirements.md: NFR6, NFR7 and NFR9.
- inception/contract-design/contract-summary.md: C1 timeout, retry rules and page-size limits.
- inception/units-generation/unit-of-work.md: U1 boundary and later-unit exclusions.
