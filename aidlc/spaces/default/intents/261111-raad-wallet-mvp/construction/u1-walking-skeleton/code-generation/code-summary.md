# Code Generation Summary — U1 Walking Skeleton

Conversation language: English.

## Current revision and ownership

This is current local implementation evidence for the approved Transactions/public-latency revision. U1 and its deployed walking skeleton remain incomplete. Engineer 1's platform/service changes are local and uncommitted; Engineer 2 retains all mobile source, generated-client and device-test ownership. No mobile source was edited in this revision. The parent published only the separate start guide in Raad commit e740b6bc8df68d317f1d81c7bdc7b8223690da34. The published service contract baseline remains 5dd760d; local partial release 1.0.0-u1.2 has not been pushed.

The source manifest retains all earlier claims and adds this revision's eight new application/test paths, for 58 paths total. Runtime caches, coverage databases, failed cdk.out bundles and deleted scratch patches are not application source and are not release artifacts. Existing root README.md, AGENTS.md and .gitignore were preserved.

## Implemented changes

- Money service provisions Ledger, Transactions and WalletDirectory. The frozen CompletedTransfer model serializes one immutable canonical row keyed by transferId, containing both wallet references, integer halalas, currency SAR, reference and UTC completion.
- A single five-action transaction updates both guarded wallet balances, inserts the canonical row conditionally and inserts two reference-only history entries. The old resource-client double serialization was removed; real DynamoDB Local now exercises native resource values successfully.
- History strongly queries a bounded page plus one lookahead, strongly batch-reads canonical rows, restores query order and checks ownership/order. Missing/corrupt canonical rows or exhausted unprocessed-key reads fail the page safely. U1 reports hasMore/X-U1-History-Truncated without inventing supported cursor navigation.
- The additive migration validates paired legacy payloads, refuses mismatches/unmatched rows, conditionally commits canonical plus reference conversion, reruns safely and verifies balances/history. It defaults to dry-run. No deployed migration was run.
- Canonical activation fails closed: CDK defaults ActivateCanonicalWriter to false; the service returns safe unavailable responses while disabled. Deployment expands with requests disabled, runs the no-write --check-ready count/reference gate, and activates only on success. Failed readiness leaves requests disabled for explicit engineer migration; a legacy payload-only rollback is incompatible.
- C1 errors are top-level code/message/correlationId. PUT creates/reads the wallet before repairing the directory; GET does not create. Internal wallet/holder IDs are removed from public shapes. The partial U1 artifact explicitly disclaims saved replay and uncertain resubmission; no business outcome record or false replay header is added.
- The edge signs an outer Function URL envelope containing the original method/path/query/body and allowlisted bearer/key headers. MoneyApi restores it only from an IAM-authorized event and independently verifies the original token. The outer SigV4 Authorization no longer overwrites the bearer.
- Verifiers reuse pinned PyJWT 2.15.1 clients with a 360-minute set cache, disabled indefinite per-key cache, one-second fetch and sixty-second unknown-key cooldown. This installed release implements locked/monotonic discovery and rejects redirects. The service validates C5's closed configuration/environment and disables profile redirects. Invalid tokens and discovery unavailability receive distinct safe responses.
- CloudFront transfers behavior has caching disabled and 100% real-time sampling of exactly seven safe fields. Platform telemetry uses an encrypted Kinesis stream, isolated processor, fourteen-day sample logs and a five-minute schedule with two-minute grace. The processor deduplicates native IDs, bounds queries, computes event-window counts/slow fractions/p95 and requires eligible consecutive breach/recovery windows. Incomplete/conflicting telemetry cannot emit a healthy pair. Metrics use Maximum gauges; handler timing is labelled diagnostic.
- Pure acceptance reconciliation requires one-to-one native response/log matches, retains failures and computes combined/sustained nearest-rank p95. This is not an executed load/instrumentation proof.
- Setup tooling creates separate fresh API/iOS/Android fixture pairs through Cognito and PUT, refuses identity collisions/reused opening balances, and stores runtime credentials only in the existing Secrets Manager fixture secret. The integrated wrapper preflights both device/config prerequisites, then runs API and both mobile journeys. Engineer 2 must provide its host-side runtime fixture consumption and mobile test.
- CI/deploy definitions retain independent repo checks, assembled service coverage and an independent Ledger coverage checker. Missing typing stubs were added. Ruff formatting/import fixes stayed within the approved source/tests. Pytest 8.4.2's reported PYSEC-2026-1845 finding was fixed by updating the dev constraint and both locks to pytest 9.2.0.

## Verification performed

Runtime: Python 3.12.4, pytest 9.2.0, pytest-cov 6.3.0, Hypothesis 6.170.15; DynamoDB Local image 2.5.2 on Docker 29.0.1. Local jsii warns that Node 26.12.1 is untested; pipeline definitions select Node 22. No warning was hidden as a fix.

