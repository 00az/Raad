# Security Design — U2 Money Service

Conversation language: English.

## Identity and Request Authorization

The public edge invokes a private-by-policy MoneyApi Lambda Function URL using `AWS_IAM`; only the environment's edge execution role receives the URL and invoke permissions. Lambda validates the mobile bearer token independently using the C5 issuer, audience, JWKS/verifier configuration, and environment. The handler derives `userId` only from the verified subject claim and rejects caller-supplied ownership identifiers. The platform rate limit and service token verification are separate defense layers.

Store the non-secret C5 verifier profile in environment-scoped SSM Parameter Store; resolve the parameter name from deployment configuration and cache the parsed profile briefly. Cache public signing keys only until their key expiry and refresh on an unknown key ID. A missing/invalid profile, failed key refresh, issuer/audience mismatch, or environment mismatch fails closed. Store correlation-signing material only in Secrets Manager, grant narrowly scoped `GetSecretValue`, and never return it to callers.

## Data Protection and Least Privilege

- Enforce HTTPS/TLS 1.2 or later at the public edge and signed IAM transport to the service URL.
- Encrypt the Ledger and WalletDirectory tables at rest with KMS-managed keys; enable point-in-time recovery in `stg` and `prd` as defined by the approved recovery targets.
- Give the Lambda role read/write access only to the two environment-specific tables, read access to its verifier parameter, and access to the single correlation secret. The event consumer receives only its event source and required table actions.
- Keep email and display name only in WalletDirectory. Logs, metrics, cursors, and transfer references contain no raw personal data. Do not put full payloads, token claims, or idempotency fingerprints in logs.
- Validate body size, normalized email, whole-halalas integers, cursor length and signature, idempotency key length, and supported C1 version before store operations.
- Return the C1 error schema with stable public codes; map internal AWS exceptions to safe 5xx responses without resource names or stack traces.

## Security Boundaries

The MoneyApi function URL is not a public browser API: the shared edge is its only caller. CORS is disabled unless a separately approved browser client requires it. Environment roles, parameters, keys, tables, and event sources are isolated; no cross-environment fallback is allowed. The MVP does not accept card/bank details or connect to real payment systems.

## Sources

`security-requirements.md`, `functional-spec.md`, `contract-summary.md` (C1, C2, C5), and `tech-stack-decisions.md` define identity, privacy, and boundaries. AWS documents that `AWS_IAM` Function URL callers need both `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction` and must sign requests with SigV4: [Lambda Function URL access control](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html), [Function URL invocation](https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html).
