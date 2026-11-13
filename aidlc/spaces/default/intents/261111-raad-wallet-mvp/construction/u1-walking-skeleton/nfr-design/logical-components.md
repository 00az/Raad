# Logical Components: U1 Walking Skeleton

Conversation language: English.

## L1 — Existing components and failure domains

| Logical part | Responsibility and owner | Failure boundary | NFR patterns |
|---|---|---|---|
| MobileApp, RaadMobile | Sign-in, secure token storage, generated C1 client, balance/send/history UI | One device/session; no authority to mutate balances locally | Integer money, one attempt per confirmation, safe read retry, no automatic uncertain-transfer replay |
| Shared sign-in service, Raad | Verified accounts, access tokens, own-profile source when selected | Sign-in/setup and verification keys; existing valid tokens can survive discovery failure within cache bounds | C3 capability checks and immutable environment-specific C5 configuration |
| Public API edge, Raad | /money mapping, token checks, basic firewall, safe errors/correlation, boundary metrics | Public money path; isolated from another environment | 9-second deadline, bounded key cache, admission limits, aggregate alarms |
| MoneyApi, RaadMoneyService | Independent caller checks, strict C1 adapter, orchestrating Ledger/directory | Money API request; profile failure affects setup/directory-dependent operations | 7-second deadline, bounded dependencies, safe errors/logging, response schema validation |
| Ledger, RaadMoneyService | Sole owner of Wallet/Transfer and balance mutations | Transactional money boundary | Atomic guarded changes, one opening credit, integer halalas, authoritative reads |
| WalletDirectory, RaadMoneyService | WalletHolder, verified profile copy and exact normalized-email resolution | Directory-dependent operations | Persistent uniqueness, bounded batch lookup, isolated personal attributes |
| Secrets and operational monitoring, owning repo infrastructure | Test credentials, protected correlation key, dashboards and notification delivery | Test setup/investigation; never a substitute money authority | Encrypted secret access, privacy allowlists, bounded telemetry, explicit retention |

Ledger and WalletDirectory remain logical modules behind MoneyApi, not new network services. Physical compute, store products, networking, provider, SDKs and monitoring resources remain Infrastructure Design selections. Shared physical storage is permitted only with clear logical ownership and supported atomic Ledger operations.

Text flow: MobileApp calls the sign-in service directly and sends access-token C1 requests through the shared API edge to MoneyApi. MoneyApi independently verifies the token, calls Ledger for money operations and WalletDirectory for profiles. Stores have no public client access. Operational signals go to the selected monitoring resources independently of the money outcome. No transfer event or queue is introduced.

## L2 — Decisions and tradeoffs

- **Bounded synchronous path:** deadlines, one safe retry and explicit admission replace extra circuit-breaker/queue services at the approved 10-active-user scale. A dependency outage gives a safe error rather than financial fallback. Tail latency is exposed, not discarded.
- **Strong money consistency:** no cache, replica or asynchronous credit is authoritative. Store transactions and unique owner keys remain required under horizontal execution. This constrains the physical store choice.
- **Logical privacy isolation:** personal attributes stay in WalletDirectory, money records use opaque IDs, logs use allowlisted operational categories, and caller correlation values are protected before logging. Protected correlation requires a compatible edge logging integration and key management; Infrastructure Design must verify it.
- **Disposable dev:** manual rebuild is allowed by the recorded recovery policy with no RTO/RPO. It can lose simulated history. Production retention/availability remain later requirements and are not weakened.
- **Measurements before capacity claims:** the 20-request admission proposal and per-stage timing budget are initial settings. Real dev load, atomicity and notification evidence are required before declaring them sufficient.

These are proposed NFR design choices for this Unit's approval. Authentication, scale, telemetry depth, recovery and feature boundaries carry forward the existing decisions. Numeric operating settings are reviewable engineering proposals, not newly attributed human requirements.

## L3 — Infrastructure handoff

| Required selection/proof | Input design | Owning next step |
|---|---|---|
| Sign-in provider/SDK, P1/P2/P13, profile source and P7 assessment | security-design.md S1–S3; C3/C5 | U1 Infrastructure Design |
| Edge capable of C5 independent verification, custom safe errors, protected correlation and total boundary timing | security-design.md S1/S5; observability-design.md O1–O3 | U1 Infrastructure Design |
| Ledger transaction layout, unique owner/directory keys, bounded history query and real local-container testing | scalability-design.md C2–C3 | U1 Infrastructure Design |
| Compute/connections/admission limits that support the 2-second target without overrunning the store | performance-design.md P1–P4; scalability-design.md C1/C4 | U1 Infrastructure Design |
| Test-user secret store and logging HMAC-key delivery, TLS and encryption | security-design.md S4; observability-design.md O2 | U1 Infrastructure Design |
| Dashboard, 14-day dev logs, sample-gated alarms and actual email recipient | observability-design.md O2–O5 | U1 Infrastructure Design and later deployed checks |
| Explicit manual dev-rebuild and rollback instructions with fixture readiness | reliability-design.md R4 | U1 Infrastructure Design / implementation |

The three repositories keep their own code and infrastructure, generated-client pins and independent dev deployment paths. Do not select or install a new framework, cloud product or runtime version in this stage. Implementation verifies supported versions and commits lockfiles. The testing cadence remains TDD for money-core rules and test-after elsewhere, with all affirmed coverage and CI/security checks preserved.

## L4 — Accepted upstream concerns and delivery limits

The approved Functional Design still has seven recorded concerns: missing holder registration/repair; GET setup conflicting with C1 PUT; incompatible public field mapping; missing displayed reference/email; unready/reused fixtures; missing history tie order; and unsafe amount-text conversion. This design leaves those upstream files unchanged. C1/C5 and the new NFR requirements remain mandatory; implementation must expose incompatible behavior in tests and cannot cite earlier approval as evidence of contract compliance. No finding is described as fixed merely because a downstream constraint mentions it.

Full durable replay, complete amount-range/self-transfer behavior, later-page navigation, full account screens/session lifecycle, complete per-caller rate controls, confirmation events and later environment delivery remain with U2/U3/U4 as previously allocated. U5's landing page is outside U1. No real payments, AI assistant, Qattah, extra region or distributed tracing is introduced.

## Sources

- construction/u1-walking-skeleton/nfr-requirements/tech-stack-decisions.md: affirmed stack, quality floors and deferred choices.
- construction/u1-walking-skeleton/nfr-requirements/performance-requirements.md, security-requirements.md, scalability-requirements.md, reliability-requirements.md and observability-requirements.md: NFR design obligations.
- construction/u1-walking-skeleton/functional-design/functional-spec.md, entities.md, rules.md and frontend-components.md: current Unit boundaries and accepted concerns.
- inception/domain-design/components.md: the existing application building blocks and ownership.
- inception/contract-design/contract-summary.md: C1/C3/C5 integration, authoritative wire shapes and later completion boundaries.
- aidlc/spaces/default/memory/team.md and project.md: repository, quality, deployment and money/privacy rules.
