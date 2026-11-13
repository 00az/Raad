# NFR Requirements: U1 Walking Skeleton Questions

Conversation language: English.

## Context already decided

- U1 covers the existing walking skeleton on `dev`: sign-in, balance, recipient lookup, one simulated transfer and the first history page across `Raad`, `RaadMoneyService` and `RaadMobile`.
- The MVP capacity target is up to 100 users, with about 10 active concurrently. At least 95% of transfer requests must receive a response within 2 seconds at the API at that load (NFR6 and NFR7).
- The 99.5% calendar-month availability target applies to `prd` (NFR5); it is not a new availability promise for `dev`.
- TLS 1.2 or later, encryption at rest, verified caller identity, environment isolation, whole-halala arithmetic and money-conservation tests remain required (NFR1 to NFR3 and C5).
- The client timeout is 15 seconds. Safe reads/setup have one bounded retry; transfers are never automatically retried. Full request-key replay remains assigned to U2; this stage does not extend U1 into that work.
- Logs and alarms must not contain passwords, tokens, email addresses or display names. Correlation IDs support investigation without distributed tracing (NFR8 to NFR11).
- Basic monitoring is required within the existing build. The monitoring email address and concrete alarm settings remain inputs to NFR Design / Infrastructure Design as already recorded.
- Python, Dart/Flutter and Python CDK are affirmed choices. Concrete data-store and sign-in-provider selection remains with Infrastructure Design. No new service is selected here.
- Production data-store retention and point-in-time recovery are already mandated by the team. The earlier record specifies no dev recovery or data-loss target.
- Functional Design was approved with its seven review findings accepted. This stage carries those risks without changing the approved Functional Design or the C1 contract.

## Q1. [Operations engineer] What recovery guarantee should the dev walking skeleton have after a loss of its data store?

The existing record specifies production retention and point-in-time recovery, but does not say whether dev test-wallet balances and transfer history must survive a disaster. This choice sets the backup and recovery requirement for the current U1 dev slice only.

A. Dev data is disposable. Recover by rebuilding the environment from infrastructure code and recreating the test accounts and wallets; prior dev balances and history may be lost. Set no guaranteed recovery time for this demonstration environment. A rebuild/reset remains an explicit engineer action, never automatic error recovery. (Recommended for the existing thin dev slice.)
B. Dev data must be recoverable. Require backups with at most 24 hours of lost test data and recovery within 4 hours. Infrastructure Design must choose and verify how to meet these targets.
X. Other (please specify)

[Answer]: A. Dev data is disposable: rebuild and recreate test wallets, with no guaranteed recovery time. (Selected by the person in the question reply; **Mode:** chat.)

The person's choice is preserved here. Its answer-log receipt is still pending because the previous project setup did not register this conversation's human replies. This text does not claim that the receipt succeeded.

## Sources

- `inception/requirements-analysis/requirements.md`: NFR1 to NFR15, demo scale, production availability and the existing monitoring boundary.
- `inception/requirements-analysis/requirements-analysis-questions.md`: Q7 to Q9, already answered.
- `inception/units-generation/unit-of-work.md` and `units-generation-questions.md`: the U1 dev scope and confirmed test-user setup.
- `inception/contract-design/contract-summary.md`: C1 request timeout/retry behavior, C3 sign-in profile and C5 token-verification boundary.
- `construction/u1-walking-skeleton/functional-design/functional-spec.md` and `rules.md`: U1 workflows and money invariants.
- `aidlc/spaces/default/memory/team.md`: production retention/recovery, affirmed stack and testing practices.
