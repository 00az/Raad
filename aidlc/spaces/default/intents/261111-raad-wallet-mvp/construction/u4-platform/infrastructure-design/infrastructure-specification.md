# infrastructure specification — u4-platform

Conversation language: English.

## Deployment

| Facet | Choice | Rationale |
|---|---|---|
| Compute model | Existing Python 3.12 Lambda/CDK platform; edge, confirmation publisher and telemetry processor | Preserve the serverless implementation path; no EC2/ECS. |
| Networking topology | CloudFront -> API Gateway HTTP API -> edge Lambda -> IAM Function URL; no VPC/NAT | The origin credential closes direct API Gateway bypass. Money resources remain U2-owned. |
| Storage strategy | PlatformRateWindows on-demand DynamoDB table; encrypted telemetry stream/logs; SSM configuration and Secrets Manager | Counters and telemetry contain no financial state. |
| Environments | Separate dev/stg/prd resources in recorded account 027863026273, us-east-1 | Verify actual identity and quotas before deployment; never deploy as root. |
| IaC approach | Existing Python CDK v2 in infrastructure/, stable construct IDs, assertions and cdk-nag | Do not replace persistent resources through a rename. |
| Resource sizing | Edge 128 MiB/9s/concurrency20; telemetry 128 MiB/20s/concurrency2; publisher 128 MiB/3s/concurrency2; one provisioned Kinesis shard/24h | Initial candidates, subject to actual quota headroom and demo load; no provisioned Lambda concurrency. |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---|---|---|---|
| External free DNS | DNS | Candidate Dynu-controlled hostname; api.dev.<reserved-hostname> | Account control and availability pending. Count every environment, landing alias and certificate-validation node against free limits. Start with dev; no paid upgrade if later environments do not fit. |
| ACM / CloudFront | CDN/TLS | Exact non-exportable ACM certificate in us-east-1, retained validation CNAME, alternate hostname and TLSv1.2_2021 policy or stricter verified equivalent | API CNAME points to actual distribution. No Route53 hosted zone. Default cloudfront.net certificate does not prove the minimum TLS version. |
| API Gateway HTTP API | Ingress | Existing /money routes, HTTPS origin, Lambda integration timeout10s above edge9s | Use generated AWS hostname as origin; no separate API custom domain required. Disable authenticated caching and preserve C1 headers/body/query. |
| Edge / origin credential | Security/routing | CloudFront overwrites the environment secret header on both origins; edge checks in constant time before private work | Missing/counterfeit credential fails closed. Independent JWT verification, protected original bearer forwarding and SigV4 to service. Edge has no money-table grants. |
| CloudFront WAF | Firewall | Common managed group plus coarse IP rule; sampling disabled | Two rule entries in illustrative estimate. Approximate WAF rates do not implement exact verified-caller limits. |
| PlatformRateWindows | Database | HMAC subject/operation/server-minute keys, count/version/expiry; TTL cleanup after2h | Exact conditional transaction consumes lookup30/min and send10/min together. Shared read/setup/history limit60/min bounds backend profile calls. Counter failure503; quota429 plus remaining-window Retry-After; no financial key consumed. |
| Cognito | Identity | Environment pool and public app client without secret; native SDK SRP flow; email verification and required name; existing password policy | Independently verify RS256, issuer, client_id, token_use, expiry and subject. Bounded GetUser must match subject/verified email. No identity pool or paid access-token customization assumed. |
| Cognito regional WAF | Firewall | Account operations100/IP/5min; general non-profile operations300/IP/5min. Explicitly exclude GetUser from both buckets | Use actual provider operation metadata. This prevents backend egress from sharing a small IP bucket across users; it does not create an IAM allowlist. |
| GetUser capacity | Provider dependency | Token authorization and provider quota; service calls additionally bounded by caller60/min, concurrency20 and1s deadline | Public provider quota remains a shared residual risk. Mixed load must prove two callers sharing backend egress remain usable during an account-operation burst. Unknown operation classification or failed isolation blocks release. No personal-profile cache introduced. |
| Confirmation publisher / EventBridge | Event producer/bus | Post-confirmation signup source only; emit schema-valid C2 UserConfirmed with environment, opaque eventId and trusted UTC occurredAt | Exclude password-reset confirmation. Catch publication failure and return the Cognito event unchanged; PUT remains the repair path. U2 owns durable SQS consumption. |
| SSM / Secrets Manager | Configuration | C4/C5, edge role and service URL; environment origin/correlation secrets; designated fixture secret | No secret in C4 or client assets. Cursor secret belongs to U2. Runtime roles read named references only. |
| Kinesis / telemetry / Scheduler | Monitoring | Encrypted one-shard stream,24h; seven safe CloudFront fields at100%; five-minute aggregation two minutes after boundary | Collector cannot read money tables/invoke money. Best-effort delivery cannot establish a complete SLI by itself. |
| CloudWatch / SNS | Monitoring | Per-environment dashboard/alarms;14day dev/30day stg-prd logs; operational email jjii0@hotmail.com | Subscription confirmation and actual stg breach/recovery delivery remain unverified. No notifications sent by this design. |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Pool/client and C4/C5 | U4/Raad | U1/U2/U3 | Versioned, non-secret outputs from matching environment; independent verifiers. |
| API mapping/certificate/edge | U4/Raad | U1/U2/U3 | Approved prefixes and targets only; new dev stub path must not change MoneyService. |
| C2 event bus | U4/Raad | U2 | Source-bound producer/consumer; queue policy restricted to rule ARN/account. |
| Correlation secret and alarm topic | U4/Raad | U1/U2 | Named read/publish roles; no client exposure. |
| Landing hosting | U5/RaadWeb | U5 | Separate distribution/bucket; no money integration. |

