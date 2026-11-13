# Reliability Requirements: U1 Walking Skeleton

Conversation language: English.

## Environment and recovery policy

U1 is the walking skeleton on dev. The person selected Q1 option A: dev data is disposable, the environment and test wallets may be recreated after loss, and no recovery time is guaranteed. This is a recovery requirement, not authorization to delete or reset an environment now. Any rebuild/reset is an explicit engineer action.

The existing production requirement remains 99.5% availability per calendar month, with retained production stores and point-in-time recovery. U1 does not deploy production or claim that this production target has been demonstrated.

## Requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR5.1 | No dev availability SLA, maximum recovery time or maximum tolerated data loss is promised for U1. Recovery may rebuild the environment from infrastructure code and recreate confirmed test users and wallets. | Infrastructure/runbook review identifies the recovery steps and the data that can be lost. Demonstration results report actual recovery observations without inventing an SLA. |
| NFR5.2 | Automated request error handling never resets balances, recreates existing wallets, erases history or destroys an environment to recover from a failure. | Failure-path review and fault tests show safe errors; a reset requires an engineer's explicit action. |
| NFR3.3 | A transfer commits both balances and its completed record together or changes none. The total money is conserved, except for the one opening allocation when a wallet is first created. | Property-based tests and injected pre-commit failures check conservation, non-negative balances and no partial transfer. |
| NFR3.4 | Wallet setup is safe to retry and cannot credit an existing wallet a second time. | Repeated and simultaneous setup calls preserve a single opening credit. Partial setup and holder-registration behavior must be evaluated against C1 and the accepted functional-design risks. |
| NFR4.1 | While a send is in flight, the client disables duplicate confirmation and retains the request identity. It never automatically repeats the transfer after an uncertain response. | Client tests show one outbound attempt per confirmation and no automatic resend on timeout. Durable request-key replay and the complete lost-answer retry flow remain U2/U3 work. |
| NFR9.2 | Every outbound call is bounded by a timeout; recoverable dependency failures produce the existing structured server/unavailable error. A lost response must not be described as proof that no transfer committed. | Inject dependency failure and response loss separately. Only a known pre-commit failure may be asserted to have left balances unchanged. |
| NFR9.3 | Safe client retries follow C1: at most one retry for its allowed setup/read operations after timeout/500/503, and respect Retry-After on 429/503. There are no automatic retries of business refusals or transfers. | Count attempts in controlled failure tests. U1 does not claim full U2 replay protection. |
| NFR14.2 | The approved verification command remains scripts/verify-dev.sh: a deployed API smoke check plus Flutter integration checks on the agreed iOS simulator and Android emulator. Each repo's dev deployment must pass its smoke check. | Record real execution evidence in Build and Test / deployment, with the exact commit and environment. No result is claimed in this requirements stage. |

## Recovery and rollback handoff

NFR Design and Infrastructure Design must describe how a human rebuilds dev and obtains new test credentials from the selected secrets store. Recreating wallets means fresh simulated balances and history; no reconciliation of lost dev transfers is promised. The process must avoid leaking credentials and must initialize each recipient needed by a verification run.

Rollback follows the team's existing last-known-good commit procedure. A rollback/rebuild is not performed merely by approving this document. Production retention, point-in-time recovery and the dev-to-stg-to-prd promotion rules remain for later units and deployment stages.

## Sources

- nfr-requirements-questions.md: Q1 option A, selected by the person.
- construction/u1-walking-skeleton/functional-design/functional-spec.md: transfer lifecycle and end-to-end check.
- construction/u1-walking-skeleton/functional-design/rules.md: BR2.1, BR2.2 and BR3.1 to BR3.3.
- inception/requirements-analysis/requirements.md: NFR3 to NFR5, NFR9 and NFR14.
- inception/contract-design/contract-summary.md: C1 retry and commit-versus-lost-response behavior.
- aidlc/spaces/default/memory/team.md: rollback, production retention and verification practices.
