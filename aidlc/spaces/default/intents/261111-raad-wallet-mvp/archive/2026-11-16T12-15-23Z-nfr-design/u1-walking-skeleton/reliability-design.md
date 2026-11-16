# Reliability Design: U1 Walking Skeleton

Conversation language: English.

## R1 — Atomicity and uncertain outcomes

Ledger changes the guarded source balance, destination balance and exactly one immutable row in the dedicated Transactions table together. The row is keyed by transferId (internal transfer_id), with sender/recipient wallet IDs as references. A known aborted transaction changes none of them. A timeout, connection loss or missing response is not proof of an abort: it may occur after commit. Do not return a definitive “no money moved” message unless the adapter has an authoritative pre-commit failure/abort result. On uncertainty, preserve the attempted details/key for reconciliation, block resubmission and tell the user the result could not be confirmed; a read-only balance/history refresh may help investigate but is not a replay guarantee.

U1 has one outbound transfer attempt per confirmation and disables repeated confirmation while in flight. It validates the Idempotency-Key syntax but creates no TransferRequest or saved key-to-outcome record. Do not queue or resend an uncertain transfer, automatically or manually, including through SDK retry policies. An inconclusive refresh keeps the result uncertain; it must not unlock another submission. U2 introduces saved outcomes and writes a successful outcome atomically with the same Transactions row and both balances. U2/U3 complete same-key retry. Their transition starts fresh transfer intents/keys and never manufactures replay outcomes for historical U1 transfers without saved keys and fingerprints.

## R2 — Setup and read recovery

Persistent owner uniqueness and one atomic opening allocation make wallet creation repeatable. Directory registration follows Ledger opening/reading, uses verified profile values and persistent subject/email uniqueness. Readiness requires both the wallet and holder entry. If registration fails after wallet commit, keep the wallet and return a safe error; the next PUT registers or reads the holder against that same wallet and never credits it again. A normalized-email ownership conflict returns C1's 409 without replacing another holder's entry. C1 exposes setup through PUT /wallet and returns WALLET_NOT_FOUND on a missing-wallet read; GET has no creation side effects. Test both the pre-commit failure and retained-wallet/incomplete-directory case.

Safe setup/read retries use performance-design.md P3: at most one automatic retry, bounded delay, Retry-After honored, no business-error retry. Do not layer a second general retry library behind the generated client. Signing-key refresh is a separate C5 verification action with its own bound, not a replay of the business request.

## R3 — Failure isolation and fallback

| Failure | Behavior | Blast radius/recovery |
|---|---|---|
| Sign-in provider unavailable | Sign-in fails safely; no credential reaches MoneyApi. An already-valid access token may still authorize using a usable key cache. | Sign-in or profile-dependent setup; restore provider/configuration. No fabricated profile. |
| Key discovery unavailable | Use an unexpired applicable key set; otherwise 503 TOKEN_VERIFIER_UNAVAILABLE. | Verification layer/cache instance; retry discovery within C5 bounds. |
| Ledger unavailable or corrupt result | Fail closed with C1 safe server/unavailable error. No substitute balance or queued transfer. | Money operations; repair dependency/configuration. Never zero or recreate balances automatically. |
| Directory unavailable | Recipient/setup requests fail safely. History returns a safe error for the page instead of fabricating identities or dropping entries. A committed wallet survives failed registration. | Directory-dependent operations; retry safe reads or PUT setup repair without another opening credit. |
| Edge cannot reach service / times out | 503 SERVICE_UNAVAILABLE, Retry-After, same correlation ID; transfer may be uncertain. | Public money path; investigate using logs and committed data. |
| Telemetry/notification unavailable | Keep the money outcome independent of telemetry. Use bounded best-effort emission; built-in edge/runtime signals expose service errors. | Investigation/alert delivery; report telemetry loss rather than claiming a healthy dashboard. |

Finite deadlines, bounded client retries and admission limits are the U1 resilience mechanisms. Do not add stateful circuit breakers, cross-region failover, a background job queue, duplicate stores or compensating transfers. A circuit breaker and a stale financial fallback would add complexity without a requirement at this scale. The selected SDK's connection reuse is bounded; failed connections are discarded and safely re-established on a later request.

## R4 — Disposable dev recovery and rollback

Dev has no availability SLA, RTO or RPO. An engineer may explicitly choose to rebuild from versioned infrastructure and recreate test users/wallets after loss. This is not permission to reset an environment now. Recovery instructions in Infrastructure Design must identify the target environment, known data loss, selected secrets source and ordered redeployment: shared sign-in/edge first, money service/store next, mobile environment configuration next. Verify C3/C5 configuration before test-user preparation. A reset must never be an automatic reaction to a failed API call.

Initialize both sender and recipient through PUT /wallet and verify directory readiness before each journey. Use independent fresh fixture pairs for API, iOS and Android journeys and an isolated performance population. Fresh-wallet checks assert 100,000 halalas once. Repeat runs must not rely on untouched shared opening balances or insert directly into stores. Verify the same completed transferId in both parties' history and in the one immutable Transactions row.

Rollback redeploys the affected repo's last known-good commit under the affirmed process, then reruns its dev smoke check. Redeploying application code does not restore lost data. After rebuild/rollback run scripts/verify-dev.sh against actual dev sign-in, API and data store with the agreed iOS simulator and Android emulator. Capture commit IDs and actual results. No deployed result is claimed here.

## R5 — Production boundary and verification

Production's existing 99.5% monthly availability, retention and point-in-time recovery requirements remain in force for later delivery. U1 does not deploy production or claim them proven. No-traffic availability measurement is a later production design input, not a new U1 synthetic endpoint.

Tests cover concurrent first setup, opening-credit uniqueness, conservation/non-negative balances, pre-commit failure, lost post-commit response, dependency timeout, no automatic transfer retry and safe recovery. Money-core logic is test-first and meets 95% line/branch coverage; each backend/mobile repo meets 80% line coverage. Real local-store tests are required at the transaction boundary; mocked success is not concurrency evidence. Full replay/concurrency completion remains U2 work without waiving U1's atomicity tests.

## Sources

- construction/u1-walking-skeleton/nfr-requirements/reliability-requirements.md: NFR3.3–3.4, NFR4.1, NFR5.1–5.2, NFR9.2–9.3 and NFR14.2.
- construction/u1-walking-skeleton/nfr-requirements/performance-requirements.md: finite deadlines and one safe retry.
- construction/u1-walking-skeleton/nfr-requirements/security-requirements.md: fail-closed verification, profile privacy and secret handling.
- construction/u1-walking-skeleton/nfr-requirements/tech-stack-decisions.md: NFR14.3–14.4 and deferred store/compute choices.
- construction/u1-walking-skeleton/functional-design/functional-spec.md and rules.md: wallet/transfer invariants, setup repair, U1 replay boundary and independent fixtures.
- inception/contract-design/contract-summary.md: C1 uncertainty/retry/setup boundary and C5 dependency errors.
- aidlc/spaces/default/memory/team.md: rollback, dev-first deployment and mixed testing cadence.
