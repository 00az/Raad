# infrastructure specification — u2-money-service

Conversation language: English.

## Deployment

| Facet | Choice | Rationale |
|---|---|---|
| Compute model | Python3.12 MoneyApi and C2 consumer Lambdas, existing uv lock; API7s and dependency attempts<=1s including SDK retries | Preserve existing implementation path. |
| Networking topology | No VPC/NAT; TLS AWS_IAM Function URL, both invoke permissions restricted to environment edge role | Independent bearer verification remains mandatory. |
| Storage strategy | Three on-demand encrypted DynamoDB tables: Ledger, Transactions, WalletDirectory, same account/region | Atomic financial transaction without personal fields in Ledger. |
| Environments | dev/stg/prd in recorded account027863026273/us-east-1; verify actual identity before provisioning | Separate data/configuration/roles; never root deployment. |
| IaC | Existing Python CDK v2, stable logical IDs, assertions/nag and actual bundle checks | No manual console changes or destructive replacement. |
| Sizing | API concurrency20, consumer2; initial128MiB candidates, measured before adjustment; no provisioned concurrency | Include shared account headroom; no demonstrated capacity claim. |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---|---|---|---|
| Ledger DynamoDB | Database | Wallet/owner uniqueness, final outcomes, receipts/reference markers; no financial TTL | Sole financial adapter writes both wallet versions/sequences, canonical transfer, outcome and unique markers atomically. Final refusal is conditional; no durable reservation. |
| Transactions DynamoDB | Database | transferId primary key; senderWalletId/completedSortKey GSI and recipientWalletId/completedSortKey GSI; role ordinals | One immutable canonical row, no duplicate payload store. GSIs are eventual; strong canonical BatchGet and contiguous expected ordinals detect gaps. Query two streams limit+1 each,20 default/100 maximum; no scan. |
| WalletDirectory DynamoDB | Database | Unique holder/email keys plus immutable profile versions | Personal fields only here. Ensure version before opaque outcome reference; retain while referenced. Missing replay version=>safe unavailable/investigation, never another movement. |
| PITR/deletion controls | Recovery | All three stg/prd tables retained, deletion-protected and PITR-enabled; no money/outcome/profile TTL | Common restore instant alone is not coherence proof. Dev reset only explicit. |
| Function URL/Lambda | Compute/ingress | AWS_IAM, exact edge role; no public browser CORS | SigV4 plus original token independently verified. No anonymous permission. |
| EventBridge rule/SQS target | Event delivery | C2 source/type/environment checks; target max age86400s/retries185; rule/account-bound queue policy | Decouple delivery acceptance from processing success. |
| SQS workqueue/consumer | Queue | Encryption,4day retention,90s visibility, batch1/partial failures, consumer concurrency2 | Retry processing before original trusted producer occurredAt+24h deadline. At expiry copy durably to processing DLQ then acknowledge; retry if copy fails. Invalid payloads quarantine immediately. |
| SQS failure destinations | Queue | Separate delivery and processing DLQs, encrypted,14day retention; safety redrive maxReceiveCount1000 with visibility never below90s | Do not rely on Lambda async6h limits for24h delivery. Preserve eventId/deadline on redrive; receipt/idempotent setup prevents another credit. |
| SSM/Secrets Manager | Configuration | Environment C5 and secret references, separate cursor signing secret/key purpose | Cursor key overlap>=24h; correlation keys retained for logs. Extra service secret is outside U4 shared subtotal. |
| CloudWatch/SNS | Monitoring |14day dev/30day stg-prd logs; service alarms to U4 topic/jjii0@hotmail.com | Confirmation and actual delivery unverified; no personal dimensions. |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Edge/identity/C4/C5/correlation | U4 | U1/U2/U3 | Matching environment outputs; named configuration/secret reads and exact invoker role. |
| C2 bus | U4 | U2 | Producer only PutEvents; consumer rule/account-bound delivery; no transfer-completed event. |
| Alarm topic | U4 | U2 | Service-owned alarms publish to matching topic, no duplicate subscription. |

## Migration, Recovery and Release Gates

| Concern | Procedure |
|---|---|
| U1->U2 | Quiesce writes; preserve IDs/times/balances. Seed per-wallet ordinals/high-watermarks in existing C1 order, add GSIs/backfill and prove contiguous coverage before activating readers. Preserve old reference reads until verified; never invent historical U1 request outcomes. |
| Wallet setup | One opening100000halalas in every environment including prd, then Directory readiness; repair pending Directory without another credit. Receipt only after ready. |
| Recovery | Restore all three tables to new names at common selected instant. Reconcile opening credits/debits/balances/outcomes/references/ordinals/profile versions/receipts. Choose a coherent point within RPO or fail. Measure detection+restore+validation+cutover<=3h and committed work lost<=5min. No reset/adjustment to pass. |
| Cost | Compute/data/PITR/logs/queues/secrets are billed. Read U4 cost worksheet; current no-cost instruction blocks paid provisioning and asset publication. No eligibility/credits assumed. |
| Inputs | Actual edge role, verifier profile, service URL, bus ARN, secret ARNs, OIDC role and confirmed alarm channel; no fixture values substituted for live outputs. |

## Sources

U2 six NFR designs; Functional Design entities/spec/rules; C1/C2/C5; team practices. [EventBridge retries](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-rule-retry-policy.html) and [SQS consumer behavior](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html) describe separate delivery/processing failure domains.
