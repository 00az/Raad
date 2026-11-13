# RAAD platform infrastructure

## Confirmed AWS account

The authorized AWS CLI session reported account `027863026273` in `us-east-1` on 2026-11-13. The account ID and region are safe configuration values; credentials are short-lived and must never be copied into this repository.

The account currently has no Route 53 hosted zones and no ACM certificates in `us-east-1`. The existing `GitHubActionsRole` trusts only `00az/hr-leave-portal` and has no attached managed policies, so it is not suitable for Raad deployments. No RAAD-specific deploy role was found. The account's existing Cognito pool belongs to another application and is not used by this stack.

## Local configuration

Copy `.env.example` to `.env.local`, then provide a domain, hosted-zone ID, us-east-1 ACM certificate ARN, alert email, and an available Cognito domain prefix before deploying. Do not put AWS credentials in either file. Authenticate with the approved AWS CLI login or use a least-privilege role; do not deploy as the root user.

The example records the account and region confirmed above. The remaining values are deliberately blank because they do not exist in the account or require your choice. The public edge stack refuses to synthesize until those inputs are set.

## CI deployment setup

Create a GitHub OIDC role scoped to repository `00az/Raad` and the `dev` environment, grant only the deployment permissions required by these CDK stacks, and set `AWS_ROLE_ARN_DEV` in the GitHub `dev` environment. Set `AWS_REGION=us-east-1` and the matching `RAAD_*` GitHub environment variables from `.env.local`. The deploy workflow assumes that role; it does not use a long-lived access key.
