# Unit Test Instructions — u3-mobile-app

Conversation language: English.

## Framework Setup and Ordering

Run every command from the U3 worktree root, `/Users/as/Developer/projects/RaadMobile-u3`, with the pinned Flutter 3.47.2 and the committed `pubspec.lock`:

```sh
flutter pub get --enforce-lockfile
```

The Testing Contract in the plan is authoritative and is custom: test-after for the whole Flutter app (TDD applies only to RaadMoneyService's money core). Implement each layer, then write and run its tests. Do not manufacture Red/Green evidence.

Runner readiness, runnable before any new test file exists (Step 2):

```sh
flutter test test/money_test.dart
```

Baseline on the unchanged tree (Step 1), recorded before any change:

```sh
flutter test --coverage
```

```sh
dart run tool/check_coverage.dart coverage/lcov.info 80
```

## Component Tests

Each command names exact files. A file becomes runnable when its step lands. Keep every existing test; add about 5–8 cases per component, more where a boundary matrix below needs them (estimate 110–150 new cases, not a cap).

| Area | Exact command | Required coverage |
|---|---|---|
| C1 contract and client | `flutter test test/contract_test.dart` | New pin hash; U2 schema shapes; unknown `Error.code` to a safe message; unknown optional fields ignored; strict request shapes; `429` with Retry-After; replay result; cursor shape |
| Money core | `flutter test test/money_test.dart test/pending_transfer_test.dart test/submission_controller_test.dart` | Amount boundaries 99/100/50000/50001, zero, negative, over-precise, long input, exact balance; integer "Max"; key persisted before send; save failure blocks send; double tap; refusal keeps values and next intent gets a new key; same-key Try again; changed details new key; restart restore without send; process death before send, after possible commit, after response; another account cannot see the intent |
| Account and session | `flutter test test/cognito_auth_test.dart test/auth_flows_test.dart test/session_boundary_test.dart test/sign_in_test.dart` | Trimmed lowercased email on every call; one sign-in refusal; rate-limited; wrong/expired code; resend same reply; password rule; email taken; shared renewal; idle 30 vs 31 days; clock going backwards; sign-out clears tokens, caches, pending intent and navigation; late responses dropped |
| Wallet and balance | `flutter test test/wallet_screen_test.dart test/wallet_setup_test.dart test/balance_snapshot_test.dart` | Setup before wallet; setup-failed retry; stale label with time; label cleared on success; no zero without a snapshot; Refresh button and pull to refresh; newest request wins |
| Send flow and offline | `flutter test test/transfer_flow_test.dart test/send_refusals_test.dart test/offline_test.dart` | Each refusal keeps values; review cancel sends nothing; uncertain view and same-key retry; result refreshes balance and history; offline disables Send/Confirm/Try again with a reason and re-enables; no queued write; no automatic resend |
| History | `flutter test test/history_screen_test.dart test/history_paging_test.dart` | Sent and received rows, local time, service order; Load more with the exact cursor; shared taps; failure keeps rows and retries the same cursor; expired cursor restart; refresh drops the old chain; null cursor ends; empty/loading/error; 1000 entries with no duplicates or gaps and no duplicate requests |
| Account screens | `flutter test test/account_screens_test.dart` | Sign-up, confirmation and resend, the confirmation-code link, forgot and reset, sign-out, session-expired and setup-failed screens: success, refusal and rate-limit paths; email and name kept; password never stored |
| Language | `flutter test test/l10n_catalog_test.dart test/rtl_layout_test.dart` | Every key in `en` and `ar`, none empty; RTL layout; LTR isolation of email, amounts and references; switch mid-draft and mid-uncertain keeps values and key |
| Accessibility | `flutter test test/accessibility_test.dart` | `meetsGuideline` tap-target, labelled-target and text-contrast checks; 200% text at 320dp with no clipped action on sign-in, wallet, send, review and history; status announcements; decorative card and unavailable tiles announced as unavailable |
| Environments and start | `flutter test test/environment_config_test.dart test/flavour_config_test.dart test/app_start_test.dart` | dev/stg/prd configs valid; missing, extra, secret-looking and cross-environment values refused; the app refuses to start before private data on a bad config |
| Log privacy (Step 16, R-01) | `flutter test test/log_privacy_test.dart` | Sign-in, wallet, send with a lost answer and Try again, history and sign-out run against the fakes while `print`, `debugPrint` and `dart:developer` `log` output is captured; the test fails if any synthetic password, code, token, email, name, amount, request key or cursor appears |
| Decorative card (Step 16, R-03) | `flutter test test/wallet_screen_test.dart test/accessibility_test.dart` | No "VISA" or Apple Wallet text or chip on the card; "Demo card" label in both languages; the card is announced as not available |

## Integration Journeys (fake-backed)

These use `lib/main_fake.dart`, never AWS. Run each platform separately and record its result on its own line:

```sh
flutter test integration_test/walking_skeleton_test.dart integration_test/u3_journeys_test.dart -d <ios-simulator-id>
```

```sh
flutter test integration_test/walking_skeleton_test.dart integration_test/u3_journeys_test.dart -d <android-emulator-id>
```

Journeys: sign-up, confirm, sign-in, wallet, send, result, history; a lost answer then Try again with the same key; offline disable; Arabic layout and a language switch. If a simulator or emulator is not available, record it as not run with the reason; never as passed.

## Coverage Targets

RaadMobile's floor is **80% line coverage** on the full suite, and coverage on `main` must not decrease. Build and Test checks it on the assembled suite. Run it as two separate commands, with nothing chained after the threshold:

```sh
flutter test --coverage
```

```sh
dart run tool/check_coverage.dart coverage/lcov.info 80
```

Never lower the threshold, exclude source, or add coverage-ignore comments to pass it. The generated `lib/api/generated` and `lib/l10n` output follows the existing coverage configuration.

## Static and Build Checks

```sh
dart format --output=none --set-exit-if-changed lib test integration_test tool
```

```sh
flutter analyze
```

```sh
dart run swagger_parser --check
```

```sh
dart run tool/check_env_config.dart config/c4-dev.example.json dev
```

```sh
dart run tool/check_no_logging.dart
```

```sh
flutter build apk --debug --flavor dev --dart-define-from-file=config/c4-dev.example.json
```

The iOS flavour build (`flutter build ios --debug --no-codesign --flavor dev ...`) needs Xcode and CocoaPods on this Mac; record it as run or not run.

## Mocking and Test Data

- Use the existing fakes in `lib/dev/` (auth and money backend) and `test/support/harness.dart`; add an injected clock, an injected connectivity signal and in-memory secure storage. No test calls Cognito, the money API or AWS.
- Contract tests read only the pinned C1 copy.
- Use synthetic accounts such as `amal@example.test`; never a real address, password, token or confirmation code. Tests that capture logs assert that no token, code, email, amount or request key appears.
- Every amount in fixtures is integer halalas.

## Live Checks — Not Run Here

Journeys against a deployed `dev` (real Cognito and U2), U4's P1–P13 provider checks, VoiceOver and TalkBack walkthroughs on devices, the native Arabic wording review and TestFlight/Play distribution are not run in this stage and stay pending. Fake-backed results do not stand in for them.
