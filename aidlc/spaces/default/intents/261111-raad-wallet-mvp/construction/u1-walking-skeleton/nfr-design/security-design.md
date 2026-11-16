# Security Design: U1 Walking Skeleton

Conversation language: English.

## S1 — Identity and authorization

MobileApp sends the original access token to the public edge. The edge strips spoofed identity headers and independently verifies the token before forwarding it unchanged. MoneyApi independently verifies signature, issuer, environment-specific audience binding, expiry, not-before when present, access-token marker and RS256 against the immutable C5 configuration. It takes the caller only from the verified sub. Local AuthGuard checks improve the UI but grant no server authority.

Validate C5 configuration on deployment/startup: closed schema, version, environment, issuer, audience/claim binding, algorithm, key-discovery URI and profile source. A missing or mismatched value prevents service readiness. Never discover an issuer, algorithm or key URL from an untrusted token. Keys are accepted only from the configured HTTPS source; reject redirects to unconfigured destinations. The selected provider is Cognito with the existing native SDK flow; actual environment hosts, issuer and audience are Infrastructure Design outputs.

Wallet and history access resolve the caller's wallet from sub, never a source-wallet ID from the body, URL or identity header. An operation cannot select someone else's history. Request validation follows C1's exact shape, normalization order and field names. Snake_case domain attributes remain internal; C1 uses amountHalalas and the Idempotency-Key header. Validate requests and provider emissions against the pinned OpenAPI; generated consumers tolerate unknown response fields under C1. The U1 pin is explicitly a partial pre-release without the completed U2 replay guarantee.

## S2 — Bounded signing-key cache

Each verification layer may hold public signing keys in memory for at most 360 minutes from its last successful fetch, using a monotonic age. Coalesce concurrent refreshes within an execution environment; an unknown kid causes at most one refresh for that verification and no more than one unknown-kid refresh per 60 seconds per cache instance. Do not invent a distributed cache or a global cache-coordination service. Infrastructure Design must account for multiple edge/service instances when evaluating refresh traffic.

A known key in an unexpired cache continues to authorize otherwise valid tokens during discovery failure. With no usable cached key and discovery unavailable, return 503 TOKEN_VERIFIER_UNAVAILABLE. A successful refresh that still lacks the key yields 401 AUTHENTICATION_REQUIRED. A refresh cooldown with an unexpired usable set that lacks the requested key yields 401; an absent/expired set yields 503 rather than pretending discovery succeeded. Never use an expired key set to improve availability. New and retiring keys overlap for the greater of 360 minutes and the access-token lifetime when rotation is under platform control. Provider-controlled withdrawal and session behavior remain C5/C3 obligations.

## S3 — Profile and money boundaries

MoneyApi reads email and display name only from the C5 configured verified access-token claims or the provider's own-profile endpoint using that access token. The Cognito native SDK flow uses bounded GetUser compatible with its token scope; OAuth userInfo-only scope requirements do not apply. Independently validate the access token and require matching returned subject and verified email. In the endpoint case, require the returned subject to equal the verified caller. Do not trust an ID token presented as an access token, an email in a wallet-setup body or a recipient's asserted user ID. Infrastructure Design runs C3 P1, P2 and P13 on dev and records the selected source/fallback.

WalletDirectory owns the only personal attributes in the money service: email and display name. Ledger holds opaque IDs, integer halalas and transfer data. Each Transactions row is keyed by transferId, holds both wallet references and contains no email, display name, credential or token. Use separate data-access ports and write privileges where the physical store supports them; MoneyApi invokes Ledger operations rather than directly changing balances. Only Ledger's transaction adapter may insert completed transfer rows as part of the balance transaction; existing rows cannot be updated or deleted by ordinary request handling. A shared database product preserves the dedicated Transactions table and component ownership boundaries.

The setup path satisfies C1's idempotent PUT /wallet and wallet-then-holder sequence. Readiness checks repair a missing holder entry for an existing wallet without another credit; verified profile values remain authoritative. No request can substitute its own setup email or holder ID. Do not collect bank details, card data, identity documents or extra personal attributes. Funds stay simulated; SAR is the sole currency.

