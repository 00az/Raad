"""Identity, edge, and monitoring stacks for the RAAD walking skeleton."""

from __future__ import annotations

from typing import Any

from aws_cdk import (
    BundlingOptions,
    Duration,
    Stack,
)
from aws_cdk import (
    aws_apigatewayv2 as apigwv2,
)
from aws_cdk import (
    aws_apigatewayv2_integrations as integrations,
)
from aws_cdk import (
    aws_certificatemanager as acm,
)
from aws_cdk import (
    aws_cloudfront as cloudfront,
)
from aws_cdk import (
    aws_cloudfront_origins as origins,
)
from aws_cdk import (
    aws_cloudwatch as cloudwatch,
)
from aws_cdk import (
    aws_cloudwatch_actions as cw_actions,
)
from aws_cdk import (
    aws_cognito as cognito,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_kinesis as kinesis,
)
from aws_cdk import (
    aws_kms as kms,
)
from aws_cdk import (
    aws_lambda as lambda_,
)
from aws_cdk import (
    aws_lambda_event_sources as event_sources,
)
from aws_cdk import (
    aws_logs as logs,
)
from aws_cdk import (
    aws_route53 as route53,
)
from aws_cdk import (
    aws_scheduler as scheduler,
)
from aws_cdk import (
    aws_secretsmanager as secretsmanager,
)
from aws_cdk import (
    aws_sns as sns,
)
from aws_cdk import (
    aws_sns_subscriptions as subscriptions,
)
from aws_cdk import (
    aws_ssm as ssm,
)
from aws_cdk import (
    aws_wafv2 as wafv2,
)
from constructs import Construct

from raad_platform.telemetry.handler import FIELDS


