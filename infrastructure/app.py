"""CDK entry point for the shared RAAD platform: one set of stacks per environment.

Inputs come from the environment or CDK context and are validated together before any stack is
built (see read_deployment_inputs). Synthesis authorizes no lookup, asset upload or deployment.
"""

import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from raad_platform.stacks import (
    IdentityStack,
    MonitoringStack,
    PublicEdgeStack,
    read_deployment_inputs,
)

app = cdk.App()
inputs = read_deployment_inputs(os.environ, app.node.try_get_context)
environment = inputs.environment
stack_env = cdk.Environment(account=inputs.account, region=inputs.region)

# Monitoring has no dependency on the others; the edge reads identity and monitoring outputs.
monitoring = MonitoringStack(
    app,
    f"RaadMonitoring-{environment}",
    environment=environment,
    alert_email=inputs.alert_email,
    env=stack_env,
)
identity = IdentityStack(
    app,
    f"RaadIdentity-{environment}",
    environment=environment,
    env=stack_env,
)
PublicEdgeStack(
    app,
    f"RaadPublicEdge-{environment}",
    environment=environment,
    identity=identity,
    monitoring=monitoring,
    domain_name=inputs.domain_name,
    hosted_zone_id=inputs.hosted_zone_id,
    certificate_arn=inputs.certificate_arn,
    service_parameter=f"/raad/{environment}/money-api/function-url",
    env=stack_env,
)
cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
app.synth()
