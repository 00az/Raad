"""Identity, edge, and monitoring stacks for the shared RAAD platform (U1 skeleton, U4)."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from aws_cdk import (
    BundlingOptions,
    CfnOutput,
    Duration,
    RemovalPolicy,
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
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_events as events,
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
from cdk_nag import NagSuppressions
from constructs import Construct

from raad_platform import configuration
from raad_platform.identity import publisher
from raad_platform.telemetry.handler import FIELDS

ENVIRONMENTS = ("dev", "stg", "prd")
# Regional WAF on the user pool (NFR12.11, C3 P10). AWS documents that WAF sees the public and
# token-authorized user pool operations, GetUser included, and that the user pools API names
# each request's operation in this header. The exact header value format is not shown in the
# documentation, so the match also accepts the service-prefixed form; the real classification
# is a deployed gate (unknown classification blocks release).
COGNITO_OPERATION_HEADER = "x-amzn-cognito-operation-name"
ACCOUNT_OPERATIONS = (
    "SignUp",
    "ConfirmSignUp",
    "ResendConfirmationCode",
    "InitiateAuth",
    "RespondToAuthChallenge",
    "ForgotPassword",
    "ConfirmForgotPassword",
)
# MoneyApi's GetUser calls share backend egress addresses, so they stay out of every IP bucket.
PROFILE_OPERATION = "GetUser"
ACCOUNT_OPERATION_LIMIT = 100
GENERAL_OPERATION_LIMIT = 300
OPERATION_WINDOW_SECONDS = 300


def operation_pattern(operations: tuple[str, ...]) -> str:
    """Anchored match for the bare or service-prefixed operation name."""
    return r"^(AWSCognitoIdentityProviderService\.)?(" + "|".join(operations) + r")$"


# C3 session policy: 60-minute access tokens; a fixed 30-day refresh lifetime (check P9).
ACCESS_TOKEN_MINUTES = 60
REFRESH_TOKEN_DAYS = 30


def require_environment(environment: str) -> None:
    """Every stack belongs to exactly one of the three named environments."""
    if environment not in ENVIRONMENTS:
        raise ValueError("environment must be dev, stg or prd")


def log_retention(environment: str) -> logs.RetentionDays:
    """Observability design: 14 days in dev, 30 days in stg and prd."""
    return logs.RetentionDays.TWO_WEEKS if environment == "dev" else logs.RetentionDays.ONE_MONTH


RESERVED_CONCURRENCY_CONTEXT = "raad:reservedConcurrency"


def reserved_concurrency(scope: Construct, environment: str, value: int | None) -> int | None:
    """A function's reserved concurrency, unless a dev deploy turns reservations off.

    A new AWS account allows 10 concurrent executions and keeps all 10 unreserved, so no
    reservation can be made until the limit is raised. A dev deploy in such an account passes
    `-c raad:reservedConcurrency=off`; stg and prd refuse the switch.
    """
    setting = scope.node.try_get_context(RESERVED_CONCURRENCY_CONTEXT)
    if setting is None or str(setting).lower() in ("on", "true"):
        return value
    if str(setting).lower() not in ("off", "false"):
        raise ValueError(f"{RESERVED_CONCURRENCY_CONTEXT} must be on or off")
    if environment != "dev":
        raise ValueError(f"{RESERVED_CONCURRENCY_CONTEXT}=off is allowed only in dev")
    return None


@dataclass(frozen=True)
class DeploymentInputs:
    """One environment's deployment inputs; none of them is a credential."""

    environment: str
    account: str
    region: str
    domain_name: str
    hosted_zone_id: str
    certificate_arn: str
    # The alert address is configuration only; it is never printed or written to source.
    alert_email: str = field(repr=False)


