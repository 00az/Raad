# Code Generation Summary — U1 Walking Skeleton

## What was built

- `Raad` now has the CDK platform application and identity, monitoring, and public-edge stacks; the edge adapter verifies Cognito access tokens, protects correlation IDs, and signs calls to the MoneyApi Function URL. It also has CI/deploy workflows, a dev verification wrapper, and account-specific local setup notes.
- `RaadMoneyService` now has the pinned C1 OpenAPI contract, Python/CDK service skeleton, integer-halalas Ledger rules, DynamoDB Ledger and WalletDirectory repositories, token verification, C1 API handlers, local DynamoDB integration tests, test-user setup, smoke script, and CI/deploy workflows.
- `RaadMobile` remains Engineer 2's workstream. The co-engineer handoff is on branch `aidlc/u1-mobile-handoff` (latest commit `16129da`). The C1 contract is on `RaadMoneyService` branch `aidlc/u1-contract-handoff` (commit `5dd760d`). The approved U1 split and test instructions are shared on `Raad` branch `aidlc/u1-coengineer-handoff` (commit `8a0d108`).

## AWS account configuration

The authorized AWS session identified account `027863026273` and region `us-east-1`. These non-secret values are recorded in `infrastructure/.env.example`. No credentials or tokens were written to the repository. The account has no Route 53 hosted zones or ACM certificates in `us-east-1`; its existing GitHub Actions role is scoped to a different repository and is not suitable for RAAD. The public domain, hosted-zone ID, certificate ARN, alert email, and a RAAD-scoped deploy role still need to be supplied or provisioned. No AWS resources were deployed.

## Verification

- Raad platform: **30 passed**, **89.95%** coverage (above the 80% floor).
- MoneyService unit suite: **81 passed**, **93.20%** coverage (above the 80% floor).
- MoneyService Ledger rules: **12 passed**, **100%** line and branch coverage (above the 95% floor).
- MoneyService local integration checks are **not complete**. In the corrected C1-only run, two cases passed and `test_c1_put_wallet_returns_201_then_200` returned 503 during wallet setup. The rest of the integration suite was not verified. The disposable DynamoDB Local container is running; stop it after resolving and rerunning those checks.
- `scripts/verify-dev.sh`, CDK deployment, and Flutter integration checks were not run. The dev domain, hosted zone, certificate, deploy role, test users, and mobile app are not ready. The approved verification command requires all three repos deployed to dev.
- Flutter 3.47.2 (Dart 3.13.2) is installed on this Mac. No mobile app tests have been run because the co-engineer's app implementation has not arrived.

## Remaining U1 work

Engineer 2 can start the mobile half against a contract fake server now that the OpenAPI contract and split are on remote branches. The backend/platform side still needs the failing local integration case repaired and the dev prerequisites above before the full walking skeleton is verified. Do not claim U1 or the walking skeleton complete until the mobile screens, widget/integration tests, and end-to-end dev verification are complete.
