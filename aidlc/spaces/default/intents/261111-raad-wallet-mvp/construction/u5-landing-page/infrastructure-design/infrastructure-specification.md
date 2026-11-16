# infrastructure specification — u5-landing-page

Conversation language: English.

## Deployment

| Facet | Choice | Rationale |
|---|---|---|
| Compute model | Static HTML/CSS, separate ar/en documents in RaadWeb | No JavaScript required for introduction/language/contact navigation. |
| Networking topology | CloudFront HTTPS to private S3 REST origin with OAC | No public S3 website bucket, server, database or API calls. |
| Storage strategy | Versioned static artifacts in private encrypted S3, block all public access | Preserve last-known-good release for rollback. |
| Environments | Isolated dev/stg/prd buckets/distributions, versioned manifest and actual URLs | Same source; no shared visitor state. |
| IaC | Python CDK in RaadWeb, tested by assertions and cdk-nag | No console publication or new hosting service. |
| Resource sizing | Static CDN/cache only, no dedicated compute | Demo 100 users/about 10 active verified by fetch smoke. |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---|---|---|---|
| S3 | Object store | Block public access; encryption at rest; versioning; no money/identity data | OAC read limited to exact distribution/account. Retain last-known-good artifact; no automatic destructive cleanup. |
| CloudFront | CDN | HTTPS only, local assets, HTML short cache/revalidate and versioned asset names; invalidate HTML after publish | Separate from wallet API; no authenticated caching issue introduced. |
| External DNS / ACM | DNS/TLS | Free controlled landing hostname, exact non-exportable certificate in us-east-1, TLS>=1.2 policy | Additional hostname/validation nodes count against free provider limits; no assumption all 3 environments fit. Publication blocked until reserved/issued/protocol proof. |
| Response headers | Security | CSP self, no executable inline code, frame-ancestors none, nosniff and HSTS after validated HTTPS | No analytics, cookies, visitor tracking, third-party fonts or external scripts. |
| GitHub Actions | Delivery | Static validation + real deployed ar/en smoke after each release | Runner/storage quota may incur cost; no paid plan authorized. |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Optional DNS account | Person/U4 configuration | U5 | Separate exact landing records; no API distribution/data permissions. |

## Content, Cost and Release Gates

| Concern | Required behavior |
|---|---|
| Contact | abdulaziz.alrubai@outlook.com only; LTR-isolated, visible/selectable, mailto does not claim delivery; operational alerts remain jjii0@hotmail.com. |
| Languages/accessibility | Complete ar/en copy/labels, semantic landmarks/skip link, focus, 320dp/200% reflow, keyboard/screen-reader and native Arabic review. |
| Distribution links | No invented TestFlight/store links; request access through public contact until supplied. |
| Privacy | No wallet/auth calls or forms collecting personal data; disable raw query/referrer/access request logging. |
| Cost | S3/CDN/requests/CI can be billed; free DNS/ACM alone does not make hosting free. No paid provisioning under current instruction. |
| Evidence | Both language URLs/assets on actual deployed host, TLS checks and rollback smoke; no parser-only result presented as browser evidence. |

## Sources

U5 six NFR designs and Functional Design; static hosting ownership in domain components and team practices; U4 DNS/cost handoff.
