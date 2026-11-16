# security design — u2-money-service

Conversation language: English.

## Identity and authorization
CloudFront overwrites the environment origin secret on both API origins. Edge verifies it in constant time before any authentication/forwarding; direct API Gateway access without the secret fails closed. Edge and MoneyApi independently verify the original bearer token and environment. SigV4 authenticates the edge to the AWS_IAM Function URL, with both InvokeFunctionUrl and InvokeFunction permissions restricted to that role. Preserve the original bearer in the protected internal envelope; caller-supplied ownership is never authoritative. Cognito SDK access tokens use independently verified subject plus bounded GetUser, matching subject and verified email; OAuth userInfo-only scope assumptions are superseded.

## Data protection and privacy
Ledger owns balances, request outcomes and receipts. Transactions stores exactly one canonical transfer row, with sender/recipient history indexes. WalletDirectory alone owns email/name and immutable WalletHolderProfileVersion records. Ensure a durable profile version before committing its opaque reference with a final Ledger result; replay resolves that exact authorized version, never today's mutable profile. Missing/corrupt referenced versions fail unavailable for investigation. Retain versions while referenced outcomes survive; do not put profile payloads in Ledger or a second history store.
All three tables are encrypted at rest; IAM scopes each environment's adapters to required tables/actions only. Ledger transaction adapter is the sole financial writer. Secrets Manager holds origin/correlation secrets, SSM the nonsecret C5 profile. No secrets in source, logs, artifacts or output.

## Transport and input controls
TLS minimum 1.2 at the public boundary requires the controlled-free-subdomain/custom-certificate path in U1 questions; default CloudFront certificate is not sufficient evidence. Validate bounded bodies, whole-halalas integer schema, normalized email, cursor/key/version before persistence. No money API CORS allowance without a browser consumer. Signed cursors bind caller, environment, snapshot, sort, limit, expiry and next expected history ordinal, with no personal profile. Safe errors disclose no internals.
Verify forged identity, direct-origin bypass, cross-user cursor, secret rotation and recognizable-PII scans before acceptance.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design/functional-spec.md and rules.md; shared inception/contract-design/contract-summary.md and domain-design/components.md; U1 nfr-design/nfr-design-questions.md (free DNS decision b8664859). No target is lowered by this revision.