class IdentityStack(Stack):
    """Environment-specific Cognito pool and correlation HMAC secret."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment: str,
        cognito_domain_prefix: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"raad-{environment}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                fullname=cognito.StandardAttribute(required=True, mutable=True),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=True,
            ),
            removal_policy=(
                __import__("aws_cdk").RemovalPolicy.DESTROY
                if environment == "dev"
                else __import__("aws_cdk").RemovalPolicy.RETAIN
            ),
        )
        self.client = self.user_pool.add_client(
            "MobileClient",
            auth_flows=cognito.AuthFlow(user_srp=True, admin_user_password=True),
            generate_secret=False,
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=[f"raad-{environment}://auth/callback"],
            ),
        )
        if not cognito_domain_prefix:
            raise ValueError(
                "RAAD_COGNITO_DOMAIN_PREFIX must be supplied for Cognito userInfo verification"
            )
        self.user_pool.add_domain(
            "HostedUiDomain",
            cognito_domain=cognito.CognitoDomainOptions(domain_prefix=cognito_domain_prefix),
        )
        self.correlation_secret = secretsmanager.Secret(
            self,
            "CorrelationHmac",
            secret_name=f"raad/{environment}/correlation-hmac",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                password_length=64,
                exclude_punctuation=True,
                secret_string_template='{"version":"1"}',
                generate_string_key="key",
            ),
        )


class MonitoringStack(Stack):
    """Privacy-bounded logs, dashboard, and sample-gated operational alarms."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment: str,
        alert_email: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.key = kms.Alias(
            self,
            "LogKey",
            alias_name=f"alias/raad-{environment}-logs",
            target_key=kms.Key(self, "LogsKey", enable_key_rotation=True),
        )
        self.topic = sns.Topic(self, "Alerts", topic_name=f"raad-{environment}-alerts")
        if alert_email:
            self.topic.add_subscription(subscriptions.EmailSubscription(alert_email))
        self.dashboard = cloudwatch.Dashboard(
            self, "Dashboard", dashboard_name=f"raad-{environment}"
        )
        self.edge_requests = cloudwatch.Metric(
            namespace="Raad/Platform",
            metric_name="EdgeRequests",
            dimensions_map={"Environment": environment},
            statistic="sum",
            period=Duration.minutes(1),
        )
        self.edge_5xx = cloudwatch.Metric(
            namespace="Raad/Platform",
            metric_name="Edge5xx",
            dimensions_map={"Environment": environment},
            statistic="sum",
            period=Duration.minutes(1),
        )
        error_alarm = cloudwatch.Alarm(
            self,
            "ServerErrors",
            metric=self.edge_5xx,
            threshold=3,
            evaluation_periods=2,
            datapoints_to_alarm=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.MISSING,
        )
        error_alarm.add_alarm_action(cw_actions.SnsAction(self.topic))
        self.transfer_latency = cloudwatch.Metric(
            namespace="Raad/Platform",
            metric_name="AdapterTransferLatencyMs",
            dimensions_map={"Environment": environment},
            statistic="p95",
            period=Duration.minutes(5),
        )
        technical_failures = cloudwatch.Metric(
            namespace="Raad/Platform",
            metric_name="TechnicalTransferFailures",
            dimensions_map={"Environment": environment},
            statistic="sum",
            period=Duration.minutes(1),
        )
        failure_alarm = cloudwatch.Alarm(
            self,
            "TechnicalTransferFailure",
            metric=technical_failures,
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.MISSING,
        )
        failure_alarm.add_alarm_action(cw_actions.SnsAction(self.topic))
        self.dashboard.add_widgets(
            cloudwatch.TextWidget(
                markdown="No traffic and windows below the configured sample minimum are **insufficient data**, not evidence of health.",
                width=24,
                height=2,
            ),
            cloudwatch.GraphWidget(
                title="Edge requests and 5xx", left=[self.edge_requests, self.edge_5xx]
            ),
            cloudwatch.GraphWidget(
                title="Adapter diagnostic p95 (excludes initialization/outer edge)",
                left=[self.transfer_latency],
            ),
        )
        self.log_group = logs.LogGroup(
            self,
            "EdgeLogs",
            log_group_name=f"/raad/{environment}/platform-edge",
            retention=logs.RetentionDays.TWO_WEEKS,
            encryption_key=self.key,
        )
        self.public_samples = logs.LogGroup(
            self,
            "PublicSamples",
            log_group_name=f"/raad/{environment}/public-latency",
            retention=logs.RetentionDays.TWO_WEEKS,
        )
        self.telemetry_stream = kinesis.Stream(
            self,
            "PublicLatencyStream",
            stream_name=f"raad-{environment}-public-latency",
            shard_count=1,
            retention_period=Duration.hours(24),
            encryption=kinesis.StreamEncryption.MANAGED,
        )
        processor_logs = logs.LogGroup(
            self, "TelemetryLogs", retention=logs.RetentionDays.TWO_WEEKS
        )
        self.processor = lambda_.Function(
            self,
            "PublicLatencyProcessor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.handle",
            code=lambda_.Code.from_asset("raad_platform/telemetry"),
            timeout=Duration.seconds(20),
            reserved_concurrent_executions=2,
            log_group=processor_logs,
            environment={
                "ENVIRONMENT": environment,
                "SAMPLE_LOG_GROUP": self.public_samples.log_group_name,
            },
        )
        self.processor.add_event_source(
            event_sources.KinesisEventSource(
                self.telemetry_stream,
                starting_position=lambda_.StartingPosition.TRIM_HORIZON,
                batch_size=50,
                max_batching_window=Duration.seconds(1),
                retry_attempts=2,
            )
        )
        self.public_samples.grant_write(self.processor)
        self.processor.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:StartQuery"],
                resources=[self.public_samples.log_group_arn],
            )
        )
        self.processor.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:GetQueryResults", "logs:StopQuery"],
                resources=["*"],
            )
        )
        self.processor.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={"StringEquals": {"cloudwatch:namespace": "Raad/Platform"}},
            )
        )
        group = scheduler.CfnScheduleGroup(
            self, "TelemetryScheduleGroup", name=f"raad-{environment}-telemetry"
        )
        schedule_role = iam.Role(
            self,
            "TelemetrySchedulerRole",
            assumed_by=iam.ServicePrincipal(
                "scheduler.amazonaws.com",
                conditions={
                    "StringEquals": {"aws:SourceAccount": self.account},
                    "ArnEquals": {"aws:SourceArn": group.attr_arn},
                },
            ),
        )
        self.processor.grant_invoke(schedule_role)
        scheduler.CfnSchedule(
            self,
            "TelemetrySchedule",
            group_name=group.ref,
            schedule_expression="cron(2/5 * * * ? *)",
            schedule_expression_timezone="UTC",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.processor.function_arn,
                role_arn=schedule_role.role_arn,
                input='{"mode":"aggregate","scheduledTime":"<aws.scheduler.scheduled-time>"}',
                retry_policy=scheduler.CfnSchedule.RetryPolicyProperty(
                    maximum_event_age_in_seconds=120, maximum_retry_attempts=1
                ),
            ),
        )
        public_pair = cloudwatch.Metric(
            namespace="Raad/Platform",
            metric_name="PublicSlowPair",
            dimensions_map={"Environment": environment},
            statistic="Maximum",
            period=Duration.minutes(5),
        )
        # A pair already encodes two consecutive source windows and eligible recovery.
        public_alarm = cloudwatch.Alarm(
            self,
            "PublicSlowTransfers",
            metric=public_pair,
            threshold=0.5,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.MISSING,
        )
        public_alarm.add_alarm_action(cw_actions.SnsAction(self.topic))
        public_alarm.add_ok_action(cw_actions.SnsAction(self.topic))
        self.dashboard.add_widgets(
            cloudwatch.TextWidget(
                width=24,
                height=3,
                markdown="Public latency uses native CloudFront records. Live delivery coverage is **unknown** (best effort). Missing/mixed/low-volume windows are **insufficient**, not healthy. Component timers are diagnostic only.",
            ),
            cloudwatch.GraphWidget(
                title="Observed public p95 and count (Maximum gauges)",
                left=[
                    cloudwatch.Metric(
                        namespace="Raad/Platform",
                        metric_name="PublicP95Ms",
                        dimensions_map={"Environment": environment},
                        statistic="Maximum",
                    ),
                    cloudwatch.Metric(
                        namespace="Raad/Platform",
                        metric_name="PublicObservedCount",
                        dimensions_map={"Environment": environment},
                        statistic="Maximum",
                    ),
                ],
            ),
        )


