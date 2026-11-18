# Code Summary — u3-mobile-app

Conversation language: English.

## Summary

U3 completes the RAAD mobile app in `RaadMobile`, as local, tested code in the worktree `/Users/as/Developer/projects/RaadMobile-u3` (registered checkout `RaadMobile-u3`), branch `aidlc/u3-mobile-app`, based on `origin/aidlc/u1-mobile-skeleton` at `7eb70f9`. Nothing was deployed, uploaded or pushed, and no AWS call was made. The first build is committed on that branch as `9a790b6`; the Step 16 rework is uncommitted on top of it. Plan Steps 1–16 are complete and ticked. On 18 November the person reopened U3 for review findings R-01 and R-03 (message 8200a3be), which added Step 16; see "Step 16 rework" below. Step 17 (this evidence, the review, the person's checkpoint and publishing) belongs to the conductor and the person.

Testing followed the approved Testing Contract (custom: test-after for the app). The developer also wrote the money-core tests for Step 4 before its controller; that is stricter than the contract asks and changes nothing it requires. The 80% floor was never relaxed.

## What Was Built

| Step | Built |
|---|---|
| 1 | Worktree and baseline: 111 tests passed, 92.47% line coverage, analyze and the client-generation check clean. `dart format` failed on the co-engineer's `wallet_screen.dart` and `virtual_card.dart` (fixed later). The decimal "Max" maths and hard-coded strings were noted. |
| 2 | `flutter_localizations`, `connectivity_plus` and the dev dependency `flutter_launcher_icons` added with `flutter pub add`; `l10n.yaml` with `generate: true`; ARB catalogs; `test/support/` fakes (clock, connectivity, in-memory store) and display helpers. |
| 3 | C1 re-pinned to U2's `1.0.0-u2.1` (RaadMoneyService `2b3660b`, sha256 `31780d20…ece0`); client regenerated; `money_service.dart` and the fake backend follow U2 (repeatable `PUT /wallet`, recipient refusals, 100–50000 halalas, 429 with Retry-After, replay, opaque cursor). |
| 4 | Integer-halala money throughout, the "Max" chip fixed, `PendingTransfer` in protected storage scoped to account and environment and saved before the send, and the `SubmissionController` state machine. |
| 5 | Sign-up, confirm, resend, forgot and reset in the Cognito adapter and the fake, with stable error codes; `SessionBoundary` with one shared renewal, the 31-day idle rule on an injected clock, conservative handling of a clock going backwards, a session epoch that drops late answers, and a full clear on sign-out. |
| 6 | Wallet setup before the wallet with Try again; `BalanceSnapshot` with an out-of-date label and time, no fabricated zero; Refresh button and pull to refresh; newest request wins. |
| 7 | Send flow: every refusal keeps the typed values; review and Cancel; the uncertain screen with Try again on the saved key; the result; offline disables Send, Confirm and Try again with a reason. Nothing is queued or resent automatically. |
| 8 | History: opaque cursor chain, one shared Load more, cursor restart, refresh replacing the chain, and separate loading, empty, error and loaded views. |
| 9 | Screens: Sign-up, Confirm email with Send the code again, Forgot and Reset password, an Account screen (language and sign-out), and the session-expired and setup-failed notices. |
| 10 | 166 messages in `en` and `ar`; `messages.dart` is now a thin lookup; a per-installation language selector; right-to-left Arabic with email, amounts and references isolated left to right; Western digits (A8, proposed). |
| 11 | Labels, live-region announcements, 44dp targets, contrast, 200% text at 320dp; the decorative card and service tiles are announced as not available. |
| 12 | Android product flavours (`.dev`, `.stg`, none; "RAAD DEV", "RAAD STG", "RAAD"), iOS build configurations, three schemes and a "Check C4" build phase; `EnvironmentConfig.fromDefines` refuses missing, extra, secret-looking and cross-environment values and the app fails closed at start; launcher icons from the bolt-only mark. |
| 13 | `integration_test/u3_journeys_test.dart` plus an updated walking-skeleton test, run on an iOS simulator and an Android emulator against the fake backend. |
| 14 | CI keeps every step and adds Java 17, `tool/check_l10n.dart`, a gen-l10n drift check and the Android dev debug build; README updated (setup, test, flavour builds, prerequisites, integration commands). |
| 15 | `docs/acceptance-journey.md`: an eight-step procedure for the six SOW criteria, with what each step proves and its evidence. Nothing in it is claimed as run. |
| 16 | R-01 and R-03 rework: `test/log_privacy_test.dart` and `tool/check_no_logging.dart` (also a CI step), and the decorative card without third-party marks. Described below. |

### Step 16 rework (R-01, R-03)

- **Log privacy test (12 tests).** Captures everything written through `print` (zone override), `debugPrint` (replaced and always restored) and `stdout`/`stderr`. It runs an account journey (sign-up, resend, wrong code, confirmation, refused then good sign-in, wallet setup, sign-out, forgot and reset, sign-in, sign-out) and a money journey (sign-in, wallet and refresh, a 37.19 SAR send whose answer is lost, Try again, the result, history with Load more and refresh, sign-out). It fails if any captured text holds a password, code, token, account id, email (typed and normalised), display name, amount (halalas and SAR), request key or history cursor, and names only the kind of value. Two canary tests prove the capture catches writes from direct calls, a widget build, a tap, a timer and a microtask. A temporary token `print` added to `money_service.dart` made both journeys fail; it was removed and that file is unchanged.
- **No-logging check.** `tool/check_no_logging.dart` scans every `.dart` file under `lib/` except generated `lib/api/generated/` and `lib/l10n/` (43 files) and fails on any call or tear-off of `print`, `debugPrint` and its relatives, the `debugDump*` dumps, `stdout`/`stderr`, and `dart:developer` `log` (with or without a prefix). It runs as its own CI step after analysis and in the README's local gates. `dart:developer` `log` cannot be captured inside a test, so this check is its guard.
- **Decorative card.** The "VISA" wordmark, the "Add to Apple Wallet" chip and its Apple Pay "not available yet" message are gone, with their two catalog keys. The card keeps the RAAD bolt and wordmark, a decorative chip graphic and the masked number, and gains a bordered "Demo card" / "بطاقة تجريبية" label. Screen readers hear "Virtual card design. Demo card. Not available yet." Tests check all three card variants in both languages for the label and for no card-network or wallet text.

## Files Created or Modified

All 139 paths are listed in `source-manifest.json` as `RaadMobile-u3@checkout/<path>`: the 137 of the first build plus `test/log_privacy_test.dart` and `tool/check_no_logging.dart` from Step 16. None was deleted.

| Area | Paths |
|---|---|
| App source (new) | `lib/app/{connectivity,language,protected_store}.dart`, `lib/auth/session_boundary.dart`, `lib/config/build_environment.dart`, `lib/money/{balance_snapshot,history_controller,pending_transfer,submission_controller,wallet_controller}.dart`, `lib/screens/{account,confirm_email,forgot_password,history,reset_password,sign_up}_screen.dart`, `lib/ui/formatting.dart`, `lib/widgets/{form_fields,language_selector,status_banner}.dart`, `lib/l10n/` (ARB catalogs and generated localizations) |
| App source (modified) | `lib/api/money_service.dart` and three regenerated client files, `lib/app/{app_services,raad_app}.dart`, `lib/auth/{auth_service,cognito_auth_service}.dart`, `lib/config/environment_config.dart`, `lib/dev/` fakes, `lib/main.dart`, `lib/main_fake.dart`, `lib/money/halalas.dart`, six existing screens, `lib/ui/{messages,raad_theme}.dart`, `lib/widgets/virtual_card.dart` |
| Tests | 14 new test files, `test/support/{display,fakes}.dart`, `integration_test/u3_journeys_test.dart`; 10 existing test files and the walking-skeleton test updated |
| Contracts | `contracts/pinned/c1-money-api/raad-money-v1.yaml`, `contracts/pins.yaml` |
| Builds and assets | `pubspec.yaml`, `pubspec.lock`, `l10n.yaml`, `android/app/build.gradle.kts`, `AndroidManifest.xml`, launcher icons, iOS xcconfigs (9 new), three schemes, `project.pbxproj`, `Podfile`, `Podfile.lock`, `Info.plist`, `ios/scripts/check_c4.sh`, `assets/images/raad_lockup.webp`, `assets/raad_bolt_icon.png` |
| Tooling and docs | `tool/check_env_config.dart`, new `tool/check_l10n.dart`, `.github/workflows/ci.yml`, `README.md`, new `docs/acceptance-journey.md` |

## Commands Run and Results

All runs are from `RaadMobile-u3`, with Flutter 3.47.2 and no network calls to AWS.

| Command | Result |
|---|---|
| Baseline `flutter test --coverage` and the 80% check (unchanged tree) | 111 passed; 92.47% |
| `flutter pub get --enforce-lockfile` | Exit 0 |
| `dart format --output=none --set-exit-if-changed lib test integration_test tool` | 95 files, 0 changed |
| `flutter analyze` | No issues |
| `dart run swagger_parser --check` | Generated client up to date |
| `dart run tool/check_l10n.dart` | First build: 166 messages; after Step 16: 165 (two card keys removed, one added) |
| `dart run tool/check_no_logging.dart` (Step 16) | No logging calls in 43 files under `lib/` |
| `dart run tool/check_env_config.dart config/c4-dev.example.json dev` | Valid |
| `flutter test --coverage` | First build: 321 passed. **After Step 16: 337 passed, 0 failed** (re-run by the conductor) |
| `dart run tool/check_coverage.dart coverage/lcov.info 80` | First build: 92.95%. **After Step 16: 94.05%** (3413 of 3629 lines), floor 80% met; `virtual_card.dart` 79.3% → 100% |
| Step 16: `flutter gen-l10n`, format, analyze, `swagger_parser --check`, C4 example check, Android dev debug build | Regenerated (identical on a second run); 97 files, 0 changed; no issues; up to date; valid; built `app-dev-debug.apk`. The simulator and emulator journeys and the iOS build were not re-run for Step 16 (they do not check the card or logging). |
| Component files (contract; money core; account and session; wallet; send and offline; history; account screens; language; accessibility; environments) | 25; 59; 54; 27; 46; 23; 21; 17; 17; 31, all passed |
| `flutter build apk --debug --flavor dev --dart-define-from-file=config/c4-dev.example.json` | Built `app-dev-debug.apk` |
| `flutter build ios --debug --no-codesign --flavor dev --dart-define-from-file=config/c4-dev.example.json` | Built, bundle id `sa.raad.raadMobile.dev` |
| Wrong-environment and missing C4 builds | Refused: Android `checkC4<Variant>` fails for stg with the dev file and for dev with no file; iOS "Check C4" phase fails for stg with the dev file |
| Integration, iOS: `flutter test integration_test/walking_skeleton_test.dart integration_test/u3_journeys_test.dart -d <iPhone 17 simulator, iOS 27.2>` | **5/5 passed** (fake-backed) |
| Integration, Android: same files with `--flavor dev -d emulator-5554` (API 37) | **5/5 passed** in 3m11s (fake-backed). The AVD is set to 1 core and 2 GB and did not finish booting; it was cold-booted with `-cores 4 -memory 4096` overrides, without editing the AVD. |
| Secret check | Gitleaks is not installed locally and was not installed (the plan does not name it); it runs in CI. A grep of the diff found only the detection regex and AWS's documentation example key in a test, now built from parts so Gitleaks will not flag it. |
| Money check | No `double` or `/ 100` on money values; the only hit is the integer `~/ 100` in `halalas.dart`. No print, debugPrint or log calls in `lib`. |

The five journeys on each platform: the walking skeleton (balance, one 100 SAR transfer, both histories); sign-up, confirm, sign-in, wallet, send, result and history; a lost answer then Try again with the same key, moving money once; offline turning sending off and back on; Arabic laid out right to left with a switch back that keeps the session.

## Test Coverage Summary

About 210 new test cases on top of the 111 baseline (321 in all), against the plan's estimate of 110–150, which was not a cap. Line coverage 92.95%. The lowest files are `lib/app/connectivity.dart` at 28% (the thin platform-plugin wrapper; its logic is tested through the manual connectivity signal), `lib/l10n/app_localizations_ar.dart` at 69.1% (generated), `lib/main.dart` at 69.6% and `lib/widgets/virtual_card.dart` at 79.3%. No coverage-ignore comment was added and no threshold changed.

## Tests Written but Not Executed Here

- **Live journeys against a deployed `dev`** (real Cognito and U2): not run; they need the person's cost go-ahead and the dev deploy.
- **GitHub Actions**: the updated `ci.yml` (including Gitleaks and the Android dev build) has not run yet; only the equivalent local commands ran.
- **stg and prd builds with real C4 files**: not built; only the dev example C4 exists. The refusal checks did run.

## Key Decisions and Deviations

1. **A8 digits (proposed, needs the person).** Western digits 0–9 in both languages; Arabic-Indic digits typed by the person are accepted and converted.
2. **"Max" chip.** Fills in the smaller of the balance and 500.00 SAR, in integer halalas.
3. **Brand assets.** The launcher icon `assets/raad_bolt_icon.png` was cut from the co-engineer's `raad_logo.jpg`; the in-app lockup `assets/images/raad_lockup.webp` is copied from RaadWeb's `site/assets/raad-logo.webp`. The person should look at both before release.
4. **Third-party marks on the decorative card (R-03, fixed in Step 16).** The "VISA" wordmark and the "Add to Apple Wallet" chip were removed at the person's request; the card is labelled "Demo card".
5. **Colour.** The muted text colour was lightened to `#7F8CA1` to meet contrast; the co-engineer should know.
6. **Navigation.** The Account button opens a new Account screen (language and sign-out). The wallet shows the latest five entries, with a full History screen behind it.
7. **Read retry.** A 503 on a read is retried once (NFR6.10). Transfers are never retried automatically and a 429 is never retried.
8. **Old sessions.** A stored U1 session with no last-use record asks the person to sign in again.
9. **Demo shortcuts.** Shown only in the offline preview (`main_fake.dart`), never in real builds.
10. **iOS packaging.** `pod install` (run by the iOS build) changed `Podfile.lock` and `project.pbxproj`: `flutter_secure_storage_darwin` and `integration_test` now come through Swift Package Manager instead of CocoaPods.
11. **Log privacy (R-01, fixed in Step 16).** The first build had no capture test; Step 16 adds the log privacy test and the no-logging check described above, and NFR10.10 is traced to them.
12. **Traceability check on a sibling checkout.** `traceability.json` names its 86 OK targets as `RaadMobile-u3@checkout/<path>`. The stage's traceability check cannot resolve that label and reports each one as a missing file (fire `cc995eb2`), as it did for U2 and U5. Every target was checked by hand to exist in `/Users/as/Developer/projects/RaadMobile-u3`; the finding is advisory.
13. **Deliberate test changes.** U1's English strings moved to the catalogs, and U1's first-page-only history became U2 paging; existing tests were updated for those changes only.

## Checks Still Open

None of these is claimed as passed.

- Journeys against a deployed `dev` with real Cognito and U2, and the U4 provider checks P1–P13 (P7 code invalidation and the P10 burst especially).
- VoiceOver and TalkBack walkthroughs on real iOS and Android devices; keyboard and switch access on devices.
- A native Arabic speaker's review of all 166 messages.
- The person's A8 digit decision (AC5.1.4 is built to the proposal).
- The new Arabic label "بطاقة تجريبية" joins the native-speaker review.
- TestFlight and Google Play internal builds per environment (AC6.2.2); this may need the existing paid developer accounts, and nothing is bought.
- The first CI run of the updated workflow.
- The local Android emulator `Medium_Phone_API_37.0` needs 4 cores and 4 GB to boot, or the `-cores 4 -memory 4096` overrides.

## Handoff

- The U3 branch `aidlc/u3-mobile-app` currently tracks `origin/aidlc/u1-mobile-skeleton`. On the person's approval it is committed, pushed with its own upstream, and opened as a PR stacked on RaadMobile PR #1 (U1), retargeted to `main` when PR #1 merges.
- U3 needs no change in Raad, RaadMoneyService or RaadWeb. Real per-environment C4 files come from U4's `write_platform_config.py` after each environment is deployed.
