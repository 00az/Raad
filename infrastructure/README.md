# RAAD platform infrastructure

## Confirmed AWS account

The authorized AWS CLI session reported account `027863026273` in `us-east-1` on 2026-11-13. The account ID and region are safe configuration values; credentials are short-lived and must never be copied into this repository.

The account currently has no Route 53 hosted zones and no ACM certificates in `us-east-1`. The existing `GitHubActionsRole` trusts only `00az/hr-leave-portal` and has no attached managed policies, so it is not suitable for Raad deployments. No RAAD-specific deploy role was found. The account's existing Cognito pool belongs to another application and is not used by this stack.

## Local configuration

Copy `.env.example` to `.env.local`, then supply a controlled hostname and us-east-1 viewer certificate together, the alert email and an available Cognito domain prefix. Leave hosted-zone ID blank for external DNS; an optional existing Route53 zone creates aliases without creating a hosted zone. Partial domain/certificate input is rejected. Do not put credentials in either file.

The CloudFront default certificate has a provider-fixed TLSv1 policy and cannot enforce the approved TLS>=1.2 requirement, so it is refused. Both DNS modes require the custom certificate with TLS1.2_2021, WAF, the origin credential, disabled authenticated-route caching and seven-field transfer telemetry. Actual free-hostname control and certificate issuance are deferred; local fixtures establish neither.

After an independently authorized deployment, read the actual `/raad/dev/public-api-url` SSM parameter or `PublicApiUrlOutput` stack output for smoke runners and mobile C4 configuration. With external DNS, retain the ACM validation CNAME and point the controlled hostname to the actual distribution hostname; these live actions remain deferred. No invented runtime hostname or fixture certificate is deployment-ready.

Bundled edge/service Lambda code explicitly uses X86_64 and Docker linux/amd64, matching existing x86 CI runners. Local synthesis packages assets and runs cdk-nag; its success is required independently of unit tests. Resource-specific documented exceptions retain the supported tested Python3.12 pin, coordinated protocol-secret rotation, dev-only no-paid-Plus identity, AWS API wildcard limitations, privacy-safe logging and edge authentication. No blanket or TLS exception is allowed. No deployment, asset upload or paid resource creation is authorized by these instructions. Live release gates and exact local evidence are recorded in the intent's code summary.

## CI deployment setup

Create a GitHub OIDC role scoped to repository `00az/Raad` and the `dev` environment, grant only the deployment permissions required by these CDK stacks, and set `AWS_ROLE_ARN_DEV` in the GitHub `dev` environment. Set `AWS_REGION=us-east-1` and the matching `RAAD_*` GitHub environment variables from `.env.local`. The deploy workflow assumes that role; it does not use a long-lived access key.
