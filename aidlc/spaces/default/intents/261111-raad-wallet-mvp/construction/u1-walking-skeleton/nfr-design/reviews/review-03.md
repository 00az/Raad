## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-16T12:42:54Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

**Prior findings**

| ID | Now | Severity | Note |
|---|---|---|---|

**New findings**

| Severity | Location | Finding | Required action |
|---|---|---|---|
| Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u4-platform/nfr-design/security-design.md > Measurable abuse policy | The proposed general 300 requests/source-IP/5-minute Cognito rule also covers GetUser. MoneyApi performs that lookup using users' tokens from service execution environments, so the provider sees shared backend egress rather than each mobile caller's address. The design does not separate these trusted backend profile calls from the general IP bucket or show an aggregate egress budget. Consequently legitimate users can exhaust a shared bucket and block other users' profile-dependent money requests; 300 per five minutes is only one request/second per bucket, which can be exceeded by the specified multi-operation ten-active-user journey. Merely separating account-operation and general rules does not establish the stated protection against starving GetUser. This is a design inference, not a measured throttling event. | Classify GetUser explicitly in the regional WAF policy and size/protect its traffic against the aggregate backend-egress workload, while retaining appropriate abuse protection for publicly callable operations. Do not assume Lambda egress is unique per user. Add a mixed-load case with two users sharing service egress, profile calls and an account-operation burst; prove the unaffected user's money path remains usable. Retain the existing release block if the selected provider policy cannot meet the required isolation. |

### Validation Tool Results

| Check | Result | Interpretation |
|---|---|---|
| Read-only detailed-NFR/trace validation | U1: 40 requirements/40 rows; U2: 44/44; U3: 17/17; U4: 19/19; U5: 12/12. All 132 required detailed IDs are represented; no duplicate coverage IDs, missing/extra IDs or absent referenced Markdown target files were found. All rows currently say OK. | Structural design coverage passes. OK means a proposed design mapping, not an executed capability, recovery or load result; the new policy concern qualifies U4's semantic coverage. |
| U2 transaction/profile/setup review | Three tables retain separate logical ownership. Final outcomes commit conditionally with atomic financial success; no durable pending key. Directory profile versions exist before their opaque references are committed. Wallet setup remains wallet-then-directory with safe repair. | Preserves the money/privacy boundaries without a second transfer-history store. Missing profile versions fail safely rather than trigger another movement. |
| U2 paging and migration review | Per-wallet sequence/high-watermark is captured strongly; both role indexes are bounded and merged in C1 order; canonical candidates are strongly read; contiguous expected ordinals detect missing projections. New completion keys must exceed both participating wallets' prior keys. Missing/lagging data causes bounded retry then unavailable, not partial success. Migration quiesces writes and seeds historical ordinals before reader cutover. | The design addresses eventual-index omissions and snapshot stability rather than assuming GSI consistency. Code/store tests must still prove ties, opposing concurrent transfers, lag, exhaustion and cursor boundaries. |
| Native Cognito WAF capability documentation | AWS explicitly lists InitiateAuth, RespondToAuthChallenge and GetUser among inspected public API operations; operation-identifying headers are available, PII matching is unavailable, and SDK blocks surface as ForbiddenException. | Confirms that native SDK coverage is a valid design path and that GetUser is in scope of the shared-IP concern. No actual regional WAF association or rule behavior was tested. |
| Application/live/provider/DNS/ACM/TLS/cost checks | Not run in this isolated design review. | No DNS account control, hostname reservation, certificate issuance, protocol conformance, paid provisioning, provider compatibility, origin delivery, deployment or load acceptance is certified. |

### Evidence and Design Boundaries

The Cognito policy assessment uses [AWS's user-pool WAF documentation](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-waf.html), together with the selected backend GetUser path in U1/U2 security design. The general-rule threshold is explicitly an initial proposal subject to demo-load validation, which is appropriate; the missing backend-egress classification should be resolved in that policy before implementation rather than discovered through a blocked wallet journey.

The controlled free-DNS/custom-ACM path is appropriately conditional: account entitlement, exact hostname, nested validation CNAME support, inherited CAA, authoritative/recursive resolution, issued certificate and TLS protocol probes remain provisioning gates. The design retains the TLS 1.2 minimum, prohibits a paid-domain/hosted-zone substitution, counts service and validation nodes against provider limits and acknowledges provider continuity risk. It neither claims free hosting nor authorizes paid AWS resources; WAF/monitoring cost approval remains explicit.

U2 restore uses a common selected instant followed by cross-table balance/outcome/profile/ordinal reconciliation, rather than treating PITR timestamps as an atomicity proof. RPO at most five minutes, RTO at most three hours and 99.5% production monthly availability remain unchanged and require an actual timed drill and observation coverage. U3 preserves protected account/environment-bound intents, integer halalas, explicit replay capability, epoch isolation and ar/en accessibility. A8 remains proposed. U5 stays static, bilingual and isolated from money/auth flows, with actual copy/accessibility/HTTPS evidence still owed.

Shared observability separates traffic and idle synthetic coverage, counts dependency failures, labels incomplete public observations and retains privacy-safe correlation rather than adding personal dimensions. Existing settled main-workflow findings are not regraded in this isolated pass; no new severity increase was established for those findings. No reviewed artifact, source file, diary or lifecycle record was changed.

### Summary

The proposed patterns and bounded paging/recovery design are sufficiently developed to inform Infrastructure Design. One Major concern remains for the person to weigh: the regional Cognito general-IP rule needs an explicit backend GetUser traffic budget and isolation test. All implementation, provisioning and live acceptance claims remain unverified.
