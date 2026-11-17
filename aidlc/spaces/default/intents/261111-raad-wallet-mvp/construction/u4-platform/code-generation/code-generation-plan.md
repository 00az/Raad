# Code Generation Plan — u4-platform

## Summary

- Builds: shared identity, C2 events, platform rate limits, monitoring and environment outputs for U2/U3.
- Touches: infrastructure/, contracts/, platform scripts, Raad CI, environment examples and generated-file ignore rules.
- Tests: approximately 60–90 new unit/contract cases, local DynamoDB concurrency checks and existing platform regressions; live checks stay pending.

Conversation language: English.

## Ownership and Coordination

Engineer 1 owns only U4 in Raad, on `aidlc/u4-platform-aziz`. Claim generation 1 was made from main `5293bbb6afc0b9d64202ad6723f3cabf208a3392`; local merge `9b6fc13` brought that main into this branch. U2 code remains in RaadMoneyService at the fetched `2b3660b`; it is reference input only. Do not edit its source, pins, queues, tables, migration scripts or workflow. U3 mobile and U5 web remain with their owners. A consumer incompatibility becomes a precise handoff to the co-engineer.

This is a platform coding plan, not deployment authorization. The verified local `raad-dev` identity is in account `305780340110`; authentication does not authorize infrastructure creation or enabling GitHub deployment. Keep all planned checks local with synthetic configuration. Do not create the OIDC role, populate deployment variables, upload assets, publish contract tags or run deployed smoke/load/email/restore checks in this stage. Build the smoke/capability tools without executing them against AWS.

## Authoritative Handoff and Resolved Inputs

The person's 16 November handoff (message 1ba86413) supersedes the old account, Dynu/external-DNS plan and literal alarm addresses in earlier designs:

- Target account `305780340110`, region `us-east-1`; existing Route 53 zone `Z024897018YB0PKUPOPY7` for `raadwallet.com`.
- Existing certificate input: `arn:aws:acm:us-east-1:305780340110:certificate/6a561a29-d6a4-4333-b7e3-de412e20717c`. Planned hosts: `dev.api.raadwallet.com`, `stg.api.raadwallet.com`, `api.raadwallet.com`. These are supplied inputs, not independently verified AWS resources.
- Keep the existing optional hosted-zone path and explicit TLS 1.2 viewer policy. No domain purchase, hosted-zone creation or free-DNS provider integration.
- Alarm destination comes only from `RAAD_ALERT_EMAIL` in gitignored local/protected environment configuration. Do not read it into the record, replace it, put an address in source/docs/logs, or send notifications.
- Remove hosted UI/OAuth configuration and the required `RAAD_COGNITO_DOMAIN_PREFIX`; native SRP plus independently validated SDK tokens/GetUser is the selected flow.
- C3 password minimum is 8, requiring lower/upper/digit and no symbol requirement. Match A4, including `Abcdef12`; no silent strengthening.
- Native alarm recovery clears on one healthy evaluation, as the handoff accepts. Preserve breach windows and record the deviation from three healthy windows in the current U4 evidence.
- Dev has not been deployed. After separate cost authorization, deploy the completed platform first and U2 directly second. Do not deploy U1 MoneyService first or run historical U1 index/ordinal migrations on a fresh environment.
- The latest handoff's cost estimate is not a spending approval or a fresh price claim. No paid Cognito Plus plan is selected.
- P7 earlier-code invalidation and all other live provider guarantees remain unverified. There is no invented pre-confirmation trigger; failure goes back to the co-engineer/person before identity acceptance.

## Implementation Steps

Each checkbox is one sequential Step. Platform layers use implementation followed by tests, preserving the exact mixed cadence in the Testing Contract. Test runner readiness precedes all new executable test work.

