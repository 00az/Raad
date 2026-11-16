# Code Generation Summary — U1 Walking Skeleton

Conversation language: English.

## Latest repair — approved message 8c6cc35f

This section supersedes all older default-hostname/ARM64/failing-synth statements below. The person deferred only AWS deployment/live execution in fcf6b4bc; local coding continued. Backend local repairs and checks now pass. U1 remains unverified against AWS. No resource creation, credential lookup, upload/deployment, live provider/account/secret/migration/API/device/load/alarm action, workflow trigger, push/merge or external message occurred.

### Source changes and controls

- A controlled hostname and custom ACM us-east-1 certificate are mandatory together. External DNS omits Route53 resources; an optional existing zone retains aliases. Default certificates/incomplete pairs are refused. Both modes enforce TLS1.2_2021, with no TLS exception. Published SSM/public-URL output and explicitly synthetic CI fixtures now agree with this design. Actual DNS ownership, issuance and C4 environment output remain Deferred.
- Both backends use explicit Lambda X86_64 and Docker linux/amd64. Fresh native cryptography assets are ELF64 x86-64: platform asset5879441340fe8bb3abcb801c47fe7a4f785ccb7af8285bd82a8e0ec212263b6d; service asset0373561e456b6241da601e7a1751b126e9ef876aa0b308978fe2090bf3531c01. Existing x86 CI needs no assumed ARM emulation. Older ARM assets are historical local files, never uploaded.
- Explicit execution roles replace AWSLambdaBasicExecutionRole and scope writes to precreated log groups. Scheduler invokes only the exact processor ARN. StartQuery/GetQueryResults target the safe sample group. SNS denies non-TLS Publish. API access logs expose only opaque requestId/status/latency with fourteen-day retention.
- Preserved WAF, both-origin secret checks, independent JWT/GetUser/subject/verified-email verification, original bearer SigV4 envelope, disabled caching, safe seven-field public telemetry, canonical five-action transfers and no U1 replay promise. No money-core/opening-credit rule changed.
- Changed existing platform stacks/tests, CI fixture, env example and work-created infrastructure README; service infrastructure/tests. All application/config paths are already covered by the retained62-path source manifest, including identity/monitoring tests. No source claim was dropped. Root README/AGENTS/.gitignore and mobile source were preserved. The new security directory contains generated verification artifacts, not application source.

### Narrow documented check exceptions

Exceptions are adjacent to their resources, not global: COG8 on dev user pool only (simulated/no-real-payment slice, paid Plus not authorized; strong password/verified-email/token/perimeter controls tested); SMG4 on two protocol secrets (coordinated HMAC current/previous key retention and CloudFront/edge rollout, not a managed database rotation target); L1 on Python functions (approved tested3.12/AL2023 pin, supported managed patches through2028-10-31 and dependency audits); IAM5 only processor Resource::* (StopQuery has no resource type; standard namespace metric publishing is namespace-constrained, while StartQuery/GetQueryResults are resource-scoped); CFR3 only distribution (standard logs would violate the approved IP/query/user-agent exclusion; safe realtime/API/edge alternatives tested); APIG4 only two routes (mandatory independent authentication is in edge to preserve C1-safe errors, tested against bypass/spoofing).

