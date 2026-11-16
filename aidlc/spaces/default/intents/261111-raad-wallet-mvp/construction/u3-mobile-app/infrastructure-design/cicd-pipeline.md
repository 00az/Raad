# cicd pipeline — u3-mobile-app

Conversation language: English.

## Pipeline Flow

1. PR runs pinned Flutter dependencies, format, analyze, pin/hash/client generation checks and unit/widget/contract tests with >=80% line coverage. Tests cover money boundaries, account isolation, offline, pending intent and ar/en states. Other engineer approves; squash merge to protected main.
2. Build dev flavor with actual validated C4; record source, contract, backend revision and artifact digest. Linux can build Android; iOS requires macOS/Xcode/CocoaPods. Local existing tools may run without a paid distribution account.
3. Run iOS and Android integration suites against real dev with independent initialized fixture pairs; API/fake journeys recorded separately. Live verification requires U4 deployment/cost clearance and provider capability proof. No credentials in test output or shell arguments.
4. Complete manual VoiceOver/TalkBack, keyboard/switch, 320dp/200% text, RTL/LTR and Arabic wording checks. Upload to existing TestFlight/Play internal channels only when authorized and available without an unauthorized purchase.
5. Promote source revision after dev smoke to stg; build each environment flavor once with its own C4, since API/issuer differ. Store digest for each flavor. Prd requires human approval after stg checks; no public store release.

| Stage | Gate |
|---|---|
| PR | Full local/CI parity, coverage, client pin, second engineer |
| Device acceptance | Both platforms, ar/en and independent real dev fixtures |
| Distribution | Existing account/signing access, cost authorization where needed |
| Prd | Passed stg and named human approval |

## Rollback and Secrets

Rebuild the last known-good compatible source for the affected flavor with a new build number, validate its C4/client pin and rerun smoke before internal release. Never restore an old token/account cache across users. Use protected CI signing credentials and provider-specific limited upload credentials; no AWS keys or private fixture data in app assets. GitHub OIDC is needed only for explicitly scoped AWS configuration/fixture reads, not direct database access.

## Sources

U3 infrastructure-specification, monitoring-design and six NFR designs; C1/C3/C4 and team deployment practices. No build upload or purchase is performed by this document.