## S4 — Encryption, credentials and logs

Require TLS 1.2 or later on app, sign-in, public API and service/dependency connections. The default CloudFront certificate cannot establish this endpoint minimum. The answered free-DNS path in nfr-design-questions.md requires a controlled hostname, DNS-validated custom ACM certificate in us-east-1 and explicit TLS1.2 minimum policy. Actual account control, records, issuance and protocol tests remain provisioning gates; no purchase is authorized. Verify certificates and hostnames; reject insecure endpoint configuration. Persistent wallet, transfer, holder, secret and operational stores require encryption at rest using the selected AWS-managed key infrastructure. Infrastructure Design maps these requirements to actual resources and demonstrates encryption and environment isolation.

Access/refresh tokens use phone secure storage; passwords stay only in transient sign-in input and are cleared after use. Test credentials come from the selected secrets store at execution time. Neither command arguments, CI output nor error objects may echo them. Laptop access and CI access follow the affirmed short-lived authentication practices. Pin dependencies and run secret scanning, dependency audit, strict typing, linting and CDK security checks under the existing test requirements.

Structured logs use an allowlist: UTC timestamp, environment, component, bounded operation, safe result/error code, duration and correlation ID. Opaque identifiers are permitted where useful but never become metric dimensions. Do not log request/response bodies, authorization headers, SDK exception payloads, email, display name, password or codes. Sanitize CR/LF in allowed text and emit safe codes rather than raw exceptions. The observability design also handles identifiers the caller controls.

## S5 — API boundary and disclosure

Every response carries the same valid X-Correlation-Id selected at the edge; errors carry matching correlationId. Preserve a valid input matching C5, otherwise generate one. Errors use C1 status/code/message/optional fieldErrors; exception stacks and internal names stay out of responses. CloudFront overwrites an environment origin-secret header on both mapped origins. The edge checks it in constant time before private work; direct API Gateway requests with absent/counterfeit credentials fail closed. Secret rotation and header overwrite require deployed proof. The basic U1 firewall protects the public API and produces safe 403/429/503 behavior where configured. Complete per-caller rate policies remain U4 work, with U2 integration. Infrastructure Design must prove the selected edge can implement the C5 error and verification behavior; product defaults are not assumed to match it.

No browser session or cookie-based wallet authentication is introduced. The Flutter API uses bearer authorization and no ambient browser credential. A restrictive API browser-origin policy can be configured, but CORS is not authorization. No new web wallet or browser-specific XSS/CSRF subsystem is added to U1.

## S6 — Verification

- Test missing, malformed, expired, incorrectly signed, wrong-environment, wrong-algorithm and wrong-token-type credentials at both verification boundaries. Test issuer/audience mismatch, configuration failure, unknown kid, refresh cooldown, rotation, and discovery failure with/without a valid cache.
- Test spoofed identity fields/headers, another user's wallet/history access, profile-subject mismatch and strict C1 request/response validation. Safe server errors disclose neither profile nor store detail.
- Scan successful, refused, throttled, timeout and startup logs, metrics and delivered alarms using recognizable synthetic credential/profile values. Confirm at-rest encryption and TLS in deployed-resource evidence.
- Check secure storage and generated-client pinning. No security test result is claimed until execution evidence exists.

## Sources

- construction/u1-walking-skeleton/nfr-requirements/security-requirements.md: NFR1.1–1.4, NFR2.1–2.3, NFR10.1, NFR11.1, NFR12.1 and NFR14.1.
- construction/u1-walking-skeleton/nfr-requirements/tech-stack-decisions.md: NFR11.2 and NFR14.3–14.4; deferred provider/store/edge selections.
- construction/u1-walking-skeleton/functional-design/functional-spec.md and rules.md: owned-wallet behavior, explicit setup repair and C1 public mapping.
- inception/contract-design/contract-summary.md: C1 validation/disclosure and C3/C5 identity, profile, cache and edge contracts.
- inception/domain-design/components.md: MoneyApi, Ledger and WalletDirectory ownership.
- aidlc/spaces/default/memory/team.md and project.md: simulated funds, whole halalas, short-lived credentials and no personal-data logging.
