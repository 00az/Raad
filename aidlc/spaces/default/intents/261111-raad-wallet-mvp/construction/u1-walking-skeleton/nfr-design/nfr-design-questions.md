# NFR Design Questions — Public TLS Boundary

Conversation language: English.

## Q1. Hostname versus required endpoint TLS policy

The person selected an AWS-assigned cloudfront.net hostname to avoid domain registration. Existing NFR2.1 and the shared C1/C3/C5 transport requirements require TLS 1.2 or later. AWS currently documents that CloudFront's default certificate automatically uses the TLSv1 security policy regardless of MinimumProtocolVersion. Modern clients negotiating TLS 1.2/1.3 does not prove that the endpoint refuses older protocols. Do not mark this requirement satisfied, silently weaken it, or deploy the wallet claiming conformance.

- A. Investigate a free custom subdomain with sufficient DNS control to validate a certificate, retaining CloudFront and the TLS 1.2 minimum. Do not register or purchase a paid domain. External provider availability and account/DNS control must be verified before selection.
- B. Retain the cloudfront.net hostname in the draft and leave live deployment blocked until a compatible controlled domain/certificate is available. Continue unrelated design topics, but do not report NFR Design fully resolved.
- X. Other (please specify)

[Answer]: A — person selected option 1 (message b8664859). Investigate a free controlled subdomain; no purchase. Dynu publishes free third-level hostnames, subdomains and CNAME records. Use external DNS plus a DNS-validated ACM certificate for the exact API hostname as the design path. Selection remains conditional on account control, hostname availability, nested underscore CNAME support, inherited CAA compatibility and successful public validation. Actual reservation/issuance belongs to provisioning; no hostname is claimed registered here. If these checks fail, deployment stays blocked and another free provider is evaluated without weakening TLS.

## Free DNS design and provisioning handoff

- Candidate provider: Dynu. Published free limit: four hostnames/subdomains; budget actual service and validation nodes against the account's limits before registration. No paid upgrade is authorized.
- API hostname shape: `api.dev.<reserved-free-hostname>`; exact suffix and availability are not yet established. Do not substitute this notation into a live deployment.
- Create the exact ACM-provided `_token.api.dev...` CNAME to its `_token.acm-validations.aws` value, preserving the validation record for renewal. Obtain the non-exportable service-integrated certificate in us-east-1, attach it to CloudFront, use an explicit TLS 1.2 minimum policy, then create the API CNAME to the actual distribution hostname. No Route 53 hosted zone is needed.
- Require public authoritative/recursive DNS evidence and actual ACM ISSUED status; verify TLS 1.0/1.1 rejection and 1.2/1.3 success against the deployed hostname. Disable dynamic-IP updates/wildcard aliases that could replace these CNAMEs; no A/AAAA record may coexist at the API node.
- The provider's published capabilities establish design feasibility, not account entitlement or deployment proof. Shared-domain dependency and provider account continuity enter the operational risk register. No external DNS account has been created and no credentials requested in chat.
- Sources checked 2026-11-16: https://www.dynu.com/en-US/FAQ/Dynamic-DNS-Service ; https://www.dynu.com/Resources/API/Documentation ; https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CNAMEs.html .

## Evidence

- AWS distribution settings: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesGeneral.html
- AWS ViewerCertificate API: https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_ViewerCertificate.html
- `nfr-requirements/security-requirements.md`: NFR2.1 and explicit default-certificate compatibility handoff.
- `inception/contract-design/contract-summary.md`: minimum TLS requirement.

## Independent design analysis completed

Existing U2 NFR Design still describes two tables and a cross-component atomic wallet setup, whereas current Functional Design requires the dedicated Transactions table and wallet-then-directory repair. It also puts amount refusal before unknown-recipient refusal and attributes balance writes directly to MoneyApi. These stale statements must be corrected when the design artifacts are regenerated; do not copy them into Code Generation.

The U2 paging solution must prove that eventual history indexes cannot omit records in a cursor snapshot; bounded contiguous per-wallet completion ordinals and fail-closed gap detection are a candidate for evaluation against the unchanged C1 sort/snapshot contract. Multi-table restore must validate cross-table transaction consistency; merely choosing a common PITR timestamp does not establish the selected 5-minute RPO or 3-hour RTO. These are design work items, not verified solutions or additional human requirements.
