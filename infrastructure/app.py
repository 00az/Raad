"""CDK entry point for the shared RAAD platform."""

import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from raad_platform.stacks import IdentityStack, MonitoringStack, PublicEdgeStack

app = cdk.App()
environment = os.environ.get("RAAD_ENVIRONMENT", "dev")
hosted_zone_id = app.node.try_get_context("hostedZoneId") or os.environ.get(
    "RAAD_HOSTED_ZONE_ID", ""
)
domain_name = app.node.try_get_context("domainName") or os.environ.get("RAAD_DOMAIN_NAME", "")
certificate_arn = app.node.try_get_context("certificateArn") or os.environ.get(
    "RAAD_CERTIFICATE_ARN", ""
)
alert_email = app.node.try_get_context("alertEmail") or os.environ.get("RAAD_ALERT_EMAIL", "")
cognito_domain_prefix = app.node.try_get_context("cognitoDomainPrefix") or os.environ.get(
    "RAAD_COGNITO_DOMAIN_PREFIX", ""
)
service_parameter = f"/raad/{environment}/money-api/function-url"
required = {
    "RAAD_DOMAIN_NAME": domain_name,
    "RAAD_HOSTED_ZONE_ID": hosted_zone_id,
    "RAAD_CERTIFICATE_ARN": certificate_arn,
    "RAAD_ALERT_EMAIL": alert_email,
    "RAAD_COGNITO_DOMAIN_PREFIX": cognito_domain_prefix,
}
missing = [name for name, value in required.items() if not value]
if missing:
    raise ValueError(f"Supply environment deployment inputs: {', '.join(missing)}")
if ":us-east-1:" not in certificate_arn:
    raise ValueError(
        "RAAD_CERTIFICATE_ARN must refer to the us-east-1 CloudFront viewer certificate"
    )
aws_region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
if aws_region != "us-east-1":
    raise ValueError("the CloudFront viewer certificate and global WAF ACL require us-east-1")
stack_env = cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region=aws_region)

identity = IdentityStack(
    app,
    f"RaadIdentity-{environment}",
    environment=environment,
    cognito_domain_prefix=cognito_domain_prefix,
    env=stack_env,
)
monitoring = MonitoringStack(
    app,
    f"RaadMonitoring-{environment}",
    environment=environment,
    alert_email=alert_email,
    env=stack_env,
)
PublicEdgeStack(
    app,
    f"RaadPublicEdge-{environment}",
    environment=environment,
    identity=identity,
    monitoring=monitoring,
    domain_name=domain_name,
    hosted_zone_id=hosted_zone_id,
    certificate_arn=certificate_arn,
    service_parameter=service_parameter,
    cognito_domain_prefix=cognito_domain_prefix,
    env=stack_env,
)
cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
app.synth()