- [ ] **Step 1 — Verify ownership, baseline and change surface.** Check the U4 claim, current branch/working files, main CI and the fetched U2 integration references without changing another unit. Inventory source/consumers and preserve existing logical IDs. Record the unchanged-tree platform suite, lint/types and relevant configuration before implementation. A prior passing PR run is historical evidence, not a new baseline result. Stories: all seven U4 stories; NFR14.
- [ ] **Step 2 — Prepare the U4 test runner and fixtures.** Keep Python 3.12, uv lock, pytest/Hypothesis, strict mypy and Ruff. Add only needed schema-validation development dependencies and local DynamoDB integration configuration in `infrastructure/pyproject.toml`, `uv.lock`, `docker-compose.yml` and `tests/conftest.py`. Prove `uv run pytest tests/test_identity_stack.py --no-cov -q` runs before first new tests. Use synthetic account/certificate/hosts and local JWT keys; no AWS credentials in offline tests. Stories: US6.2; NFR14.10.
- [ ] **Step 3 — Materialize C2–C5 provider contracts, then tests.** Preserve C2 source `raad.identity`, detail-type `raad.identity.user-confirmed.v1` and payload in `detail`. Write canonical C3/C4/C5 files at the paths in Contract Design, with version/release semantics reconciled with the existing U2 verifier representation and mobile C4 shape. Add `tests/test_platform_contracts.py` for schema validity, prohibited/unknown output fields, environment binding, transport/error shape and compatibility. Provider emission must have exactly declared fields even where C2 permits additive fields to consumers. Changes needing consumer work are coordinated, not hidden behind a new profile shape. Stories: US1.1–US1.3, US1.5–US1.6, US3.5, US6.2; C2–C5.
- [ ] **Step 4 — Apply native identity settings, then regression tests.** Update `IdentityStack` and callers in `stacks.py`/`app.py`: case-insensitive email sign-in, public SRP client, prevent-user-existence errors, access 60 minutes, refresh 30 days, token revocation, required email/name only and immutable user-editable profile fields as C3 requires. Remove hosted UI/OAuth resources and prefix requirement. Keep the controlled test-fixture authentication flow only if the selected SDK/service requires it and scoped tests prove compatibility. Update `test_identity_stack.py` for A4, P3/P5/P6/P9 and no paid Plus. Record fixed refresh lifetime versus U3-owned idle tracking; do not claim a rolling 30-day idle guarantee from configuration alone. Stories: US1.1, US1.3, US1.5, US1.6; C3 P1–P9/P13; NFR1.10/NFR11.10.
- [ ] **Step 5 — Add C2 bus and post-confirmation publisher, then provider tests.** Add a per-environment bus and bounded publisher module under `raad_platform/identity/`, scoped role, log group and Cognito trigger wiring. Publish only `PostConfirmation_ConfirmSignUp`, never password-reset confirmation. Construct UUID eventId/trusted UTC occurredAt/environment/subject/confirmed email/name from the trusted trigger; read routing/schema constants from the canonical contract in tests. Handle exceptions and PutEvents partial failure with safe aggregate telemetry, return the original event unchanged on publication failure, and never log the trigger/profile. Add `test_identity_publisher.py` (success, wrong trigger, incomplete/unverified profile, SDK/partial failures, undeclared fields, no PII). Stories: US1.2; C2/C3 P12; NFR4.10/NFR9.11/NFR10.10.
- [ ] **Step 6 — Publish shared SSM boundaries and enforce publisher access, then stack tests.** Export `/raad/<env>/event-bus/arn` and `/raad/<env>/alarm-topic/arn`, with the existing `raad-<env>-alerts` topic; preserve matching verifier/edge-role/correlation-secret outputs used by U2. Bound PutEvents to the publisher role and contract source/detail type, considering same-account identity policies so an allow-only bus statement is not misrepresented as exclusivity. Add assertions for resource policies, exact ARNs, environment separation, encryption and no circular dependence on the U2 stack. U2 retains ownership of the rule, queue, delivery DLQ, processing DLQ and idempotent consumer. Stories: US1.2, US6.2; U2 R-02/R-06.
- [ ] **Step 7 — Implement platform counter storage, then unit/concurrency tests.** Add platform-owned `PlatformRateWindows` table and rate-store module, encrypted/on-demand, bounded IAM and TTL cleanup at two hours. Use server-minute windows and HMAC-derived subject keys with no profile data. Atomic conditional consumption must charge both lookup and send counters together or neither. Delayed TTL deletion cannot reopen a window; key rotation cannot reset active windows. Add `test_platform_rate_store.py` and Docker-backed `tests/integration/test_platform_rate_limits.py` for contention, exact admission, combined rollback, boundary rollover, TTL lag, caller/environment isolation and unavailable store. No money data or request keys are stored. Stories: US3.5, US1.3; NFR12.11/NFR7.11.
- [ ] **Step 8 — Enforce verified-caller limits at the edge, then request tests.** Return verified subject from authentication and apply lookup 30/min, send 10/min (also one lookup), and shared other read/setup/history 60/min before service invocation. Never trust caller identity headers. Quota refusal is flat C1 429 RATE_LIMITED plus remaining-window Retry-After; counter failure is safe 503 with bounded dependency calls. A denied request cannot reach U2 or consume a financial request key. Add `test_platform_rate_limits.py` and extend `test_edge_adapter.py` for exact paths, caller independence, request/header/body/query preservation and failure mapping. Preserve constant-time origin checks, original bearer, SigV4 and no authenticated caching. Stories: US3.5, US1.3; C5; NFR9.10/NFR12.10–12.11.
- [ ] **Step 9 — Protect direct Cognito operations, then regional WAF assertions.** Associate environment regional WAF with the pool. Account operations get approximate 100/IP/5min and general non-profile operations 300/IP/5min; explicitly exclude GetUser from both. Verify provider operation metadata against current AWS primary documentation before coding it. Keep sampling/raw request logging off and emit no PII dimensions. Test associations/classification/exclusions and independent coarse CloudFront protection. Apply only resource/check-specific COG8 exceptions for unapproved paid Plus in dev/stg/prd with rationale and retained release risk; do not disable nag checks. Real operation classification, two-caller isolation and provider refusal mapping remain deployed gates. Stories: US1.1–US1.3/US1.5; C3 P10/P11; NFR12.11.
- [ ] **Step 10 — Complete environment stacks/configuration, then assertions.** Make dev/stg/prd explicit and validated, preserve stable logical IDs, retention and secrets. Use the existing zone/certificate as inputs, with account/region/environment checks before any future deployment. Replace stale account examples in `infrastructure/.env.example` and `infrastructure/README.md` with placeholders, document the new native flow, and leave `.env.local` intact. Add generated coverage/runtime/scratch ignore patterns to root `.gitignore` without deleting local files. Update stack tests across all environments, preserve x86_64/linux-amd64 packaging and explicit TLS 1.2. Stories: US6.2; NFR2.10–2.11/NFR9.11/NFR14.10.
- [ ] **Step 11 — Generate validated C4/C5 outputs, then writer tests.** Add `raad_platform/configuration.py`, `scripts/write_platform_config.py` and `test_platform_config_writer.py`. Accept one environment's coherent deployment-output document and produce C4 `config/<env>.json` plus verifier configuration with no secrets. C4 keys are exactly configVersion/environment/apiBaseUrl/moneyBasePath/authIssuer/authAudience/authClientId; C5 follows the canonical verifier schema and selected native GetUser profile. Validate all values against the same environment's outputs, not hostname substrings alone; refuse missing/extra/cross-environment/secret-looking fields and overwrite of unrelated files. Offline fixture mode does not call AWS. The generated public file is delivered to U3, without editing RaadMobile. Stories: US6.2, US1.6; C4/C5; NFR1.10/NFR9.11.
- [ ] **Step 12 — Complete alarm windows and safe telemetry, then tests.** Extend monitoring/processor gauges and dashboards for two 5-minute windows of technical 5xx >=1% with >=20 eligible requests, technical transfer failures >=3/5min, public p95 >2000ms with >=20 complete samples, throttles >=1/min for two windows, publisher/event failures and collector heartbeat absent three minutes. Preserve low-volume/incomplete observation as missing/insufficient evidence and separate observation-health alarms; any U2 DLQ requires operator reconciliation. Record native one-evaluation recovery as accepted deviation; do not change breach criteria to make tests green. Keep current public sample reconciliation, safe seven-field logging and retention. Update monitoring/public-latency test files. Alarm address is configuration only, with no notification execution. Stories: US6.2; NFR5.10/NFR6.10/NFR8.10–8.11/NFR10.10/NFR15.10; U2 R-04.
- [ ] **Step 13 — Add isolated dev stub mapping, then routing tests.** Add a dev-only nonfinancial stub and explicit path mapping independent of MoneyService source/C1. Add `test_platform_mapping.py` for correct route, unknown path, disabled stg/prd mapping, origin restriction and unchanged /money behavior. No catch-all cross-environment target. Stories: US6.2; NFR13.10.
- [ ] **Step 14 — Build platform smoke and capability tools, then offline tool tests.** Add `scripts/platform_smoke.py`, `scripts/check_identity_capabilities.py`, `test_platform_smoke.py` and `test_platform_capabilities.py`. Scope by account/environment/expected outputs, reject mismatches before actions, load secrets only at runtime, log no token/code/profile/address and fail when mandatory evidence is absent. Offline tests inject clients/HTTP/clock; real execution is opt-in. Include C3 P1–P13 evidence checklist, especially two confirmation codes for P7, SDK GetUser compatibility, origin/TLS protection and C2-trigger-to-U2 readiness. Mark live scenarios pending rather than implementing always-passing placeholders. Stories: US1.1–US1.3/US1.5–US1.6/US6.2; C2–C5.
- [ ] **Step 15 — Wire offline CI and run local gates.** Update Raad PR CI to run canonical contract/provider/config-writer tests and actual local-store integration; keep no deployment credentials in PR CI. Preserve format/lint/strict types/audit/Gitleaks/80% repo coverage and actual Docker CDK synth/nag. Run all U4 scoped commands and assembled suite, synthetic synth for each environment, native asset checks and secret scan. Do not enable or repair AWS deployment by creating credentials/roles; staged/prod promotion execution belongs to later pipeline/deployment stages. Stories: US6.2; NFR14.10.
- [ ] **Step 16 — Record evidence, independent review and co-engineer handoff.** Update checked steps only when actually completed. Write source manifest, code summary, exact validation results and requirement-level traceability including every detailed U4 NFR. Separate local implementation from deferred live checks and accepted deviations. Record output paths/contract revisions for U2/U3, platform-first/fresh-U2 deployment order, remaining P7/cost/provider gates and GitHub OIDC work. Obtain the separate architecture review and the person's U4 checkpoint. When this claimed unit is complete, use the supported `aidlc unit publish u4-platform` path through the installed workflow; Ziyad's side pins/gates/lands the handoff. Do not claim publish/merge/tag/deployment success before those operations actually succeed. Stories: all U4 stories; U2 R-02/R-04/R-06.

