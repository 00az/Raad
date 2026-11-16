# security design — u4-platform

Conversation language: English.

## Identity, transport and origin
Use environment-isolated Cognito user pool/public app client (no client secret), current native SDK flow and validated C3/C5 capability matrix P1–P13. JWT independently verified at edge and service; own-profile GetUser must match verified subject/verified email. Never assume OAuth userInfo scopes for SDK tokens.
CloudFront overwrites a per-environment Secrets Manager origin header for both mapped origins; edge checks it in constant time before private work. Function URL requires SigV4 and both invoke permissions restricted to edge role; original bearer preserved securely for service verification. Missing configuration/secrets fail closed, never fallback across environments.
Use external free DNS/custom ACM certificate exact hostname in us-east-1 with explicit >=TLS1.2 viewer policy, as U1 answered questions specify. Account control, nested validation record, CAA, issuance and actual protocol tests are provisioning gates. No domain purchase/Route53 zone. Free DNS is not zero AWS hosting cost.

## Measurable abuse policy
Design initial limits, to be validated at approved demo load: verified caller gets 30 recipient lookups/minute and 10 transfer attempts/minute; every send also consumes one lookup token. Strong conditional fixed-window counters keyed by environment/verified subject hash/operation in a platform-owned TTL store; server time, exact count, atomic combined send/lookup consumption. No PII counters or financial state. Counter unavailable =>safe503; limit =>C1 429 with remaining-window Retry-After. Denied attempts do not consume money/idempotency key. Test boundary bursts and another caller unaffected. Fixed-window boundary burst limitation is documented; not described as sliding protection.
Unauthenticated account actions cannot trust a claimed account header. Native Cognito public SDK operations require a user-pool-associated regional WAF, initial 100 account-operation requests per source IP per5minutes and separate300 general requests/IP/5minutes to avoid starving GetUser. Managed WAF rates are approximate coarse abuse defense, not exact per-account counters; provider throttling/lockout complements them. No username/email inspection/logging or promise of exact per-account throttling. Verify actual supported operations and C3 behavior; SDK ForbiddenException must map to safe localized throttling without invented Retry-After. If required C3 semantics cannot be met by selected flow, block acceptance rather than claim edge coverage of direct SDK calls.
WAF/monitoring resources may incur cost and are design only until cost approval; user has authorized no paid provisioning. AWS documents native SDK WAF coverage: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html .

## Encryption, privacy and delivery
Encrypt persistent stores/secrets/logs at rest; per-environment roles and runtime-only secret references. C4/verifier output contains no secrets. Disable raw WAF request sampling/body/authorization/query logging; allowlist bounded safe signals. Identity attributes only email/displayName and required opaque IDs. Retain strict typing/lint/audit/secret scan, actual CDK synth/bundle/cdk-nag and >=80% platform line coverage; other-engineer PR approval before merge.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