## Capability and Provisioning Gates

| Check | Required evidence | Current state |
|---|---|---|
| P1/P2/P13 | Actual SDK token and public PUT/GET; profile-subject binding and wrong-token/environment tests | Local evidence exists; live unverified. |
| P7 resend invalidation | Issue a new code, prove old code refused and new code accepted using a controlled mailbox without logging codes | GAP: documentation does not prove old-code invalidation. AWS lists no pre-confirmation trigger; custom messages alter delivery, post-confirmation is too late. If native behavior fails, block identity release and revisit C3 with the person; do not invent a trigger fallback. |
| Other P1–P13 behavior | Record expiry/reset/resend/renew/sign-out/idle results and supported fallbacks | Unverified; no complete C3 release claim. |
| Regional WAF/GetUser | Actual operation classification and mixed-load isolation at ten active users | Proposed remedy, not measured proof. |
| DNS/TLS | Free account quota, actual reserved hostname, underscore CNAME/CAA resolution, ISSUED certificate and TLS1.0/1.1 rejection/TLS1.2/1.3 success | Pending; no placeholder deployment. |
| Cost | Existing instruction requires no cost | No paid resource creation, asset publication, subscription or enrollment authorized. Local Code Generation/checks can proceed. |

## Cost Worksheet

Illustrative pay-as-you-go list-price subtotal checked2026-11-16,730h/month, without assumed free allowances, credits, discounts or tax. This is not a complete bill forecast or spending authorization. Account free-plan/credit eligibility, balance and expiration are unverified.

| Item | Calculation USD | Illustrative subtotal |
|---|---|---|
| CloudFront and regional WAF | 2 ACLs*5 +4 rule entries*1 | 14.00/environment/month |
| Native public-latency stream | 1 provisioned shard*730h*0.015 | 10.95/environment/month |
| Shared secrets | 3(origin, correlation, test fixture)*0.40 | 1.20/environment/month |
| Listed items | Decimal script sum | 26.15/environment/month;78.45 for three environments |
| U1 dev basic path | 1 ACL+2 rules+stream+3 secrets | 19.15/month before other charges |
| Exclusions | Compute/API/CDN requests and egress, WAF requests, Kinesis puts/realtime logs, DynamoDB/PITR, cursor secret, CloudWatch logs/metrics/queries/alarms/dashboard, SNS/events/queues/KMS/paid SSM, CI/artifacts/tax | Additional usage-dependent costs |
| Mobile distribution | Apple TestFlight developer membership99USD/year; Play Console registration25USD, subject to existing membership/eligible waivers | No purchase or enrollment |
| DNS/certificate | Free controlled subdomain conditional; non-exportable integrated ACM certificate has no additional certificate fee | Hosting resources still billed |

Sources: [WAF](https://aws.amazon.com/waf/pricing/), [Kinesis](https://aws.amazon.com/kinesis/data-streams/pricing/), [Secrets Manager](https://aws.amazon.com/secrets-manager/pricing/), [Apple](https://developer.apple.com/programs/), [Google](https://support.google.com/googleplay/android-developer/answer/6112435), [ACM](https://aws.amazon.com/certificate-manager/pricing/). No actual billing API queried.

## Code Generation Handoff

| Area | Required change |
|---|---|
| External DNS | Remove mandatory hostedZoneId gate for a custom certificate; support external DNS without Route53 resources. Keep generated API origin; preserve minimum TLS with certificate. |
| Native SDK | Remove stale userInfo-only wording and unnecessary hosted-UI requirement where native flow does not need it; retain token/profile compatibility. |
| Limits/events/monitoring | Implement exact rate counters, regional operation rules excluding GetUser, event producer/buffer and full alarm windows. These are not claimed implemented. |
| Resource safety | Review actual cdk diff; preserve logical IDs, data, compatible rollback and coordinated secret rotation. No deployment from this stage. |

## Sources

U4 six NFR designs; C2–C5; domain components; existing infrastructure/raad_platform/stacks.py; team practices; U1 answered free-DNS question, message b8664859. [Cognito WAF](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html) documents operation metadata and native SDK coverage. [Trigger documentation](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-working-with-lambda-triggers.html) does not supply the previously proposed pre-confirmation fallback.
