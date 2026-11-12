# External Dependency Map: RAAD Digital Wallet MVP

Conversation language: English.

External dependencies are items outside the team's direct control that could block or delay a Bolt. Each row names the item, its owner, the lead time, the Bolt it blocks, and the fallback if it slips.

## Dependencies

| # | Dependency | Owner | Lead time | Blocks | Fallback if it slips |
|---|---|---|---|---|---|
| D1 | AWS account with IAM permissions for CDK deploys and GitHub Actions OIDC role | Engineer 1 | 1–2 days (assumed in progress) | Bolt 1 (first CDK deploy to `dev`) | No fallback — required before `dev` deploy. Start Bolt 1's CDK work locally; delay the first deploy until ready. |
| D2 | Apple Developer account and TestFlight configuration | Engineer 2 | 1–7 days depending on account status | Bolt 5 (iOS tester build) | Build the app and pass all local checks; delay TestFlight distribution until account is confirmed. `prd` deploy gates on testers receiving the build. |
| D3 | Google Play internal testing setup | Engineer 2 | 1–3 days | Bolt 5 (Android tester build) | Build the app and pass all local checks; delay Google Play upload until setup is confirmed. |
| D4 | RAAD logo file | External (design) | Unknown | Bolt 5 (`RaadMobile` completion — logo needed for app UI) | Proceed with a placeholder asset; replace before `prd` deploy. `prd` gates on the real file. |
| D5 | Test-access email address for the landing page **Request test access** button | External (product) | Unknown | Bolt 4 (`RaadWeb` completion — email needed for the button) | Deploy the page with a placeholder email; replace before `prd` deploy. `prd` gates on the real address. |
| D6 | macOS runner or macOS laptop with Xcode and CocoaPods for iOS builds | Engineer 2 / GitHub Actions | 1–2 days to confirm runner availability | Bolt 5 (iOS simulator integration tests and TestFlight build) | Use a physical macOS machine if the GitHub Actions macOS runner is unavailable. Confirm before Bolt 5 starts. |
| D7 | Native Arabic review of app and landing page wording | External (language reviewer) | Unknown | Pre-`prd` release (not a Bolt blocker; a release-gate condition) | Complete all technical acceptance in English first; Arabic review is the final gate before `prd` deploy. |
| D8 | Docker available on the CI runner for `RaadMoneyService` concurrency tests | Engineer 1 / GitHub Actions | Assumed available; confirm before Bolt 2 | Bolt 2 (concurrency test against real data-store container) | Run concurrency tests in a local Docker container during development; CI confirmation needed before merge to `main`. |

## Critical-Path Dependencies

**D1** (AWS account) blocks Bolt 1 and therefore the entire build. It must be resolved first.

**D6** (macOS for iOS) blocks Bolt 5 and must be confirmed before that Bolt starts. If it is not in place, Bolt 5 cannot finish.

**D4 and D5** (logo and email) do not block their Bolt's technical work — they block `prd` deploy only. Each Bolt can be completed and verified on `dev` and `stg` with placeholders.

## Items Inside the Team's Control

The following are not external dependencies — they are within the team's control and tracked in the unit of work:

- Python version pinning and `uv` lockfile setup (`RaadMoneyService`, `Raad`)
- Flutter SDK version pinning and `pubspec.lock` (`RaadMobile`)
- Two test users set up with the setup script from U1 — created by the team, not an external dependency

## Sources

- `unit-of-work.md` in `inception/units-generation/`: Open Questions (logo, email, Arabic review)
- `delivery-planning-questions.md` in this directory: Q5 B, Q6
- `team-practices.md` in `inception/practices-discovery/`: Testing Posture (Docker for concurrency test), Deployment (iOS builds need macOS)