## Story-to-Step Traceability

| Story / obligation | Steps | Boundary |
|---|---|---|
| US1.1 Sign up | 3, 4, 9, 14 | U4 provider settings; U3 normalizes client email and owns bilingual screens |
| US1.2 Confirm email/wallet | 3, 5, 6, 14 | U4 event; U2 creates wallet idempotently; P7 remains a real-provider gate |
| US1.3 Sign in | 4, 8, 9, 14 | Native SRP, generic client refusal support, coarse account protection |
| US1.5 Password reset | 4, 9, 14 | A4 and reset settings; password-reset confirmation never publishes C2 |
| US1.6 Stay signed in | 3, 4, 11, 14 | 60-minute access/30-day fixed refresh; U3 owns idle fallback |
| US3.5 Recipient abuse limits | 7, 8 | Atomic 30 lookup/10 send limits; U2 refusal/money rules unchanged |
| US6.2 Per-environment platform | 1, 2, 6, 10–16 | Offline infrastructure/configuration/smoke code; actual environment proof deferred |
| C2 producer / U2 R-06 | 3, 5, 6, 14, 16 | No final release tag until provider tests pass and code lands on main |
| U2 R-02 | 6, 10, 16 | Both SSM outputs; fresh platform then U2; no U1 migration on empty tables |
| U2 R-04 | 12, 14, 16 | Accepted native recovery deviation; actual email/load/restore not yet proven |
| NFR1.10 / 2.10–2.11 | 3–6, 9–11, 14 | Independent identity/TLS/encryption/configuration checks |
| NFR4.10 / 5.10 / 6.10 | 5, 6, 12, 14 | Event safety, availability/recovery and public latency |
| NFR7.10–7.11 | 7–10, 12, 14 | Bounded dependencies, 100-user/10-active acceptance remains live |
| NFR8.10–8.11 / 15.10 | 12, 14 | Full window policies, observation completeness and UTC |
| NFR9.10–9.11 | 5–8, 10, 11, 14 | Bounded failure and fail-closed outputs |
| NFR10.10 / 11.10 | 4–9, 11, 12, 14 | No sensitive/profile logs, minimal stored attributes |
| NFR12.10–12.11 / 13.10 / 14.10 | 7–10, 13–16 | Perimeter, rates, isolated mapping and unchanged quality floor |