def read_deployment_inputs(
    environ: Mapping[str, str], context: Callable[[str], Any]
) -> DeploymentInputs:
    """Validate environment, account, region, host, certificate and alert inputs together.

    Every check fails before any stack is built. Error text names the input, never its value,
    so an alert address or other configuration never reaches CI or terminal logs.
    """
    environment = environ.get("RAAD_ENVIRONMENT", "")
    require_environment(environment)
    region = (
        environ.get("CDK_DEFAULT_REGION")
        or environ.get("AWS_REGION")
        or environ.get("AWS_DEFAULT_REGION")
        or ""
    )
    if region != "us-east-1":
        raise ValueError(
            "CDK_DEFAULT_REGION must be us-east-1: the CloudFront viewer certificate and "
            "global WAF ACL require it (set AWS_REGION/AWS_DEFAULT_REGION and disable EC2 "
            "metadata lookups in CI)"
        )
    account = environ.get("CDK_DEFAULT_ACCOUNT", "")
    if not re.fullmatch(r"[0-9]{12}", account):
        raise ValueError("CDK_DEFAULT_ACCOUNT must be a 12-digit account ID")
    expected = environ.get("RAAD_EXPECTED_ACCOUNT", "")
    if expected and expected != account:
        raise ValueError("CDK_DEFAULT_ACCOUNT does not match RAAD_EXPECTED_ACCOUNT")

    def value(context_key: str, variable: str) -> str:
        found = context(context_key) or environ.get(variable, "")
        return str(found).strip()

    domain = value("domainName", "RAAD_DOMAIN_NAME")
    zone = value("hostedZoneId", "RAAD_HOSTED_ZONE_ID")
    certificate = value("certificateArn", "RAAD_CERTIFICATE_ARN")
    alert_email = value("alertEmail", "RAAD_ALERT_EMAIL")
    validate_public_domain(environment, domain, zone, certificate)
    if certificate.split(":")[4:5] != [account]:
        raise ValueError("RAAD_CERTIFICATE_ARN must belong to CDK_DEFAULT_ACCOUNT")
    if zone and not re.fullmatch(r"Z[A-Z0-9]{4,32}", zone):
        raise ValueError("RAAD_HOSTED_ZONE_ID must be an existing Route 53 hosted zone ID")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", alert_email):
        raise ValueError("Supply RAAD_ALERT_EMAIL from protected deployment configuration")
    return DeploymentInputs(environment, account, region, domain, zone, certificate, alert_email)


def validate_public_domain(environment: str, domain: str, zone: str, certificate: str) -> None:
    """Require a controlled hostname/certificate pair; an existing DNS zone is optional."""
    if not domain or not certificate:
        raise ValueError(
            "Supply domain and custom certificate together; default TLS is unsupported"
        )
    if "://" in domain or "/" in domain or "." not in domain or domain.endswith(".cloudfront.net"):
        raise ValueError("Supply a controlled custom hostname")
    if ":us-east-1:" not in certificate:
        raise ValueError("CloudFront viewer certificate must be in us-east-1")


