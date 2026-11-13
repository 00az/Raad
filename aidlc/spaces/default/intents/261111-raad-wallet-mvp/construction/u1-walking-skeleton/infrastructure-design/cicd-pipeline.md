# CI/CD Pipeline — U1 Walking Skeleton

Conversation language: English.

## Pipeline Stages

Each repository keeps an independent GitHub Actions pipeline. Pull requests are required for every change; CI runs the same checks locally and in GitHub Actions. Each workflow authenticates to AWS through GitHub OIDC and a short-lived, environment-scoped role. No static AWS keys or test credentials are stored in repository secrets.

1. **Source and contract check** — check out the repository, validate the pinned contract files and SHA-256 entries, and fail if the generated-client pin is stale.
2. **Lint and type checks** — Python repos run Ruff and strict mypy; the Flutter repo runs `dart format --set-exit-if-changed` and `flutter analyze` with the affirmed lint rules.
3. **Build and unit tests** — install from committed lockfiles; Python uses the supported pinned runtime, `uv`, pytest and Hypothesis; Flutter uses `flutter test`. Enforce 80% line coverage in each backend/mobile repo and 95% line and branch coverage for the Ledger money core. Ledger rule changes follow the affirmed test-first order.
4. **Security and dependency checks** — run secret scanning, dependency audit and the repository's existing security checks. Fail on high/critical findings; never print test credentials, request bodies or unfiltered SDK exceptions.
5. **Infrastructure synthesis and assertions** — in `Raad`, synthesize Python CDK, run CDK security checks and assert TLS, WAF association, no authenticated-route caching, log retention, encrypted resources, scoped IAM and environment separation. In `RaadMoneyService`, assert table encryption, conditional/transactional access, bounded Lambda concurrency, deadlines and no transfer-write retry. Do not deploy from an unreviewed pull request.
6. **Contract and integration tests** — validate request and response shapes against the pinned C1 OpenAPI file; exercise edge forwarding, spoofed identity-header removal, correlation behavior, safe error mapping and the independent MoneyApi verifier. Run local-store transaction, conditional uniqueness, conservation and concurrency checks against the selected real local DynamoDB container. Mock-only success is not transaction evidence.
7. **Merge and dev deployment** — after all checks pass and the other engineer approves, squash-merge to `main`. Deploy the shared `Raad` resources first, then `RaadMoneyService`, then publish the environment configuration consumed by `RaadMobile`. If the MoneyApi integration is not ready, the public route returns a safe unavailable response. A successful infrastructure deployment alone does not mean the end-to-end skeleton works.
8. **Dev verification** — prepare users and wallets through supported setup, confirm readiness, then run `scripts/verify-dev.sh` against the real dev sign-in, API and store. Run the separate accepted performance check with 100 registered users, 10 active users, at least 200 valid funded transfers and the full cold-plus-sustained sample population. Capture safe outputs and all three repo commit IDs.
9. **Staging and production promotion** — use the same CDK definitions with isolated configuration. Promote dev-verified commits through stg, then prd, without environment branches. Production remains behind a manual approval; validate production retention, availability measurement, backup/recovery and security requirements before first release. These environments are outside this U1 dev provisioning run.

## Stage-to-Gate Map

| Stage | Gate |
|---|---|
| Pull request validation | All applicable lint, type, build, test, coverage, security, contract and CDK checks pass; second engineer approves. |
| Dev deployment | Short-lived OIDC role and required environment parameters are present; deploy shared platform, then MoneyApi; fail closed on missing issuer/audience/secret configuration. |
| Dev smoke and skeleton verification | `scripts/verify-dev.sh` passes against the real dev path; both users are initialized through C1; setup readiness, balance, one transfer and history are verified. |
| Performance acceptance | Both combined idle-start/sustained and sustained p95 are at most 2,000 ms; every valid funded transfer succeeds; safe sample counts and achieved concurrency are recorded. |
| Staging promotion | Dev evidence is attached to the release; stg configuration is environment-isolated and its smoke check passes. |
| Production promotion | Explicit human approval; production NFR, security, retention, backup and rollback readiness evidence is reviewed. |

## Deployment, Rollback and Secrets

For dev, publish immutable Lambda versions and move the live alias after deployment smoke checks. For a production application release, use a small canary shift through the alias before full traffic; retain the prior version for rollback. Keep API and data changes backward compatible using expand/contract steps. Roll back the affected repository to its prior known-good commit and rerun the dev smoke check. Redeploying code does not restore lost data; disposable dev may be rebuilt only by an explicit engineer decision and must recreate fixtures through supported setup.

GitHub OIDC roles are separate by repository and environment, restricted to the repository/ref and required actions. The dev deploy role may update only dev stacks. Runtime roles read only their own table and approved environment configuration; the edge and MoneyApi each have read-only access to the shared current/previous correlation HMAC secret. Test-user passwords are fetched from Secrets Manager at execution time and are not passed as command-line arguments or printed in CI output. Notification email, hostnames, issuer, audience and client IDs are deployment inputs, not checked-in constants. Keep credentials and personal attributes out of workflow artifacts and alarm text.

No pipeline result, deployed resource, load result or alarm delivery is claimed by this design. Build and Test records actual evidence after implementation.

## Sources

- `construction/u1-walking-skeleton/nfr-requirements/tech-stack-decisions.md`: languages, tools, repos, coverage and deployment practices.
- `construction/u1-walking-skeleton/nfr-design/performance-design.md`, `security-design.md`, `scalability-design.md`, `reliability-design.md` and `observability-design.md`: concrete checks and operating limits.
- `inception/contract-design/contract-summary.md`: pinned C1 contract and cross-repository release controls.
- `aidlc/spaces/default/memory/team.md`: pull request, branch, deploy and review practices.