## Change Surface and Compatibility

Primary changes: `infrastructure/app.py`, `raad_platform/stacks.py`, `edge/handler.py`, focused identity/rate/configuration modules, telemetry only where needed for missing policies, corresponding tests and local integration fixtures; canonical `contracts/c2–c5` files; new platform scripts; `.github/workflows/ci.yml`; named infrastructure examples/README and root `.gitignore`. Dependency/requirements/lock changes must be necessary and recorded. Do not refactor unrelated modules or edit older reviews/state/audit files.

The current edge differs from C5 on accepted correlation syntax and some forwarded headers. Reconcile it deliberately with the canonical contract and the U2 transport consumer in Steps 3/8; no silent protocol change. Preserve the flat C1 error schema and environment-bound verifier format already consumed by U2.

The current deployment workflow remains intentionally unable to authenticate. The plan does not introduce a working deploy role or trigger any AWS resource changes. A final U4 PR/publish is separate from automatic approval to incur the quoted dev cost.

## Acceptance Boundaries and Remaining Gates

Local completion requires source/tests, actual packaging/synth/nag for all environments, coverage/lint/types/audit/secret scan, independent review and accurate evidence. It does not prove deployed readiness. P7, actual WAF metadata/GetUser isolation, provider email/reset behavior, protocol rejection, public p95/load, complete observations, email delivery and coherent restore drill remain release checks. If a provider cannot meet C3, return the exact gap to the co-engineer/person; do not fabricate a hook or lower an acceptance criterion.

