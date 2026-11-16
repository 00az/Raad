# infrastructure specification — u3-mobile-app

Conversation language: English.

## Deployment

| Facet | Choice | Rationale |
|---|---|---|
| Compute model | Existing pinned Flutter app on iOS and Android; no mobile-owned AWS server | U3 owns presentation and device state. |
| Networking topology | Native Cognito SDK for C3, HTTPS public CloudFront API for C1, C4 validated at build time | No AWS identity pool, embedded AWS keys or direct database access. |
| Storage strategy | Platform secure storage for tokens and pending intent; account/environment-scoped snapshots; language preference separately | Clear private state on sign-out; reject late responses from old session epochs. |
| Environments | Separate dev/stg/prd flavors, actual C4 issuer/client/API values | Missing or cross-environment inputs fail the build. Never use the example JSON for live proof. |
| IaC approach | Consume U4 versioned outputs; app build/release configuration in RaadMobile | U3 creates no cloud stacks. |
| Resource sizing | One in-flight operation per control, bounded history pages 20 default/100 maximum; 15-second total request deadline | No eager all-history fetch or queued financial writes. |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---|---|---|---|
| iOS Keychain / Android protected storage | Device storage | Existing secure-storage plugin, account/environment keys; passwords/codes never persisted | Persist immutable key/recipient/amount before send; failure to persist blocks send. |
| Flutter build tools | Build | Existing pinned SDK/pubspec.lock; generated Dart client from exact C1 pin | No runtime/library upgrades inferred from this design. |
| C4 configuration | Configuration | Validated non-secret file generated from actual U4 outputs per flavor | Do not embed origin/correlation secrets or test passwords. |
| TestFlight / Play internal testing | Distribution | Existing team-selected channels, signing keys protected in CI; no new enrollment | Apple/Google account fees may apply; no-cost instruction blocks purchases/uploads that incur cost. |
| Local simulators / emulators | Verification | iOS and Android contract-fake and real-dev suites recorded separately | Local tests can continue; fake journeys are not AWS verification. |

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Cognito C3 / C4 and public C1 URL | U4 with U2 API | U3 | No provider admin privileges; native tokens independently verified server-side. |

## Release Gates and Cost

| Concern | Gate |
|---|---|
| ar/en and accessibility | Complete catalogs, correct RTL/LTR isolation, 320dp and 200% text, keyboard/switch access and actual VoiceOver/TalkBack evidence on both platforms; native Arabic wording review. A8 Western digits remains proposed. |
| Session/intent | Account switch, sign-out, crash/restart, lost response, double tap, offline and locale switch preserve ownership and immutable intent. U1 uncertainty blocks resubmit; full U2 alone enables explicit same-key replay. |
| Provider | U4 P1–P13 and P7 code invalidation remain mandatory; no client-side check can enforce invalidation at Cognito. |
| Distribution | Check existing paid membership/waiver before release. No Apple/Google purchase authorized. Simulator builds are a separate free local path, not tester distribution. |
| Money/time | Integer halalas and authoritative balance; UTC instants displayed locally; no locale/DST change alters amount, key or server order. |

## Sources

U3 six NFR designs and Functional Design, shared C1/C3/C4, team mobile ownership and deployment practices; U4 cost worksheet. No new application implementation or cloud resource is created.