No CFR4/TLS, blanket or paid-feature exception exists. SNS3/IAM4/scheduler wildcard/APIG1/CFR4 were corrected, not waived. Tests verify scoped metadata, concrete compensating controls, safe log fields, narrow permissions and x86 bundling. Advisory MFA/geo/dev-PITR/deprecation/cross-stack warnings remain; no production security claim follows. AWS lists3.14 stable and3.15 preview; the tested supported pin was retained rather than blindly migrating major runtimes. See [runtime support](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html), [Logs action resources](https://docs.aws.amazon.com/service-authorization/latest/reference/list_logs.html), and [namespace restrictions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/iam-cw-condition-keys-namespace.html).

### Fresh local evidence

| Check | Result |
|---|---|
| Unchanged-tree platform baseline |138passed/86.00%. Affected isolated service-stack baseline had10 passing assertions; it did not establish whole-package coverage. |
| Platform exact coverage command in instructions | **145passed/86.09%,exit0**. |
| Exact eight-file service U1 unit command | **133passed/89.35%,exit0**. |
| Service `uv run pytest tests/unit tests/integration` | **155passed/90.62%,exit0**, including22 real DynamoDB Local cases. Disposable container stopped. |
| Both repos' Ruff check/format and strict mypy commands in instructions | All exit0; platform18 formatted/9 typed files, service25 formatted/6 typed files. |
| `uv run pip-audit` in each repo | Both exit0/no known dependency vulnerabilities; service's local unpublished package is explicitly skipped. |
| Exact platform external-DNS and service synthetic-fixture `cdk synth --all` commands in instructions | **Both exit0**, including actual amd64 Docker bundles and cdk-nag. Platform reran successfully after narrowing GetQueryResults to its supported log-group resource. No lookup/publish/deploy command ran. |
| Native asset `file` inspection | Both fresh `_rust.abi3.so` files are x86-64 ELF, matching X86_64 functions. |
| Scoped diff checks | Pass for repaired application/config files. Historical tool-owned audit whitespace was not edited. |

Old default/ARM assertions initially failed after the approved behavior change and were updated to the new requirements before passing. No threshold was reduced. No money-core edits occurred; previous TDD and independent100% line/branch Ledger evidence remain valid historical evidence. Node26.12.1 jsii and ignored --all warnings remain explicit; CI selectsNode22. Synthetic inputs are account111111111111/example.test/build ARN fixtures, never ownership or live endpoint claims.

### Qualified local secret scan

Official Gitleaks v8.24.2 pinned digest `sha256:b5918eb91b8d2473cec722f066abb4352e4ffdc4ec9f4283ec143aba9ec9ebc4`, documented dir mode/full redaction, offline/read-only working-tree mounts. Raw scans exit1: Raad355 findings/93.44MB, service235/28.35MB. All service findings and354 Raad findings are generated cdk.out vendored SDK/examples/cryptography/PyJWT matches. Parent inspected the one authored U2 requirement-prose match and confirmed no credential value: false positive. No application credential was found; this is qualified triage, not a clean raw/history/CI scan. No broad exclusion or other-unit edit was added. Redacted raw reports and bounded classification are at `security/{raad,service}.json` and `security/scan-notes.md`.

### Deferrals and ownership gaps

Trace rows for actual DNS/ACM/protocol checks, deployment/provider proof, dev API/device journeys, alarms/correlation and public load/timing are Deferred with fcf6b4bc and unmet prerequisites; no live result was counted OK. Existing procedures are retained. P7 remains unverified; no unsupported pre-confirmation trigger was invented. Failed or unbuilt local work stays GAP.

Steps1/3/4/5/6/7/8/10/11/12/13 are reconciled/ticked; Step12 records only the authorized live deferral. Steps2/9 remain open for Engineer2's mobile/client-revision reconciliation; prior mobile coverage/fake-device results are historical, and full Arabic/English localization remains U3-owned. No mobile edits or fresh mobile tests were claimed. Parent owns independent review/gates. The local backend repair is review-ready; U1 is not a verified deployed skeleton or authorized release.

## Current approved-plan continuation — 2026-11-16

**Result: partial implementation ready locally; Code Generation/U1 is not complete. Both real local synthesis commands fail cdk-nag. No deployment, asset upload, live migration, paid provisioning, DNS registration or external message was performed.** The evidence in this section supersedes older "fresh/current" labels below; those sections are retained as historical implementation/recovery evidence.

### Current source and implemented change

The checkouts remain on Raad `aidlc/u1-money-service` at `793f2efa53814fa7a19fbc153a8c6431752e6697`, service `aidlc/u1-contract-handoff` at `087487dddbb3515fd0b5967e11b1a58aa21a34c5`, and observed mobile `8ce7db67187cbaf0e2be91334af4f9cce44a26df`. The recorded sibling registrations still resolve to `../money-service` and `../mobile`. Existing edits were retained. No mobile source was edited or mobile test rerun in this continuation; earlier 106-test/95.11% mobile and fake-device evidence is historical, not a current dev acceptance result.

- `infrastructure/app.py` now requires only alert configuration and a Cognito prefix for default dev preparation. Domain, hosted-zone ID and certificate form an optional all-or-none triple. Partial triples and custom viewer certificates outside us-east-1 are rejected.
- `infrastructure/raad_platform/stacks.py` now creates the same WAF-protected, origin-secret-checked, uncached API distribution and seven-field real-time transfer telemetry when custom-domain inputs are empty. Default mode creates no Route 53 records or custom certificate. Custom mode retains aliases, its us-east-1 certificate and DNS records. Default mode is rejected outside dev.
- The actual selected public root is published through `/raad/<environment>/public-api-url` SSM and `PublicApiUrlOutput`. Default mode uses the distribution's generated DomainName token; custom mode uses the configured domain. These are future generated outputs, not an existing RAAD endpoint. Smoke setup must set `MONEY_API_BASE_URL` and Engineer 2 must generate C4 using the actual output after an independently authorized successful deployment.
- `.github/workflows/ci.yml` now exercises default dev synthesis using explicitly synthetic account/email/prefix inputs, without a fictitious custom certificate/domain requirement. The `.env.example` and this work's `infrastructure/README.md` explain the two modes and their limits. Root `README.md`, `AGENTS.md` and `.gitignore` were preserved.
- Real native bundling revealed that host-default Docker output contained aarch64 wheels while Lambda previously defaulted to x86_64. Platform edge/telemetry and service functions now explicitly use ARM64; edge/service Docker bundling explicitly selects linux/arm64. The fresh package output uses aarch64 cryptography wheels; `file` confirms the `_rust.abi3.so` assets in both repos are ARM aarch64 ELF. This proves architecture matching, not deployed runtime behavior.
- Regression assertions cover default mode, complete custom mode, six rejected partial triples, certificate-region validation, dev-only default use, generated/public URL publication, preserved WAF/origin headers/realtime logging and declared ARM64 functions. Existing R-06 GetUser and R-07 direct-origin fixes were preserved.

### Explicit plan/design incompatibility

The approved plan selects the AWS-assigned CloudFront hostname plus an optional all-or-none domain/Route53/certificate triple. The latest isolated infrastructure design instead describes controlled free external DNS plus custom ACM without Route 53. This continuation implements the approved reversible local mode and does not silently rewrite that plan into the newer design. The external-DNS path still needs a plan revision and controlled actual hostname/certificate inputs; no hostname is owned or issued here.

NFR2.1 is still TLS>=1.2. AWS fixes a default CloudFront certificate's viewer security policy at TLSv1 regardless of a supplied minimum; local synth confirms the resulting CFR4 failure. The default mode is therefore **incompatible with release acceptance**, not a waiver or proof of compliance. `traceability.json` now records NFR2.1 as GAP. See [AWS ViewerCertificate behavior](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-cloudfront-distribution-viewercertificate.html).

### Commands and measured evidence

Working directories are `infrastructure/` for platform and registered `../money-service/` for service. Python3.12.4/pytest9.2.0 remain pinned; local jsii warns about Node26.12.1, while workflows select Node22. No warning or quality floor was hidden.

| Command | Actual result |
|---|---|
| Platform `uv run pytest --cov=raad_platform --cov=../scripts --cov-report=term-missing` before source changes | 126 passed; 85.59% combined coverage; exit0. |
| Exact eight-file service U1 unit command from unit-test-instructions.md before source changes | 130 passed; 89.29%; exit0. |
| Final platform coverage command above | **138 passed; 86.00%; exit0.** An intermediate new default-certificate assertion failed because CDK omitted ViewerCertificate; explicit default-certificate configuration fixed it before this run. |
| Final exact eight-file service U1 unit command | **131 passed; 89.29%; exit0**, including new ARM64 assertion. |
| Service `uv run pytest tests/unit tests/integration` | 152 passed including22 real DynamoDB Local integration cases; 90.57%; exit0. This ran before the final architecture-only assertion/property change. No money logic changed afterward. Disposable local container was stopped. |
| Exact Ledger scoped JSON coverage command from instructions; then independent checker | 25 passed; 100% line and100% branch; both exit0. Original TDD Red/Green evidence is retained below; no money-core rules changed in this continuation. |
| Platform Ruff check/format commands covering raad_platform/tests/app.py/../scripts; strict mypy on raad_platform/app.py/../scripts | All exit0;18 formatted Python files;9 source files type-checked. |
| Service Ruff check/format on src/tests/scripts; strict mypy src | All exit0;25 formatted Python files;6 source files type-checked. |
| Real platform and service local synths below | Native packaging succeeds for explicit ARM64 target; **both synthesis commands exit1 on security findings**, listed below. No publish or deployment command ran. |

Exact synthetic-fixture synthesis invocations, each as a separate command in its owning repo:

```bash
RAAD_ALERT_EMAIL=synthetic-build@example.test RAAD_COGNITO_DOMAIN_PREFIX=raad-synthetic-build-example-test CDK_DEFAULT_REGION=us-east-1 CDK_DEFAULT_ACCOUNT=111111111111 uv run cdk synth --all
RAAD_EDGE_ROLE_ARN=arn:aws:iam::111111111111:role/raad-build-edge RAAD_CORRELATION_SECRET_ARN=arn:aws:secretsmanager:us-east-1:111111111111:secret:raad/dev/correlation-hmac-build CDK_DEFAULT_REGION=us-east-1 CDK_DEFAULT_ACCOUNT=111111111111 uv run cdk synth --all
```

The first cache-denied platform invocation was retried with actual sandbox authorization. The installed CDK prints that `--all` is ignored and continues synthesis. The public build image is now present at digest `sha256:28c6fdd016bb4922d8f89f5e6dc477a31c80e3999cce2222ea22c602930a30f3`; older expired-ECR statements below are historical. Neither synthetic account nor email/prefix/ARN is a real runtime configuration claim.

### Unsuppressed synthesis/security blockers

Platform errors: COG8 (Cognito is not Plus), SMG4 (no automatic correlation/origin secret rotation), SNS3 (publish TLS enforcement), L1 (pinnedPython3.12 is not latest), IAM4 (LambdaBasicExecutionRole on edge/processor), IAM5 (processor wildcard metric/query resources and scheduler qualified-function wildcard), CFR3 (standard CloudFront access logging absent), CFR4 (default certificate allowsTLSv1), APIG1 (HTTP API access logs absent), APIG4 (authorization resides in edge code, not route authorizer annotations). Service errors: L1 and IAM4 on MoneyApi. These are actual failing checks, not accepted exceptions. No suppression or threshold reduction was added.

Warnings include Cognito MFA/geo restrictions, dev PITR disabled, existing addAlias/PITR API deprecations, cross-stack-reference default and the ignored default-certificate minimum. Some findings overlap deliberate design choices (safe-field logging, independent edge authorization, pinned runtime, coordinated secret rotation); they still require a concrete audited design/implementation resolution before a passing synth. No paid Cognito tier was enabled to clear COG8.

**CI architecture gap:** the existing GitHub workflows select x86 `ubuntu-latest` and do not explicitly configure QEMU or native ARM execution. Local ARM64 packaging on this Apple Silicon host does not prove those CI jobs can run linux/arm64 containers. Before claiming CI-ready packaging, use an explicitly ARM-capable runner/emulation setup, or coordinate Lambda and bundle back to explicit x86_64/linux/amd64. No implicit QEMU availability, GitHub run success or new tooling installation is claimed here. This remains an open Step11 release check.

### Remaining work and source accounting

Steps1,3,4,8 and13 are reconciled/ticked from actual implementation and current local evidence; approved plan wording is unchanged. Steps2,5,6,7,9,10,11 and12 remain open where complete capability, handoff/deployment or integration proof is missing. In particular Step12 is untouched: no live100-user/10-active-user load, p95 acceptance, public delay proof, alarm delivery, actual Cognito/identity checks, migration/cutover or real dev API/iOS/Android verification exists. P7 old-code invalidation remains unverified; no unsupported pre-confirmation fallback was invented. No new opening credit behavior was changed: 100000halalas once for new wallets in each environment remains the existing implementation.

All changed application/config paths are retained in the62-path manifest: `.github/workflows/ci.yml`, `infrastructure/{app.py,.env.example,README.md,raad_platform/stacks.py,tests/test_public_edge_stack.py}`, and service `src/raad_money/infrastructure.py`, `tests/unit/test_service_stack.py`. No new source path was introduced; earlier claims remain. Generated cdk.out assets/coverage/runtime caches are local build evidence, not application-source additions or published assets.

Co-engineer handoff remains C1 local partial release1.0.0-u1.2 versus published baseline5dd760d; regenerate/reconcile the owned mobile client only in Engineer2's track. Use the actual public URL/pool/client outputs for C4, with no placeholder dev file. Operational alert destination jjii0@hotmail.com is supplied through deployment settings; no actual subscription/delivery is claimed. The separate public contact is later U5 work. Parent owns review and failure/repair routing; this continuation does not settle U1 as complete.

## Current revision and ownership

This is current local implementation evidence for the approved Transactions/public-latency revision. U1 and its deployed walking skeleton remain incomplete. On this continuation, the source revisions are Raad `793f2efa53814fa7a19fbc153a8c6431752e6697`, RaadMoneyService `087487dddbb3515fd0b5967e11b1a58aa21a34c5` and the observed mobile input `8ce7db67187cbaf0e2be91334af4f9cce44a26df`. These revisions identify the tested checkouts, not PR, push or release evidence. The workflow parity changes and host mobile runner remain local changes. Engineer 2 retains all mobile source, generated-client and device-test ownership; no mobile source was edited in this continuation. Earlier start-guide and contract-publication statements below are historical context.

The source manifest retains all earlier claims and includes the telemetry driver, mobile dev runner and their offline tests, for 62 paths total. Runtime caches, coverage databases, failed cdk.out bundles and deleted scratch patches are not application source and are not release artifacts. Existing root README.md, AGENTS.md and .gitignore were preserved. Mobile co-engineer sources are observed integration inputs, not changes authored by this agent.

## Implemented changes

### Review R-06 / R-07 correction

- **R-06 selected remedy:** the provider own-profile adapter now uses Cognito `GetUser`, authorized with the caller's SDK-issued access token, instead of OAuth `userInfo`. The published C5 `user-profile-endpoint` URI is the pinned regional Cognito API root. The verifier independently validates the RS256 JWT, issuer, client, expiry, token type and subject before the call; requires the exact `aws.cognito.signin.user.admin` scope; then checks the returned subject, verified email and nonempty name. The SDK client is unsigned (this operation is authorized by the caller token, not IAM), restricted to the issuer's regional endpoint, reused, and bounded to one attempt with 0.25-second connect and 0.75-second read timeouts. No service IAM grant or mobile source change was added.
- This is an explicit correction to Infrastructure Design's earlier PKCE/userInfo selection, authorized by the request to repair R-06 using its offered own-profile remedy. The actual mobile SDK SRP and fixture ADMIN_USER_PASSWORD_AUTH paths are preserved. The historical design documents are preserved as decision history; they must not be read as evidence that PKCE/userInfo has been implemented. OAuth-only tokens without the SDK scope now fail safely; a future OAuth migration must coordinate its scopes/profile adapter.
- Regression evidence uses locally RSA-signed tokens with the documented SDK scope, actual JWT verification, and botocore's real GetUser request/response model through Stubber. This checks the adapter's provider-wire semantics without pretending Cognito minted these local tokens. Actual P1/P2/P13 provider capability, public PUT/GET, device sign-in and production behavior remain unverified.
- **R-07 selected remedy:** a distinct per-environment 64-character Secrets Manager origin credential is added by CloudFront on every configured API origin. CloudFront overwrites a viewer-supplied `X-Raad-Origin`. The edge retrieves only this secret using scoped read access and compares it in constant time before bearer authentication, forwarding, dev fault injection and public SLI publication. Missing/wrong origin credentials return safe C1 `403 FORBIDDEN`; unavailable/malformed configuration returns safe `503 SERVICE_UNAVAILABLE`. Denials emit no header, event, secret, personal fields or public transfer samples. The credential is not forwarded to MoneyApi. The default execute-api hostname remains reachable for CloudFront, but its money handler rejects bypass calls.
- The CloudFront template uses a deployment-resolved Secrets Manager dynamic reference; the Lambda receives only the ARN. Secret material is visible to principals allowed to read the deployed CloudFront origin configuration, so that permission is part of the trusted infrastructure boundary. No automatic rotation is claimed. Rotation must coordinate the distribution's secret version/property update and the edge's expected secret; allow the finite 60-second runtime cache to expire and verify both paths. A mismatched rollout fails closed rather than allowing bypass. Updating a secret alone does not refresh CloudFront's resolved header. Rotate after suspected disclosure and rerun the security checks.
- Added 11 platform regressions and 8 service regressions. Before source changes the platform baseline was 115 passed/85.04%. The affected service baseline had 55 passing assertions but exited 1 at 58.77% because it measured only three files against whole-package coverage; no threshold changed. After the correction, the full platform command passed **126 tests / 85.59%** and the exact eight-file U1 service unit command passed **130 tests / 89.29%**. These supersede earlier counts for the modified source, not the historical assembled integration result below.
- Current static checks passed: platform `uv run ruff check raad_platform tests app.py ../scripts`, `uv run ruff format --check raad_platform tests app.py ../scripts` (18 files), `uv run mypy raad_platform app.py ../scripts` (9 source files); service `uv run ruff check src tests scripts`, `uv run ruff format --check src tests scripts` (25 files), `uv run mypy src` (6 source files). Formatting only followed the passing regression runs. No backend money-rule arithmetic changed, so its prior Ledger evidence is retained as historical.
- All six corrected application/test paths already exist in the retained source manifest: platform `raad_platform/{stacks.py,edge/handler.py}`, `tests/{test_edge_adapter.py,test_public_edge_stack.py}` and service `src/raad_money/identity.py`, `tests/unit/test_identity.py`. No claim was dropped, no plan checkbox was advanced and no mobile file was edited.

#### Deployed security and identity verification still required

Before release, obtain the actual generated HTTP API endpoint from the deployed MoneyHttpApi resource and set `RAAD_ORIGIN_API_URL` to it; use the configured public root in `MONEY_API_BASE_URL`. With no bearer token, perform these read-only probes separately and capture only status/safe results:

```bash
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' "$RAAD_ORIGIN_API_URL/money/v1/wallet"
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' -H 'X-Raad-Origin: deliberately-invalid' "$RAAD_ORIGIN_API_URL/money/v1/wallet"
curl --silent --show-error --output /dev/null --write-out '%{http_code}\n' -H 'X-Raad-Origin: deliberately-invalid' "$MONEY_API_BASE_URL/money/v1/wallet"
```

The two origin calls must return 403. The public call must return 401 (CloudFront replaced the counterfeit header and bearer authentication was reached), not 403/503. No command supplies the real origin credential. Then run the approved fixture/setup and public API smoke with an actual SDK-authenticated token to prove wallet PUT/GET and the verified profile; run both device journeys through `scripts/verify-dev.sh`. Preserve the direct-origin rejection evidence separately from CloudFront latency samples. These probes and actual-provider tests were **not run** here because the deployed configuration and devices remain unavailable. Real bundling/cdk-nag, origin/header delivery, CloudFront overwrite semantics, secret deployment/rotation and live capabilities remain release gaps.

Provider references: [GetUser authorization and attributes](https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_GetUser.html), [OAuth userInfo token requirements](https://docs.aws.amazon.com/cognito/latest/developerguide/userinfo-endpoint.html), [CloudFront custom-header overwrite and origin restriction](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/add-origin-custom-headers.html).

### Earlier implementation

- Money service provisions Ledger, Transactions and WalletDirectory. The frozen CompletedTransfer model serializes one immutable canonical row keyed by transferId, containing both wallet references, integer halalas, currency SAR, reference and UTC completion.
- A single five-action transaction updates both guarded wallet balances, inserts the canonical row conditionally and inserts two reference-only history entries. The old resource-client double serialization was removed; real DynamoDB Local now exercises native resource values successfully.
- History strongly queries a bounded page plus one lookahead, strongly batch-reads canonical rows, restores query order and checks ownership/order. Missing/corrupt canonical rows or exhausted unprocessed-key reads fail the page safely. U1 reports hasMore/X-U1-History-Truncated without inventing supported cursor navigation.
- The additive migration validates paired legacy payloads, refuses mismatches/unmatched rows, conditionally commits canonical plus reference conversion, reruns safely and verifies balances/history. It defaults to dry-run. No deployed migration was run.
- Canonical activation fails closed: CDK defaults ActivateCanonicalWriter to false; the service returns safe unavailable responses while disabled. Deployment expands with requests disabled, runs the no-write --check-ready count/reference gate, and activates only on success. Failed readiness leaves requests disabled for explicit engineer migration; a legacy payload-only rollback is incompatible.
- C1 errors are top-level code/message/correlationId. PUT creates/reads the wallet before repairing the directory; GET does not create. Internal wallet/holder IDs are removed from public shapes. The partial U1 artifact explicitly disclaims saved replay and uncertain resubmission; no business outcome record or false replay header is added.
- The edge signs an outer Function URL envelope containing the original method/path/query/body and allowlisted bearer/key headers. MoneyApi restores it only from an IAM-authorized event and independently verifies the original token. The outer SigV4 Authorization no longer overwrites the bearer.
- Verifiers reuse pinned PyJWT 2.15.1 clients with a 360-minute set cache, disabled indefinite per-key cache, one-second fetch and sixty-second unknown-key cooldown. This installed release implements locked/monotonic discovery and rejects redirects. The service validates C5's closed configuration/environment. Its earlier userInfo implementation is superseded by the GetUser correction above. Invalid tokens and discovery unavailability receive distinct safe responses.
- CloudFront transfers behavior has caching disabled and 100% real-time sampling of exactly seven safe fields. Platform telemetry uses an encrypted Kinesis stream, isolated processor, fourteen-day sample logs and a five-minute schedule with two-minute grace. The processor deduplicates native IDs, bounds queries, computes event-window counts/slow fractions/p95 and requires eligible consecutive breach/recovery windows. Incomplete/conflicting telemetry cannot emit a healthy pair. Metrics use Maximum gauges; handler timing is labelled diagnostic.
- Pure acceptance reconciliation requires one-to-one native response/log matches, retains failures and computes combined/sustained nearest-rank p95. This is not an executed load/instrumentation proof.
- Setup tooling creates separate fresh API/iOS/Android fixture pairs through Cognito and PUT, refuses identity collisions/reused opening balances, and stores runtime credentials only in the existing Secrets Manager fixture secret. After setup and API smoke, the wrapper invokes scripts/run_mobile_dev.py with setup's nonsecret run ID. The runner validates C4 against the runtime pool/client/API outputs, reads the secret with bounded SDK configuration, checks all six accounts are distinct and phase/run-tagged, and runs iOS then Android with explicit RAAD_E2E_TARGET=dev. Each phase's temporary JSON uses mode 0600 inside a 0700 directory and is cleaned on normal completion or exceptions. Flutter output is suppressed to avoid printing account details; only safe phase status appears. The implementation is covered offline; the integrated device run remains unverified. Forced process termination can leave private files or Flutter build artifacts for host cleanup, so these remain test-only accounts.
- CI/deploy definitions retain independent repo checks, assembled service coverage and an independent Ledger coverage checker. Missing typing stubs were added. Ruff formatting/import fixes stayed within the approved source/tests. Pytest 8.4.2's reported PYSEC-2026-1845 finding was fixed by updating the dev constraint and both locks to pytest 9.2.0.
- CI parity correction in this continuation: both platform workflows now run the test-instruction coverage command including `../scripts`, and both Ruff checks and strict mypy include `app.py` and the host scripts. The dev workflow path filter includes `scripts/**`, so changing the verification runner triggers the same checks. No coverage threshold was lowered. Both workflow paths were already claimed in the retained source manifest.

## Verification performed

Runtime: Python 3.12.4, pytest 9.2.0, pytest-cov 6.3.0, Hypothesis 6.170.15; DynamoDB Local image 2.5.2 on Docker 29.0.1. Local jsii warns that Node 26.12.1 is untested; pipeline definitions select Node 22. No warning was hidden as a fix.

| Check | Recorded result and evidence age |
|---|---|
| Platform full command: uv run pytest | Fresh continuation: 100 passed, including 40 offline driver cases; combined coverage 84.60%; configured 80% floor passed. |
| Platform and host runner: uv run pytest --cov=raad_platform --cov=../scripts --cov-report=term-missing | 2026-11-15: 115 passed, including 15 new offline mobile-runner cases; combined coverage 85.04%, runner combined coverage 88%; configured 80% floor passed. Initial new-test failures were a test assertion matching the macOS /private path, corrected before this passing run. |
| Host runner Ruff, strict mypy and wrapper bash -n | Passed on 2026-11-15; no AWS or device invocation occurred. |
| Platform earlier six-file command | Historical 60 passed/88.84% before driver source was added. On the later source tree its 60 assertions still passed but coverage failed at 53.39%; this is not a current passing full-suite result. |
| Service exact U1 unit command from unit-test-instructions.md | Fresh continuation: 122 passed; combined coverage 89.62%; configured 80% floor passed. No service source was changed. |
| Service assembled command: uv run pytest tests/unit tests/integration | Fresh continuation: 144 passed, including 22 real local-store/boundary cases; combined coverage 90.94%; 524 statements/38 missed. The existing disposable DynamoDB Local container was started for this run and stopped afterward; no deployed table was touched. |
| Ledger exact scoped JSON command from unit-test-instructions.md | Historical: 25 passed; 56/56 statements and 16/16 branches covered; report artifacts/coverage/u1-ledger.json. Not rerun in this continuation. |
| uv run python scripts/check_ledger_coverage.py artifacts/coverage/u1-ledger.json | Exit 0: line=100.00%, branch=100.00%; floors independently enforced. |
| Platform uv run ruff check raad_platform tests app.py ../scripts; uv run ruff format --check raad_platform tests app.py ../scripts | Fresh continuation: passed; all 18 checked Python files formatted. These are the corrected commands in both platform workflows. |
| Service Ruff check and format --check | Passed; all 26 checked Python files formatted. |
| uv run mypy raad_platform app.py ../scripts; uv run mypy src | Fresh platform: passed, nine source files. Historical service: passed, six source files; not rerun here. Strict configuration retained. |
| uv run pip-audit, each repo after pytest update | Both exit 0, no known vulnerabilities. The local service package has no PyPI entry and is not a third-party audit target. Cache-deserialization warnings were advisory. |
| bash -n scripts/verify-dev.sh | Exit 0. |
| scripts/verify-dev.sh | Exit 1 at preflight: RAAD_IOS_DEVICE_ID missing. No fixture/account mutation or API/mobile journey ran. |
| Real cdk synth --all with explicit nonsecret build fixture inputs, each repo | Both failed while bundling: public.ecr.aws/sam/build-python3.12 authorization token expired. cdk-nag completion and deployable packaging are unverified. |
| docker pull public.ecr.aws/sam/build-python3.12 | Fresh continuation: default and escalated invocations both fail with the expired-token response. The image is absent locally; no global Docker credentials were changed and no alternate package path was substituted. The earlier synth failure remains unresolved. |
| git diff --check -- .github/workflows/ci.yml .github/workflows/deploy-dev.yml | Passed for the current implementation changes. Repository-wide diff check also reports existing trailing whitespace in two tool-owned audit messages; those audit records were preserved. |

Initial unchanged-tree baselines, before application edits, were platform 30 passed/89.95% and service 81 unit tests passed/93.20% on pytest 8.4.2. Parent recorded TDD Red for CompletedTransfer as an ImportError in the exact Ledger command before core implementation. The first Green had 18 passing tests but insufficient new branch coverage; added validation cases produced the final 25 passing/100% independent floors above.

Two intermediate failures were repaired, not suppressed: integration fixtures lacked the test correlation-secret ARN, and assembling unit/integration directories exposed duplicate module basenames. The fixture now supplies local-only configuration, and pytest importlib mode permits both directories without weakening coverage. An intermediate integration-only run passed all assertions but exited on whole-package coverage; the final assembled run above passed that floor. Earlier concurrent coverage output was discarded and the final Ledger report/checker ran sequentially after the assembled suite.

Both synths used build fixtures (account 111111111111/example.test), not asserted live deployment values. A documented anonymous public pull was attempted with an isolated empty Docker config and the existing daemon socket, then explicit --config/--host flags; both still returned the expired-token error. Global Docker credentials were untouched and the scratch config was removed. Inline-asset CDK assertion tests are not a substitute for successful real bundling/nag. No CDK deployment or production write occurred. The disposable local DynamoDB container was stopped afterward.

## Incomplete plan steps and release blockers

Only plan steps 1, 3, 4, 8 and 13 are marked complete. Mixed/mobile/deployed steps 2, 5, 6, 7, 9, 10, 11 and 12 remain unchecked; source and local proof completed within them do not establish their full acceptance.

- Mobile now has the Flutter iOS/Android skeleton, generated client, unit/widget/contract tests, tool/check_coverage.dart, example C4 config and integration_test/walking_skeleton_test.dart on aidlc/u1-mobile-skeleton at 8ce7db6 (skeleton commit 3c563cb). It pins published C1 baseline 5dd760d, not the newer local contract. Mobile tests did not start in this continuation: Flutter SDK cache writes were denied by the sandbox; offline dependency resolution also lacked yaml ^3.1.4. Real dev configuration, simulator/emulator evidence and temporary fixture-file export/cleanup remain outstanding.
- Prior authorized account evidence identified 027863026273/us-east-1 and no suitable RAAD hosted zone/certificate/deploy role. Those historical observations were not reasserted as a fresh account inventory. Real public domain, zone/certificate, alert destination, RAAD-scoped deployment access, deployed pools/client/verifier/secret outputs and ready fresh fixture credentials remain provisioning inputs.
- Real Lambda bundling and cdk-nag must pass after the public-image access failure is resolved. GitHub Actions workflows were authored, not executed; no PR checks, reviewer approval, merge or deployment success is claimed.
- C3 P1/P2/P13, deployed configuration/identity isolation, full dependency-deadline fault behavior, protected logging/rotation investigation and all three dev journeys remain unproven. Local unit tests do not establish these live capabilities.
- Deployed legacy-schema inspection, controlled migration/activation/rollback and cost estimate are not executed. The disabled-writer/readiness gate is implemented and tested locally; it is not a completed cutover.
- No deployed initialization/origin-delay proof, alarm email delivery, telemetry-loss exercise, 100-user/10-active-user ten-minute load run, complete response/log reconciliation or accepted p95 result exists. The load/fault driver now has 40 passing offline tests; its deployed wiring and live execution remain unverified.
- Secret scanning was not independently executed in this revision; the authored Gitleaks CI step is not a passed scan.

Traceability was regenerated from current upstream IDs. Blocked/unbuilt work is GAP, not a human-approved deferral. Backend implementation/test evidence in the registered money-service@checkout is described explicitly; the current traceability validator only permits OK targets inside this project's directory and rejects sibling/checkout-alias targets. The manifest and this summary retain that evidence without fabricating local proxy source. Parent owns independent review and lifecycle settlement.

## Historical handoff context

Earlier commits 16129da (mobile handoff), 5dd760d (published C1 baseline) and 8a0d108 (shared split) remain historical handoff references. The earlier local API setup failure and two-table implementation are superseded by this revision's passing real-store suite and three-table design; earlier deployed/mobile completion was never claimed.