Existing architecture risks and the mobile PR #1 navigation finding remain owned by their records/engineers. U4 does not silently mark them fixed.

## Inputs

- Current U4 NFR requirements/designs and infrastructure specification/monitoring/pipeline.
- Shared requirements, domain components, units and story map; C2–C5 in Contract Design.
- Canonical C2 file and fetched U2 `2b3660b` deploy/consumer boundary.
- Person's handoff 1ba86413, merge authorization 52c987b1 and continuation 1dbe2a50.
- Exact Testing Contract below; test-after applies to this platform unit.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.",
  "scope": "classic",
  "test_strategy": "standard",
  "project_type": "greenfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Methodology evidence**: We chose this mixed cadence at the practices interview. RAAD's central risk is money movement: balances must be right after every transfer, and a repeated request must never move money twice. In that small core of `RaadMoneyService` the tests are the specification, so writing them first costs little and catches the defects that matter most. Everywhere else, the org default cadence (test-after) keeps us on the short timeline. This posture differs from the org default only for the money-movement core.\n- **Ordering**: For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.\n- **Coverage**: Each backend repo (`Raad`, `RaadMoneyService` and later `RaadAiService`) and the mobile repo (`RaadMobile`) holds at least 80% line coverage on its own. The money-movement core in `RaadMoneyService` also holds at least 95% line and branch coverage. We never lower a floor to make a step pass, and coverage on `main` never decreases in any repo. `RaadWeb` is static HTML and CSS with no code to measure; its smoke test checks it after every deploy.\n- **Money-movement checks** (in `RaadMoneyService`, required in addition to coverage):\n  - Property-based tests with Hypothesis show that, for any sequence of transfers, the total money across all wallets stays the same and no balance goes below zero.\n  - A replay test shows that sending the same transfer request again returns the original result and moves money exactly once.\n  - A concurrency test shows that simultaneous transfers out of one wallet can never overdraw it. It runs against a real local container of the data store in Docker, not a mock.\n  - Rejection tests cover insufficient funds; a zero, negative or over-precise amount; an unknown recipient; a transfer to oneself; an unauthenticated caller; and access to another user's wallet.\n- **Test types** (Standard test strategy):\n  - Service repos (`RaadMoneyService`, and later `RaadAiService`): unit tests with pytest and Hypothesis, and integration tests against local containers in Docker.\n  - Infrastructure (`Raad`'s platform stacks and each service's own stacks): pytest tests of the CDK stacks, alongside the cdk-nag checks that run on every synth.\n  - `RaadMobile`: unit and widget tests with `flutter test`, and end-to-end tests with `integration_test` on an iOS simulator and an Android emulator.\n  - Deployed environments: each deployable repo's pipeline runs a smoke test against the environment after every deploy. A service's smoke test calls its deployed API, `RaadWeb`'s fetches the landing page, and `Raad`'s checks the shared pieces it deployed (for example that the API domain answers and a test user can sign in).\n- **CI**: Each repo's full suite runs in GitHub Actions on every pull request, and a pull request merges only when the suite is green. The suite runs again on every push to `main`. Any failure blocks.\n- **Setup**: Each repo's README documents one setup command and one test command, and lists that repo's prerequisites: in the Python repos, `uv`, Node.js for the AWS CDK CLI, and Docker where the tests or builds need it; in `RaadMobile`, the pinned Flutter SDK and, for the simulator tests and app builds, Xcode with CocoaPods and the Android SDK."
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:67e5bbb80db5d51b2847a7275866f774aaee32fcb4f9b6c3ad6d429836b14ece",
  "contract_sha256": "sha256:7d7f077a74e1c8ed59b1ec6ddd9f041d8db0c6a93d62e46cc8c573d062f59d5e"
}
```
