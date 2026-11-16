# Technology Decisions: U1 Walking Skeleton

Conversation language: English.

## Decisions carried forward

The team has already selected the languages, application framework and infrastructure tooling. This stage records those choices and the capabilities required of the remaining selections. It does not select a new AWS service or move a decision out of its agreed later design stage.

| Area | Existing decision | Rationale/source |
|---|---|---|
| Shared platform | Python with AWS CDK | Affirmed team practices; infrastructure remains versioned with its owning repo. |
| Money service | Python; MoneyApi, Ledger and WalletDirectory retain their approved boundaries | Domain Design and U1 Functional Design isolate the money core and personal directory data. |
| Mobile app | Dart/Flutter for iOS and Android | Affirmed team choice; U1 contains only the English skeleton screens. |
| Public interface | C1 OpenAPI 3.1, HTTPS/JSON at /money/v1; Dart client generated from a pinned contract | Contract Design; handwritten mobile request/response models are not substituted. |
| Python environment | uv with committed lockfile; one supported pinned Python version across Python repos | Team practices. The concrete runtime version is verified and pinned during implementation/infrastructure selection. |
| Python checks | Ruff, strict mypy, pytest, Hypothesis, dependency audit and CDK security checks | Existing quality requirements; no coverage floor is lowered. |
| Mobile checks | dart format, flutter analyze with the affirmed lint rules, flutter test and integration_test | Existing mobile testing practices and the walking-skeleton verification. |
| Delivery | Independent repo pipelines in GitHub Actions, short-lived AWS credentials, dev-first checks | Affirmed delivery practices; U1 proves the three repos' dev path. |

## Required capabilities of deferred selections

| Selection | Required capability | Owning next step |
|---|---|---|
| Ledger/WalletDirectory data-store product and remaining physical layout | Whole-halala integer storage; dedicated Transactions table keyed by transferId with sender/recipient wallet references; atomic guarded debit, credit and immutable transfer row; one wallet per owner; encrypted persistence; bounded first-page queries; appropriate local-container tests | Infrastructure Design, informed by NFR Design and ADR-008. The dedicated table is already decided; the data-store product remains for Infrastructure Design. U2 adds history indexes and saved idempotency outcomes. |
| Sign-in provider and SDK | C3 P1/P2/P13 for U1, verified access-token identity, environment-specific issuer/audience and an approved profile-attribute source | U1 Infrastructure Design; remaining P-checks stay assigned to U4. |
| Public gateway/firewall implementation | C5 forwarding, verification, safe error/correlation behavior and U1's basic firewall | U1 Infrastructure Design; complete rate policies remain U4 work. |
| Secret store | Setup reads test-user passwords without committing or logging them | Infrastructure Design. |
| Monitoring resources and settings | Dashboard, safe metrics, the existing three alarm categories and email delivery | NFR Design / Infrastructure Design. |

## Quality requirements

| ID | Requirement | Verification |
|---|---|---|
| NFR14.3 | Each backend and mobile repo retains at least 80% line coverage; the Ledger money-movement core also retains at least 95% line and branch coverage. Money-core work is test-first; other layers use the affirmed test-after cadence. | Each repo's full local suite and matching CI checks report the applicable floors. No implementation or coverage result is claimed here. |
| NFR14.4 | Infrastructure changes are Python CDK code with the existing security checks. Repo changes follow the team's PR, review, short-lived branch and squash-merge practices. | Build and Test / CI Pipeline capture actual check evidence. This document performs no commit, merge or deployment. |
| NFR11.2 | Chosen SDKs, stores and telemetry do not require collecting personal attributes beyond email and display name. | Review configuration/schema requirements before selecting a dependency or service. |

## Boundaries and open inputs

There is no requirement for an AI assistant, Qattah, real payment provider, extra region, distributed tracing system or larger capacity tier in U1. The static landing page remains U5.

Exact runtime/package versions are not asserted from memory. The owning implementation stage verifies the supported versions and commits the appropriate lockfiles. The remaining infrastructure choices above stay open intentionally, as the approved earlier contracts require.

## Sources

- construction/u1-walking-skeleton/functional-design/functional-spec.md and rules.md: components, workflows and invariants.
- inception/requirements-analysis/requirements.md: NFR2, NFR3, NFR7, NFR11 and NFR14.
- inception/contract-design/contract-summary.md: C1 generated client, C3 provider capability checks and C5 edge requirements.
- aidlc/spaces/default/memory/team.md and project.md: affirmed stack, tooling, testing, delivery and project boundaries.
- inception/units-generation/unit-of-work.md: U1 and later-unit responsibilities.