def _execution_role(scope: Construct, identifier: str, log_group: logs.ILogGroup) -> iam.Role:
    """Bound log writes to this function's precreated group, without managed policies."""
    role = iam.Role(scope, identifier, assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
    log_group.grant_write(role)
    return role


# Native CloudWatch alarms return to OK after one healthy evaluation. The observability design
# asked for three healthy windows; the person accepted native recovery (U4 handoff), recorded here
# and in U4's evidence. Breach criteria are unchanged.
RECOVERY_NOTE = (
    "Recovery: native CloudWatch returns to OK after one healthy evaluation (accepted "
    "deviation from the three-window design). Missing or low-volume data is insufficient "
    "evidence, never healthy."
)


def platform_metric(
    environment: str, name: str, statistic: str = "Sum", minutes: int = 1
) -> cloudwatch.Metric:
    """A Raad/Platform metric; Environment is its only dimension (no personal data)."""
    return cloudwatch.Metric(
        namespace="Raad/Platform",
        metric_name=name,
        dimensions_map={"Environment": environment},
        statistic=statistic,
        period=Duration.minutes(minutes),
    )


def platform_alarm(
    scope: Construct,
    identifier: str,
    *,
    metric: cloudwatch.IMetric,
    threshold: float,
    periods: int,
    topic: sns.ITopic,
    description: str,
    comparison: cloudwatch.ComparisonOperator = (
        cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
    ),
    missing: cloudwatch.TreatMissingData = cloudwatch.TreatMissingData.MISSING,
) -> cloudwatch.Alarm:
    """Alarm on `periods` consecutive breaching windows; notifies the environment topic."""
    alarm = cloudwatch.Alarm(
        scope,
        identifier,
        metric=metric,
        threshold=threshold,
        evaluation_periods=periods,
        datapoints_to_alarm=periods,
        comparison_operator=comparison,
        treat_missing_data=missing,
        alarm_description=f"{description} {RECOVERY_NOTE}",
    )
    alarm.add_alarm_action(cw_actions.SnsAction(topic))
    return alarm


def throttle_alarm(
    scope: Construct, identifier: str, metric: cloudwatch.IMetric, topic: sns.ITopic
) -> cloudwatch.Alarm:
    """Monitoring design: any throttle in each of two consecutive one-minute windows."""
    return platform_alarm(
        scope,
        identifier,
        metric=metric,
        threshold=1,
        periods=2,
        topic=topic,
        description="Throttling >=1/min in two consecutive windows.",
    )


def _runtime_pin_exception(function: lambda_.Function) -> None:
    # Supported AL2023 pin, not an obsolete runtime; managed patches remain enabled.
    NagSuppressions.add_resource_suppressions(
        function,
        [
            {
                "id": "AwsSolutions-L1",
                "reason": "Approved tested Python3.12 AL2023 pin is AWS-supported until 2028-10-31 with managed patches. Dependency audit and package tests gate release; a major upgrade requires synchronized local/CI runtime pins.",
            }
        ],
    )


def _rotation_exception(secret: secretsmanager.Secret, reason: str) -> None:
    # Protocol keys require coordinated users, unlike an AWS-managed database target.
    NagSuppressions.add_resource_suppressions(
        secret, [{"id": "AwsSolutions-SMG4", "reason": reason}]
    )


class IdentityStack(Stack):
    """Environment-specific Cognito pool (native SDK flow) and correlation HMAC secret."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        environment: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        require_environment(environment)
        # C3: one account per normalized email, only email and display name stored, both
        # immutable after sign-up, and A4's password rule exactly (no silent strengthening).
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"raad-{environment}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            sign_in_case_sensitive=False,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False),
                fullname=cognito.StandardAttribute(required=True, mutable=False),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=False,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.DESTROY if environment == "dev" else RemovalPolicy.RETAIN,
        )
        # Public native-SDK client: SRP sign-in and refresh only for the app. The admin
        # password flow needs IAM credentials (AdminInitiateAuth) and exists only for the
        # controlled test-fixture setup that RaadMoneyService's dev scripts use; it is not
        # reachable with the public client ID alone. No hosted UI or OAuth: CDK enables OAuth
        # flows by default, so they are disabled explicitly.
        self.client = self.user_pool.add_client(
            "MobileClient",
            auth_flows=cognito.AuthFlow(user_srp=True, admin_user_password=True),
            generate_secret=False,
            disable_o_auth=True,
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
            prevent_user_existence_errors=True,
            enable_token_revocation=True,
            access_token_validity=Duration.minutes(ACCESS_TOKEN_MINUTES),
            id_token_validity=Duration.minutes(ACCESS_TOKEN_MINUTES),
            # Fixed lifetime counted from sign-in, not an idle limit: U3 keeps last use and
            # signs out after 30 idle days (C3 check P9).
            refresh_token_validity=Duration.days(REFRESH_TOKEN_DAYS),
            read_attributes=cognito.ClientAttributes().with_standard_attributes(
                email=True, email_verified=True, fullname=True
            ),
            write_attributes=cognito.ClientAttributes().with_standard_attributes(
                email=True, fullname=True
            ),
        )
        self._event_producer(environment)
        self._account_firewall(environment)
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
        # Resource-specific identity exceptions; no nag rule is disabled for the app.
        NagSuppressions.add_resource_suppressions(
            self.user_pool,
            [
                {
                    # Paid Plus (threat protection) is not authorized for any environment.
                    "id": "AwsSolutions-COG8",
                    "reason": f"Paid Cognito Plus is not approved for {environment}; funds are simulated. Compensating controls are tested: A4 password policy, verified email, prevent-user-existence errors, token revocation, independent RS256/issuer/client/token_use checks at edge and MoneyApi, and the regional WAF on this pool. Retained release risk: no adaptive authentication or compromised-credential detection until Plus is approved.",
                },
                {
                    # A4 is the person-approved rule; nag's symbol requirement would change it.
                    "id": "AwsSolutions-COG1",
                    "reason": "Assumption A4 (approved requirements) fixes the password rule at 8+ characters with lower, upper and digit and no symbol; Abcdef12 must be accepted. Requiring symbols would silently strengthen A4 and break AC1.1.1, so the change goes to the person, not into code. Compensating controls: the approved A4 rule and Cognito's native sign-in lockout. The regional WAF on this pool is not relied on here: it is unverified until the dev P10 burst check (check_identity_capabilities.py --burst) observes a refusal.",
                },
            ],
        )
        _rotation_exception(
            self.correlation_secret,
            "Both independent runtimes share a versioned HMAC profile; rotation preserves current/previous keys through 14-day log retention. No AWS-managed rotation target exists for this protocol. Coordinated rollout/investigation is a deferred release check; no automatic rotation is claimed.",
        )
        # Non-secret deployment outputs read by scripts/write_platform_config.py (C4/C5).
        CfnOutput(self, "EnvironmentOutput", value=environment)
        CfnOutput(self, "UserPoolIdOutput", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientIdOutput", value=self.client.user_pool_client_id)
        CfnOutput(self, "EventBusArnOutput", value=self.event_bus.event_bus_arn)

    def _event_producer(self, environment: str) -> None:
        """C2: per-environment bus and a bounded sign-up-confirmation publisher.

        U2 owns the rule, queues and idempotent consumer on this bus. Encryption at rest uses
        EventBridge's service-owned key; no customer key is added for uniformity alone.
        """
        self.event_bus = events.EventBus(
            self, "IdentityEventBus", event_bus_name=f"raad-{environment}-identity-events"
        )
        publisher_logs = logs.LogGroup(
            self,
            "IdentityPublisherLogs",
            log_group_name=f"/raad/{environment}/identity-publisher",
            retention=log_retention(environment),
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.publisher_role = _execution_role(self, "IdentityPublisherRole", publisher_logs)
        # Identity side of exclusivity: this role may send only the contract's source/type.
        self.publisher_role.add_to_policy(
            iam.PolicyStatement(
                actions=["events:PutEvents"],
                resources=[self.event_bus.event_bus_arn],
                conditions={
                    "StringEquals": {
                        "events:source": [publisher.EVENT_SOURCE],
                        "events:detail-type": [publisher.EVENT_DETAIL_TYPE],
                    }
                },
            )
        )
        self.publisher = lambda_.Function(
            self,
            "IdentityEventPublisher",
            function_name=f"raad-{environment}-identity-publisher",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.X86_64,
            handler="publisher.handle",
            code=lambda_.Code.from_asset(
                "raad_platform/identity", exclude=["__pycache__", "*.pyc", "__init__.py"]
            ),
            memory_size=128,
            timeout=Duration.seconds(3),
            reserved_concurrent_executions=reserved_concurrency(self, environment, 2),
            log_group=publisher_logs,
            role=self.publisher_role,
            environment={
                "ENVIRONMENT": environment,
                "EVENT_BUS_ARN": self.event_bus.event_bus_arn,
            },
        )
        _runtime_pin_exception(self.publisher)
        # Cognito invokes this only for its own pool (CDK scopes the permission's SourceArn).
        self.user_pool.add_trigger(cognito.UserPoolOperation.POST_CONFIRMATION, self.publisher)
        self._restrict_bus_publishers()
        ssm.StringParameter(
            self,
            "EventBusArnParameter",
            parameter_name=f"/raad/{environment}/event-bus/arn",
            string_value=self.event_bus.event_bus_arn,
        )

    def _restrict_bus_publishers(self) -> None:
        """Make the publisher role the only sender, and only of the C2 source/detail type.

        In one account an identity policy alone can grant events:PutEvents, so an allow-only
        bus statement would not make the publisher exclusive. Explicit denies bind every
        principal in the account, including administrators. Policy writes on one bus are
        serialized to avoid concurrent-modification failures during deployment.
        """
        bus_arn = self.event_bus.event_bus_arn
        statements = {
            "DenyOtherPublishers": {
                "ArnNotEquals": {"aws:PrincipalArn": self.publisher_role.role_arn}
            },
            "DenyOtherSources": {"StringNotEquals": {"events:source": publisher.EVENT_SOURCE}},
            "DenyOtherDetailTypes": {
                "StringNotEquals": {"events:detail-type": publisher.EVENT_DETAIL_TYPE}
            },
        }
        previous: events.CfnEventBusPolicy | None = None
        for statement_id, condition in statements.items():
            policy = events.CfnEventBusPolicy(
                self,
                f"IdentityEventBus{statement_id}",
                event_bus_name=self.event_bus.event_bus_name,
                statement_id=statement_id,
                statement={
                    "Sid": statement_id,
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "events:PutEvents",
                    "Resource": bus_arn,
                    "Condition": condition,
                },
            )
            if previous is not None:
                policy.node.add_dependency(previous)
            previous = policy

    def _account_firewall(self, environment: str) -> None:
        """Approximate per-IP limits on the direct-SDK account path (C3 P10, NFR12.11).

        These are coarse abuse limits, not exact per-account counters; the provider's own
        throttling and lockout complement them. Sampling and request logging stay off, so no
        username, email or body reaches WAF records, and metrics carry no personal dimension.
        """

        def operation(pattern: str) -> wafv2.CfnWebACL.StatementProperty:
            return wafv2.CfnWebACL.StatementProperty(
                regex_match_statement=wafv2.CfnWebACL.RegexMatchStatementProperty(
                    regex_string=pattern,
                    field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                        single_header={"Name": COGNITO_OPERATION_HEADER}
                    ),
                    text_transformations=[
                        wafv2.CfnWebACL.TextTransformationProperty(priority=0, type="NONE")
                    ],
                )
            )

        def per_ip(
            name: str, priority: int, limit: int, scope: wafv2.CfnWebACL.StatementProperty
        ) -> wafv2.CfnWebACL.RuleProperty:
            return wafv2.CfnWebACL.RuleProperty(
                name=name,
                priority=priority,
                action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                statement=wafv2.CfnWebACL.StatementProperty(
                    rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                        limit=limit,
                        aggregate_key_type="IP",
                        evaluation_window_sec=OPERATION_WINDOW_SECONDS,
                        scope_down_statement=scope,
                    )
                ),
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    cloud_watch_metrics_enabled=True,
                    metric_name=f"raad-{environment}-identity-{name}",
                    sampled_requests_enabled=False,
                ),
            )

        not_profile = wafv2.CfnWebACL.StatementProperty(
            not_statement=wafv2.CfnWebACL.NotStatementProperty(
                statement=operation(operation_pattern((PROFILE_OPERATION,)))
            )
        )
        self.identity_firewall = wafv2.CfnWebACL(
            self,
            "IdentityFirewall",
            name=f"raad-{environment}-identity",
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name=f"raad-{environment}-identity-waf",
                sampled_requests_enabled=False,
            ),
            rules=[
                per_ip(
                    "AccountOperationsPerIp",
                    1,
                    ACCOUNT_OPERATION_LIMIT,
                    operation(operation_pattern(ACCOUNT_OPERATIONS)),
                ),
                per_ip("GeneralOperationsPerIp", 2, GENERAL_OPERATION_LIMIT, not_profile),
            ],
        )
        wafv2.CfnWebACLAssociation(
            self,
            "IdentityFirewallAssociation",
            resource_arn=self.user_pool.user_pool_arn,
            web_acl_arn=self.identity_firewall.attr_arn,
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
        require_environment(environment)
        self.logs_key = kms.Key(self, "LogsKey", enable_key_rotation=True)
        # CloudWatch Logs can encrypt a log group with this key only when the key policy names
        # the regional Logs service, limited here to this account's log groups. Without it the
        # first dev deploy failed to create the edge log group.
        self.logs_key.add_to_resource_policy(
            iam.PolicyStatement(
                principals=[iam.ServicePrincipal(f"logs.{self.region}.amazonaws.com")],
                actions=[
                    "kms:Encrypt*",
                    "kms:Decrypt*",
                    "kms:ReEncrypt*",
                    "kms:GenerateDataKey*",
                    "kms:Describe*",
                ],
                resources=["*"],
                conditions={
                    "ArnLike": {
                        "kms:EncryptionContext:aws:logs:arn": (
                            f"arn:{self.partition}:logs:{self.region}:{self.account}:log-group:*"
                        )
                    }
                },
            )
        )
        self.key = kms.Alias(
            self,
            "LogKey",
            alias_name=f"alias/raad-{environment}-logs",
            target_key=self.logs_key,
        )
        self.topic = sns.Topic(self, "Alerts", topic_name=f"raad-{environment}-alerts")
        self.topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["sns:Publish"],
                resources=[self.topic.topic_arn],
                conditions={"Bool": {"aws:SecureTransport": "false"}},
            )
        )
        # A topic policy replaces SNS's default owner policy, so alarm delivery from this and
        # U2's stacks needs CloudWatch named explicitly, limited to this account's alarms.
        self.topic.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("cloudwatch.amazonaws.com")],
                actions=["sns:Publish"],
                resources=[self.topic.topic_arn],
                conditions={
                    "StringEquals": {"aws:SourceAccount": self.account},
                    "ArnLike": {
                        "aws:SourceArn": f"arn:{self.partition}:cloudwatch:{self.region}:{self.account}:alarm:*"
                    },
                },
            )
        )
        # Address comes only from deployment configuration; it is never written to source.
        if alert_email:
            self.topic.add_subscription(subscriptions.EmailSubscription(alert_email))
        ssm.StringParameter(
            self,
            "AlarmTopicArnParameter",
            parameter_name=f"/raad/{environment}/alarm-topic/arn",
            string_value=self.topic.topic_arn,
        )
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
        # Technical 5xx >=1% with >=20 eligible requests, in two consecutive 5-minute windows.
        # Below 20 requests the expression yields no datapoint, so low volume is never healthy.
        self.error_rate = cloudwatch.MathExpression(
            expression="IF(requests >= 20, 100 * FILL(errors, 0) / requests)",
            using_metrics={
                "requests": platform_metric(environment, "EdgeRequests", minutes=5),
                "errors": platform_metric(environment, "Edge5xx", minutes=5),
            },
            period=Duration.minutes(5),
            label="Technical 5xx rate % (>=20 requests)",
        )
        platform_alarm(
            self,
            "ServerErrors",
            metric=self.error_rate,
            threshold=1,
            periods=2,
            topic=self.topic,
            description="Technical 5xx >=1% with >=20 eligible requests in two 5-minute windows.",
        )
        self.transfer_latency = cloudwatch.Metric(
            namespace="Raad/Platform",
            metric_name="AdapterTransferLatencyMs",
            dimensions_map={"Environment": environment},
            statistic="p95",
            period=Duration.minutes(5),
        )
        platform_alarm(
            self,
            "TechnicalTransferFailure",
            metric=platform_metric(environment, "TechnicalTransferFailures", minutes=5),
            threshold=3,
            periods=2,
            topic=self.topic,
            description="Technical transfer failures >=3 in each of two 5-minute windows.",
        )
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
            retention=log_retention(environment),
            # CloudWatch Logs takes the key's own ARN; an alias ARN is refused.
            encryption_key=self.logs_key,
        )
        self.public_samples = logs.LogGroup(
            self,
            "PublicSamples",
            log_group_name=f"/raad/{environment}/public-latency",
            retention=log_retention(environment),
        )
        self.telemetry_stream = kinesis.Stream(
            self,
            "PublicLatencyStream",
            stream_name=f"raad-{environment}-public-latency",
            shard_count=1,
            retention_period=Duration.hours(24),
            encryption=kinesis.StreamEncryption.MANAGED,
        )
        processor_logs = logs.LogGroup(self, "TelemetryLogs", retention=log_retention(environment))
        processor_role = _execution_role(self, "TelemetryExecutionRole", processor_logs)
        self.processor = lambda_.Function(
            self,
            "PublicLatencyProcessor",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.X86_64,
            handler="handler.handle",
            code=lambda_.Code.from_asset("raad_platform/telemetry"),
            timeout=Duration.seconds(20),
            reserved_concurrent_executions=reserved_concurrency(self, environment, 2),
            log_group=processor_logs,
            role=processor_role,
            environment={
                "ENVIRONMENT": environment,
                "SAMPLE_LOG_GROUP": self.public_samples.log_group_name,
            },
        )
        _runtime_pin_exception(self.processor)
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
                actions=["logs:StartQuery", "logs:GetQueryResults"],
                resources=[self.public_samples.log_group_arn],
            )
        )
        self.processor.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:StopQuery"],
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
        # StopQuery has no resource type. Queries/results and metric namespace are bounded.
        NagSuppressions.add_resource_suppressions(
            processor_role,
            [
                {
                    "id": "AwsSolutions-IAM5",
                    "appliesTo": ["Resource::*"],
                    "reason": "StopQuery has no resource type. Existing namespace metric publishing uses no dataset ARN and is restricted to Raad/Platform. StartQuery/GetQueryResults target only the safe sample group. No money access is granted.",
                }
            ],
            apply_to_children=True,
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
        schedule_role.add_to_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[self.processor.function_arn],
            )
        )
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
            alarm_description=(
                "Public transfer p95 >2000 ms in two complete 5-minute windows with >=20 "
                f"samples each. {RECOVERY_NOTE}"
            ),
        )
        public_alarm.add_alarm_action(cw_actions.SnsAction(self.topic))
        public_alarm.add_ok_action(cw_actions.SnsAction(self.topic))
        self._observation_health(environment, group, schedule_role)
        self._platform_alarms(environment)
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

    def _observation_health(
        self, environment: str, group: scheduler.CfnScheduleGroup, role: iam.Role
    ) -> None:
        """Collector heartbeat every minute, and alarms separate from the latency SLO."""
        scheduler.CfnSchedule(
            self,
            "TelemetryHeartbeatSchedule",
            group_name=group.ref,
            schedule_expression="rate(1 minute)",
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(mode="OFF"),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.processor.function_arn,
                role_arn=role.role_arn,
                input='{"mode":"heartbeat"}',
                retry_policy=scheduler.CfnSchedule.RetryPolicyProperty(
                    maximum_event_age_in_seconds=60, maximum_retry_attempts=0
                ),
            ),
        )
        # Absent for three consecutive minutes: missing data counts as breaching here only.
        platform_alarm(
            self,
            "CollectorHeartbeatMissing",
            metric=platform_metric(environment, "PublicCollectorHeartbeat"),
            threshold=1,
            periods=3,
            comparison=cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
            missing=cloudwatch.TreatMissingData.BREACHING,
            topic=self.topic,
            description="Public-latency collector heartbeat absent for three minutes.",
        )
        # A failed or contradictory collection is an observation-health fault, distinct from
        # low volume, which stays insufficient evidence without alarming.
        platform_alarm(
            self,
            "PublicCollectionFailure",
            metric=platform_metric(environment, "PublicCollectionFailures", "Maximum", 5),
            threshold=1,
            periods=2,
            topic=self.topic,
            description="Public-latency collection failed in two consecutive 5-minute windows.",
        )
        throttle_alarm(
            self,
            "TelemetryProcessorThrottles",
            self.processor.metric_throttles(period=Duration.minutes(1), statistic="Sum"),
            self.topic,
        )

    def _platform_alarms(self, environment: str) -> None:
        """Identity publisher and rate-store signals, by environment only."""
        publisher_name = f"raad-{environment}-identity-publisher"
        platform_alarm(
            self,
            "IdentityEventPublishFailure",
            metric=platform_metric(environment, "IdentityEventPublishFailures", minutes=5),
            threshold=1,
            periods=1,
            topic=self.topic,
            description=(
                "A C2 UserConfirmed event was not accepted by the bus; confirmation still "
                "succeeded and PUT /wallet repairs wallet setup."
            ),
        )
        throttle_alarm(
            self,
            "IdentityPublisherThrottles",
            cloudwatch.Metric(
                namespace="AWS/Lambda",
                metric_name="Throttles",
                dimensions_map={"FunctionName": publisher_name},
                statistic="Sum",
                period=Duration.minutes(1),
            ),
            self.topic,
        )
        platform_alarm(
            self,
            "RateStoreUnavailable",
            metric=platform_metric(environment, "EdgeRateStoreUnavailable"),
            threshold=1,
            periods=2,
            topic=self.topic,
            description="Rate-window store failures >=1/min in two consecutive windows (503s).",
        )
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Rate decisions (429 refusals, store unavailable)",
                left=[
                    platform_metric(environment, "EdgeRateLimited"),
                    platform_metric(environment, "EdgeRateStoreUnavailable"),
                ],
            ),
            cloudwatch.GraphWidget(
                title="C2 publisher (published, skipped, failed)",
                left=[
                    platform_metric(environment, "IdentityEventsPublished"),
                    platform_metric(environment, "IdentityEventsSkipped"),
                    platform_metric(environment, "IdentityEventPublishFailures"),
                ],
            ),
            cloudwatch.GraphWidget(
                title="Observation health (heartbeat, collection failures, insufficient)",
                left=[
                    platform_metric(environment, "PublicCollectorHeartbeat"),
                    platform_metric(environment, "PublicCollectionFailures", "Maximum", 5),
                    platform_metric(environment, "PublicCollectionInsufficient", "Maximum", 5),
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
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        require_environment(environment)
        validate_public_domain(environment, domain_name, hosted_zone_id, certificate_arn)
        code = lambda_.Code.from_asset(
            "raad_platform/edge",
            bundling=BundlingOptions(
                image=lambda_.Runtime.PYTHON_3_12.bundling_image,
                platform="linux/amd64",
                # Keep the raad_platform.edge package layout so the handler and its rate-store
                # module import identically in Lambda and in the offline tests.
                command=[
                    "bash",
                    "-c",
                    (
                        "pip install -r requirements.txt -t /asset-output"
                        " && mkdir -p /asset-output/raad_platform/edge"
                        " && cp -au . /asset-output/raad_platform/edge"
                        " && touch /asset-output/raad_platform/__init__.py"
                    ),
                ],
            ),
        )
        origin_secret = secretsmanager.Secret(
            self,
            "OriginVerificationSecret",
            secret_name=f"raad/{environment}/cloudfront-origin",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                password_length=64, exclude_punctuation=True
            ),
        )
        _rotation_exception(
            origin_secret,
            "CloudFront origin header and edge expected key require coordinated distribution/secret rollout; AWS has no managed rotation target for this protocol. Constant-time checks, bounded 60-second cache and fail-closed mismatch are tested; live rotation verification is deferred.",
        )
        edge_role = _execution_role(self, "EdgeExecutionRole", monitoring.log_group)
        # Platform-owned verified-caller counters (C5 rate_limits). Items hold an HMAC-protected
        # subject, a count and a cleanup expiry only; no money data or request keys.
        self.rate_table = dynamodb.Table(
            self,
            "PlatformRateWindows",
            table_name=f"raad-{environment}-platform-rate-windows",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expiresAt",
            # Service-owned encryption at rest; no customer key for counters alone.
            encryption=dynamodb.TableEncryption.DEFAULT,
            # Team practice keeps PITR on data stores; this table is tiny, so the cost is nil.
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.DESTROY if environment == "dev" else RemovalPolicy.RETAIN,
        )
        self.edge = lambda_.Function(
            self,
            "MoneyEdge",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.X86_64,
            handler="raad_platform.edge.handler.entry",
            code=code,
            timeout=Duration.seconds(9),
            reserved_concurrent_executions=reserved_concurrency(
                self, environment, 20 if environment == "dev" else None
            ),
            environment={
                "ENVIRONMENT": environment,
                "USER_POOL_ID": identity.user_pool.user_pool_id,
                "CLIENT_ID": identity.client.user_pool_client_id,
                "SERVICE_URL_PARAMETER": service_parameter,
                "CORRELATION_SECRET_ARN": identity.correlation_secret.secret_arn,
                "ORIGIN_SECRET_ARN": origin_secret.secret_arn,
                "LOG_LEVEL": "INFO",
                "RATE_TABLE_NAME": self.rate_table.table_name,
            },
            log_group=monitoring.log_group,
            role=edge_role,
        )
        _runtime_pin_exception(self.edge)
        live_edge = self.edge.add_alias("live")
        identity.correlation_secret.grant_read(self.edge)
        origin_secret.grant_read(self.edge)
        # Conditional counter updates only (TransactWriteItems is authorized per UpdateItem).
        self.rate_table.grant(self.edge, "dynamodb:UpdateItem")
        throttle_alarm(
            self,
            "EdgeThrottles",
            self.edge.metric_throttles(period=Duration.minutes(1), statistic="Sum"),
            monitoring.topic,
        )
        throttle_alarm(
            self,
            "RateWindowThrottles",
            self.rate_table.metric(
                "WriteThrottleEvents", period=Duration.minutes(1), statistic="Sum"
            ),
            monitoring.topic,
        )
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
        access_logs = logs.LogGroup(
            self,
            "ApiAccessLogs",
            log_group_name=f"/raad/{environment}/http-api",
            retention=log_retention(environment),
        )
        stage = api.default_stage.node.default_child if api.default_stage else None
        assert isinstance(stage, apigwv2.CfnStage)
        stage.access_log_settings = apigwv2.CfnStage.AccessLogSettingsProperty(
            destination_arn=access_logs.log_group_arn,
            format='{"requestId":"$context.requestId","status":"$context.status","latencyMs":"$context.responseLatency"}',
        )
        # JWT/origin authentication is deliberately in the edge for C1-safe errors.
        for child in api.node.find_all():
            if isinstance(child, apigwv2.CfnRoute):
                NagSuppressions.add_resource_suppressions(
                    child,
                    [
                        {
                            "id": "AwsSolutions-APIG4",
                            "reason": "Integration independently verifies RS256 issuer/client/type/expiry and the origin secret before forwarding. Keeping auth in edge preserves mandatory C1 errors. Tests cover token rejection, spoofed identity and direct-origin rejection.",
                        }
                    ],
                )
        self.api = api
        if environment == "dev":
            self._dev_stub_mapping(environment, api, code, origin_secret)
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
                    custom_headers={"X-Raad-Origin": origin_secret.secret_value.unsafe_unwrap()},
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
                custom_headers={"X-Raad-Origin": origin_secret.secret_value.unsafe_unwrap()},
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
        if hosted_zone_id:
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
        # Standard logs expose viewer IP/query/user-agent, forbidden by this privacy profile.
        NagSuppressions.add_resource_suppressions(
            distribution,
            [
                {
                    "id": "AwsSolutions-CFR3",
                    "reason": "Approved privacy design excludes viewer IP/query/user-agent standard logs. Transfers have 100%-sampled seven-field realtime logs, with safe API/edge logs for other responses. Missing delivery blocks latency acceptance; field allowlists/privacy are tested.",
                }
            ],
        )
        self.distribution = distribution
        self.public_api_url = "https://" + domain_name
        ssm.StringParameter(
            self,
            "PublicApiUrl",
            parameter_name=f"/raad/{environment}/public-api-url",
            string_value=self.public_api_url,
        )
        CfnOutput(self, "PublicApiUrlOutput", value=self.public_api_url)
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
        # C5 verifier for SDK (SRP/admin) access tokens, built by the same function the C4/C5
        # writer uses to check deployment outputs.
        verifier = configuration.verifier_config(
            environment,
            Stack.of(self).region,
            identity.user_pool.user_pool_id,
            identity.client.user_pool_client_id,
        )
        verifier_json = json.dumps(verifier)
        ssm.StringParameter(
            self,
            "EnvironmentVerifier",
            parameter_name=f"/raad/{environment}/verifier",
            string_value=verifier_json,
        )
        # Non-secret deployment outputs read by scripts/write_platform_config.py and the smoke
        # tool. The origin credential and secret values are never outputs.
        CfnOutput(self, "EnvironmentOutput", value=environment)
        CfnOutput(self, "VerifierConfigOutput", value=verifier_json)
        CfnOutput(self, "HttpApiEndpointOutput", value=api.api_endpoint)

    def _dev_stub_mapping(
        self,
        environment: str,
        api: apigwv2.HttpApi,
        code: lambda_.Code,
        origin_secret: secretsmanager.Secret,
    ) -> None:
        """NFR13.10: a nonfinancial stub mapped by its own path, in dev only.

        Its own function, role and log group; it can read only the origin secret, so it cannot
        reach MoneyApi, money tables or the correlation key. No catch-all or cross-environment
        target: stg and prd have no such route at all.
        """
        stub_logs = logs.LogGroup(
            self,
            "DevStubLogs",
            log_group_name=f"/raad/{environment}/platform-stub",
            retention=log_retention(environment),
            removal_policy=RemovalPolicy.DESTROY,
        )
        stub = lambda_.Function(
            self,
            "DevStub",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.X86_64,
            handler="raad_platform.edge.stub.entry",
            code=code,
            memory_size=128,
            timeout=Duration.seconds(3),
            reserved_concurrent_executions=reserved_concurrency(self, environment, 2),
            log_group=stub_logs,
            role=_execution_role(self, "DevStubExecutionRole", stub_logs),
            environment={
                "ENVIRONMENT": environment,
                "ORIGIN_SECRET_ARN": origin_secret.secret_arn,
            },
        )
        _runtime_pin_exception(stub)
        origin_secret.grant_read(stub)
        for route in api.add_routes(
            path="/stub/v1/{proxy+}",
            methods=[apigwv2.HttpMethod.GET],
            integration=integrations.HttpLambdaIntegration("DevStubIntegration", stub),
        ):
            # Public, unauthenticated by design: it returns a fixed status document only.
            NagSuppressions.add_resource_suppressions(
                route,
                [
                    {
                        "id": "AwsSolutions-APIG4",
                        "reason": "Dev-only nonfinancial stub proving path-mapped extension (NFR13.10). It returns a fixed status document, checks the CloudFront origin credential in constant time, reads no token or user data and has no permission beyond reading the origin secret. Absent from stg and prd.",
                    }
                ],
                apply_to_children=True,
            )