class PublicEdgeStack(Stack):
    """Public HTTPS edge, WAF, and SigV4 forwarding adapter."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment: str,
        identity: IdentityStack,
        monitoring: MonitoringStack,
        domain_name: str,
        hosted_zone_id: str,
        certificate_arn: str,
        service_parameter: str,
        cognito_domain_prefix: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        code = lambda_.Code.from_asset(
            "raad_platform/edge",
            bundling=BundlingOptions(
                image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                command=[
                    "bash",
                    "-c",
                    "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output",
                ],
            ),
        )
        self.edge = lambda_.Function(
            self,
            "MoneyEdge",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.entry",
            code=code,
            timeout=Duration.seconds(9),
            reserved_concurrent_executions=20 if environment == "dev" else None,
            environment={
                "ENVIRONMENT": environment,
                "USER_POOL_ID": identity.user_pool.user_pool_id,
                "CLIENT_ID": identity.client.user_pool_client_id,
                "SERVICE_URL_PARAMETER": service_parameter,
                "CORRELATION_SECRET_ARN": identity.correlation_secret.secret_arn,
                "LOG_LEVEL": "INFO",
            },
            log_group=monitoring.log_group,
        )
        live_edge = self.edge.current_version.add_alias("live")
        identity.correlation_secret.grant_read(self.edge)
        self.edge.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    Stack.of(self).format_arn(
                        service="ssm",
                        resource="parameter",
                        resource_name=service_parameter.lstrip("/"),
                    )
                ],
            )
        )
        money_api_arn = Stack.of(self).format_arn(
            service="lambda", resource="function", resource_name=f"raad-{environment}-money-api"
        )
        self.edge.add_to_role_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunctionUrl"],
                resources=[money_api_arn],
                conditions={"StringEquals": {"lambda:FunctionUrlAuthType": "AWS_IAM"}},
            )
        )
        self.edge.add_to_role_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[money_api_arn],
                conditions={"Bool": {"lambda:InvokedViaFunctionUrl": "true"}},
            )
        )
        api = apigwv2.HttpApi(
            self,
            "MoneyHttpApi",
            api_name=f"raad-{environment}-money",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=["authorization", "content-type", "x-correlation-id"],
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
                allow_origins=[],
            ),
        )
        api.add_routes(
            path="/money/v1/{proxy+}",
            methods=[apigwv2.HttpMethod.ANY],
            integration=integrations.HttpLambdaIntegration(
                "MoneyEdgeIntegration", live_edge, timeout=Duration.seconds(10)
            ),
        )
        api.add_routes(
            path="/money/v1",
            methods=[apigwv2.HttpMethod.ANY],
            integration=integrations.HttpLambdaIntegration(
                "MoneyRootIntegration", live_edge, timeout=Duration.seconds(10)
            ),
        )
        self.api = api
        acl = wafv2.CfnWebACL(
            self,
            "BasicFirewall",
            scope="CLOUDFRONT",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name=f"raad-{environment}-waf",
                sampled_requests_enabled=False,
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSManagedCommon",
                    priority=1,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS", name="AWSManagedRulesCommonRuleSet"
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="common",
                        sampled_requests_enabled=False,
                    ),
                ),
                wafv2.CfnWebACL.RuleProperty(
                    name="BasicRateLimit",
                    priority=2,
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=1000, aggregate_key_type="IP"
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="rate",
                        sampled_requests_enabled=False,
                    ),
                ),
            ],
        )
        if domain_name and hosted_zone_id and certificate_arn:
            delivery_role = iam.Role(
                self,
                "CloudFrontTelemetryRole",
                assumed_by=iam.ServicePrincipal(
                    "cloudfront.amazonaws.com",
                    conditions={"StringEquals": {"aws:SourceAccount": self.account}},
                ),
            )
            monitoring.telemetry_stream.grant_write(delivery_role)
            realtime = cloudfront.CfnRealtimeLogConfig(
                self,
                "TransferRealtimeLogs",
                name=f"raad-{environment}-transfers",
                sampling_rate=100,
                fields=list(FIELDS),
                end_points=[
                    cloudfront.CfnRealtimeLogConfig.EndPointProperty(
                        stream_type="Kinesis",
                        kinesis_stream_config=cloudfront.CfnRealtimeLogConfig.KinesisStreamConfigProperty(
                            role_arn=delivery_role.role_arn,
                            stream_arn=monitoring.telemetry_stream.stream_arn,
                        ),
                    )
                ],
            )
            certificate = acm.Certificate.from_certificate_arn(
                self, "ViewerCertificate", certificate_arn
            )
            distribution = cloudfront.Distribution(
                self,
                "Distribution",
                domain_names=[domain_name],
                certificate=certificate,
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        f"{api.api_id}.execute-api.{Stack.of(self).region}.amazonaws.com",
                        protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                ),
                minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
                web_acl_id=acl.attr_arn,
            )
            distribution.add_behavior(
                "/money/v1/transfers",
                origins.HttpOrigin(
                    f"{api.api_id}.execute-api.{Stack.of(self).region}.amazonaws.com",
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            )
            distribution_resource = distribution.node.default_child
            assert isinstance(distribution_resource, cloudfront.CfnDistribution)
            distribution_resource.add_property_override(
                "DistributionConfig.CacheBehaviors.0.RealtimeLogConfigArn", realtime.ref
            )
            alias = route53.CfnRecordSet.AliasTargetProperty(
                dns_name=distribution.distribution_domain_name,
                hosted_zone_id="Z2FDTNDATAQYW2",
                evaluate_target_health=False,
            )
            route53.CfnRecordSet(
                self,
                "ApiAlias",
                hosted_zone_id=hosted_zone_id,
                name=domain_name,
                type="A",
                alias_target=alias,
            )
            route53.CfnRecordSet(
                self,
                "ApiAliasIpv6",
                hosted_zone_id=hosted_zone_id,
                name=domain_name,
                type="AAAA",
                alias_target=alias,
            )
        self.web_acl = acl
        assert self.edge.role is not None
        ssm.StringParameter(
            self,
            "PlatformEdgeRoleArn",
            parameter_name=f"/raad/{environment}/platform-edge-role-arn",
            string_value=self.edge.role.role_arn,
        )
        ssm.StringParameter(
            self,
            "CorrelationSecretArn",
            parameter_name=f"/raad/{environment}/correlation-hmac/arn",
            string_value=identity.correlation_secret.secret_arn,
        )
        profile_url = f"https://{cognito_domain_prefix}.auth.{Stack.of(self).region}.amazoncognito.com/oauth2/userInfo"
        issuer = f"https://cognito-idp.{Stack.of(self).region}.amazonaws.com/{identity.user_pool.user_pool_id}"
        verifier = {
            "configVersion": "1.0",
            "environment": environment,
            "issuer": issuer,
            "audience": identity.client.user_pool_client_id,
            "audienceClaim": "client_id",
            "tokenTypeMarker": {
                "location": "claim",
                "name": "token_use",
                "expectedValue": "access",
            },
            "jwksUri": issuer + "/.well-known/jwks.json",
            "acceptedAlgorithms": ["RS256"],
            "profileAttributeSource": "user-profile-endpoint",
            "userProfileUri": profile_url,
        }
        ssm.StringParameter(
            self,
            "EnvironmentVerifier",
            parameter_name=f"/raad/{environment}/verifier",
            string_value=__import__("json").dumps(verifier),
        )
