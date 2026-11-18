## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-18T16:54:21Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u3-mobile-app/code-generation/code-summary.md > Key Decisions and Deviations item 11 | The unit test instructions asked for a test that captures logs and asserts no token, code, email, amount or request key appears. None was written. The "never write tokens or personal details into logs" rule (NFR10.10) rests only on a one-time search showing no print, debugPrint or log calls in lib. I repeated that search and it is clean today, but nothing stops a later change from adding a log call. | Add a small guard test or a CI grep step that fails if lib gains print, debugPrint or developer.log calls. Otherwise record at the gate that NFR10.10 is accepted as unverified by a test. | Resolved (reviewer) |
| R-02 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u3-mobile-app/code-generation/code-summary.md > Tests Written but Not Executed Here | The live journeys against a deployed dev (real Cognito and U2), the U4 provider checks P1 to P13 and the first run of the updated CI workflow (including Gitleaks and the Android dev build) have not run. All integration results come from the fake backend. The Construction Verification Command `scripts/verify-dev.sh` was not run because no dev environment exists and no AWS call is authorized. | Keep these as open checks before release. Do not treat the 5/5 fake-backed journeys as proof of the real sign-in, API and data path. | Accepted risk |
| R-03 | Minor | RaadMobile-u3/lib/widgets/virtual_card.dart:353 (the "VISA" wordmark) and the "Add to Apple Wallet" chip | A third-party card brand mark and an Apple Wallet chip sit on a simulated wallet that has no card. This hints at a real payment system and is a trademark question. The summary flags it and leaves it to the person. | The person decides at the gate whether to keep, change or remove both marks. | Resolved (reviewer) |
| R-04 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u3-mobile-app/code-generation/code-summary.md > Key Decisions item 1 (A8 digits) | AC5.1.4 is built to a proposed Western-digits-in-both-languages choice that the person has not confirmed. | Get the person's A8 decision. If it changes, plan a follow-up change to the formatting helpers. | Accepted risk |
| R-05 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u3-mobile-app/code-generation/traceability.json > targets named `RaadMobile-u3@checkout/<path>` | The traceability sensor cannot resolve the sibling-checkout label and reports each of the 86 targets as a missing file. The developer checked every target by hand. | Treat the sensor output as a known false positive. Do not rework the traceability file for it. | Accepted risk |
| R-06 | Minor | RaadMobile-u3/lib/app/connectivity.dart (28.0% line coverage) | The platform-plugin wrapper is mostly uncovered, with no coverage-ignore added. Overall coverage is well above the floor, and the offline logic is tested through the manual signal. | None required. Optionally add one test of the plugin-to-signal mapping. | Accepted risk |
| R-07 | Minor | RaadMobile-u3/lib/main.dart and lib/app (no `FlutterError.onError` or `runZonedGuarded` handler); RaadMobile-u3/tool/check_no_logging.dart | The no-logging check and the journeys cover the app's own writes and the fake-backed happy and failure paths. They do not cover Flutter's default error reporting, which prints exception text and stack traces to the console for any unhandled error in debug and profile builds. The app installs no handler of its own. If an exception message ever embeds a token or an email address, it would reach the console unseen by both guards. Nothing in `lib/` interpolates an exception into text today (grep clean). The log test also runs only against the fakes, not the real Cognito and API adapters, so the real adapters' error text is untested. | Optional. Either install a global error handler that records only the error type, or note at the gate that NFR10.10 is verified for the app's own writes and not for framework error output. Recheck when the live dev journeys run. | New |

> R-01 Reviewer note: `test/log_privacy_test.dart` captures print (zone override), debugPrint (replaced and restored, also on failure), and stdout and stderr (IOOverrides). Two canary tests prove a deliberate leak is caught and named without its value, including from a build, a tap, a timer and a microtask. Two full journeys (account and money, with a lost answer and Try again, and paging) assert no password, code, token, account id, email, name, amount, request key or cursor appears. `tool/check_no_logging.dart` guards `lib/` statically and runs as a CI step in `.github/workflows/ci.yml`. It is run here and passes (43 files).

> R-01 Earlier decision: Accepted risk

> R-03 Reviewer note: `lib/widgets/virtual_card.dart` no longer holds the "VISA" wordmark, the Apple icon, the Apple Wallet chip or the snackbar. A grep of `lib/` (excluding generated client) for visa, mastercard, apple and mada finds no matches. The Arabic and English catalogs drop `cardsAddToAppleWallet` and `cardsAppleWalletSoon` and add `cardsDemo` ("Demo card" and the Arabic equivalent). The catalogs match at 165 messages.

> R-03 Earlier decision: Accepted risk

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| flutter analyze | No issues found | Clean. |
| flutter test --coverage | 337 tests, all passed | Includes the new log privacy tests and the card tests. |
| dart run tool/check_coverage.dart coverage/lcov.info 80 | Line coverage 94.05% (3413 of 3629); floor 80% | Above the floor. `virtual_card.dart` is at 100%. |
| dart run tool/check_l10n.dart | Arabic and English catalogs match: 165 messages | The card catalog change is consistent in both languages. |
| dart run tool/check_no_logging.dart | No logging calls in 43 files under lib/ | The generated client and l10n are excluded by design. |
| scripts/verify-dev.sh | Not run | It targets a deployed dev that does not exist and no AWS call is authorized. This is the already-decided R-02 and is not raised again. |

### Summary

R-01 and R-03 are fixed on the evidence. The log test really captures output and names a leak, the static check covers print, the debugPrint family, stdout and stderr and dart:developer log with comment and string handling, and the card carries no third-party mark in either language. The one remaining gap is minor: Flutter's own error output is outside both guards.