| Check | Actual final result |
|---|---|
| Platform exact six test files from unit-test-instructions.md | 60 passed; combined line/branch coverage 88.84%; 391 statements/28 missed. Configured 80% floor passed. |
| Service assembled command: uv run pytest tests/unit tests/integration | 144 passed, including 22 real local-store/boundary cases; combined coverage 90.94%; 524 statements/38 missed. Configured 80% floor passed. |
| Ledger exact scoped JSON command from unit-test-instructions.md | 25 passed; 56/56 statements and 16/16 branches covered; report artifacts/coverage/u1-ledger.json. |
| uv run python scripts/check_ledger_coverage.py artifacts/coverage/u1-ledger.json | Exit 0: line=100.00%, branch=100.00%; floors independently enforced. |
| Platform Ruff check and format --check | Passed; all 14 checked Python files formatted. |
| Service Ruff check and format --check | Passed; all 26 checked Python files formatted. |
| uv run mypy raad_platform; uv run mypy src | Both passed: no issues in six source files per repo, strict configuration retained. |
| uv run pip-audit, each repo after pytest update | Both exit 0, no known vulnerabilities. The local service package has no PyPI entry and is not a third-party audit target. Cache-deserialization warnings were advisory. |
| bash -n scripts/verify-dev.sh | Exit 0. |
| scripts/verify-dev.sh | Exit 1 at preflight: RAAD_IOS_DEVICE_ID missing. No fixture/account mutation or API/mobile journey ran. |
| Real cdk synth --all with explicit nonsecret build fixture inputs, each repo | Both failed while bundling: public.ecr.aws/sam/build-python3.12 authorization token expired. cdk-nag completion and deployable packaging are unverified. |

Initial unchanged-tree baselines, before application edits, were platform 30 passed/89.95% and service 81 unit tests passed/93.20% on pytest 8.4.2. Parent recorded TDD Red for CompletedTransfer as an ImportError in the exact Ledger command before core implementation. The first Green had 18 passing tests but insufficient new branch coverage; added validation cases produced the final 25 passing/100% independent floors above.

Two intermediate failures were repaired, not suppressed: integration fixtures lacked the test correlation-secret ARN, and assembling unit/integration directories exposed duplicate module basenames. The fixture now supplies local-only configuration, and pytest importlib mode permits both directories without weakening coverage. An intermediate integration-only run passed all assertions but exited on whole-package coverage; the final assembled run above passed that floor. Earlier concurrent coverage output was discarded and the final Ledger report/checker ran sequentially after the assembled suite.

Both synths used build fixtures (account 111111111111/example.test), not asserted live deployment values. A documented anonymous public pull was attempted with an isolated empty Docker config and the existing daemon socket, then explicit --config/--host flags; both still returned the expired-token error. Global Docker credentials were untouched and the scratch config was removed. Inline-asset CDK assertion tests are not a substitute for successful real bundling/nag. No CDK deployment or production write occurred. The disposable local DynamoDB container was stopped afterward.

## Incomplete plan steps and release blockers

Only plan steps 1, 3, 4, 8 and 13 are marked complete. Mixed/mobile/deployed steps 2, 5, 6, 7, 9, 10, 11 and 12 remain unchecked; source and local proof completed within them do not establish their full acceptance.

- Mobile folder still contains only README.md. Flutter project, generated client, widget/coverage checks, config/dev.json, integration_test/walking_skeleton_test.dart and actual simulator/emulator identifiers/evidence belong to Engineer 2 and are not present here.
- Prior authorized account evidence identified 027863026273/us-east-1 and no suitable RAAD hosted zone/certificate/deploy role. Those historical observations were not reasserted as a fresh account inventory. Real public domain, zone/certificate, alert destination, RAAD-scoped deployment access, deployed pools/client/verifier/secret outputs and ready fresh fixture credentials remain provisioning inputs.
- Real Lambda bundling and cdk-nag must pass after the public-image access failure is resolved. GitHub Actions workflows were authored, not executed; no PR checks, reviewer approval, merge or deployment success is claimed.
- C3 P1/P2/P13, deployed configuration/identity isolation, full dependency-deadline fault behavior, protected logging/rotation investigation and all three dev journeys remain unproven. Local unit tests do not establish these live capabilities.
- Deployed legacy-schema inspection, controlled migration/activation/rollback and cost estimate are not executed. The disabled-writer/readiness gate is implemented and tested locally; it is not a completed cutover.
- No deployed initialization/origin-delay proof, alarm email delivery, telemetry-loss exercise, 100-user/10-active-user ten-minute load run, complete response/log reconciliation or accepted p95 result exists. The complete load/fault driver wiring and its live execution remain outstanding.
- Secret scanning was not independently executed in this revision; the authored Gitleaks CI step is not a passed scan.

Traceability was regenerated from current upstream IDs. Blocked/unbuilt work is GAP, not a human-approved deferral. Backend implementation/test evidence in the registered money-service@checkout is described explicitly; the current traceability validator only permits OK targets inside this project's directory and rejects sibling/checkout-alias targets. The manifest and this summary retain that evidence without fabricating local proxy source. Parent owns independent review and lifecycle settlement.

## Historical handoff context

Earlier commits 16129da (mobile handoff), 5dd760d (published C1 baseline) and 8a0d108 (shared split) remain historical handoff references. The earlier local API setup failure and two-table implementation are superseded by this revision's passing real-store suite and three-table design; earlier deployed/mobile completion was never claimed.
