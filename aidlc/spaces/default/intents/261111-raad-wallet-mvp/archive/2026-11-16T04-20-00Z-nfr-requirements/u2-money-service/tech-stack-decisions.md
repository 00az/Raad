# Technology Stack Decisions — U2 Money Service

Conversation language: English.

## Decisions

| Area | Decision | Rationale / constraint |
|---|---|---|
| Language and runtime | Python 3.12 for the service runtime. | Matches the current service package constraints; use strict type checking and Ruff. |
| API and compute | AWS Lambda handlers behind the shared `/money` API edge. | Stateless request handling supports independent deployment and horizontal scaling; the platform remains responsible for public routing and firewall policy. |
| Persistent data | Amazon DynamoDB for wallets, transfer requests, transfers, holder directory, and event receipts. | Conditional writes and transactional operations support one-time wallet setup, replay protection, and atomic sender/recipient balance changes. Infrastructure Design must verify transaction and partition choices. |
| Infrastructure as code | AWS CDK v2 in Python. | Service-owned stacks keep MoneyService deployable independently in each environment. |
| Package and test tooling | `uv`; pytest, Hypothesis, pytest-cov, Ruff, mypy, and dependency audit in CI. | Supports deterministic locking, property/concurrency tests, the 80% backend coverage floor, and the 95% line/branch floor for money movement. |
| API contract | OpenAPI 3.1 C1 contract, owned and versioned by U2. | Keeps mobile and other clients pinned to a stable public boundary. |
| Event contract | AsyncAPI 3.0 C2 consumer contract; accept compatible 1.x payloads and ignore unknown optional fields. | Provides tolerant evolution for the shared account-confirmed event. |
| Identity | Verify C5 JWT claims locally using environment-specific, non-secret verifier configuration; never accept caller-supplied owner IDs. | Preserves defense in depth while the shared platform edge authenticates requests. |
| NFR14.1 | The MoneyService repository maintains at least 80% line coverage. | CI reports the full service suite's coverage independently. |
| NFR14.2 | The Ledger money-movement core maintains at least 95% line and branch coverage. | CI reports both floors for the isolated core; neither floor is lowered to make the step pass. |
| NFR14.3 | Lint, strict type checks, dependency audit, infrastructure checks, and the full suite pass before merge. | A local green run and matching GitHub Actions run are required; failures block merge. |

## Alternatives and Boundaries

The current U2 repository uses Python and CDK, and the approved service design requires atomic multi-record money movement. DynamoDB is retained as the service data store because its conditional and transactional write model fits those invariants. Do not add a cache, queue, second database, or real-payment provider for this MVP without a new approved design. Specific AWS resource sizing, retry timings, keys, backups, and deployment configuration remain for Infrastructure Design.
