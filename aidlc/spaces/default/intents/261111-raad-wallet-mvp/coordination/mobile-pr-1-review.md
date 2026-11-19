# RaadMobile PR #1 review

Reviewed PR https://github.com/00az/RaadMobile/pull/1 at head `8812178f313dcd86c296af142e86cb6e8129689b`, base `c615d299880ec2891f50734e87d09b1a32508ccd`.

Recommendation: request changes before merge. This is a local review; no GitHub review was submitted.

## P1: System Back permits a duplicate transfer after an unknown outcome

Location: `lib/screens/send_review_screen.dart:119-124`.

`PopScope.canPop` checks only `_submitting`. After a lost response, `_submitting` becomes false and `_outcomeUnknown` becomes true. Hiding the app-bar back arrow does not disable system Back. The user can return to the populated send form, continue, and confirm with a freshly generated key before reconciling balance/history. The first request may already have committed; the second request creates another transfer. This violates the U1 partial-release rule against resending an unknown transfer outcome.

Reproduced at the exact PR head using the contract fake: commit then lose the response, invoke `tester.binding.handlePopRoute()`, continue from the unchanged form, confirm again. Expected one POST; actual two POSTs. The app's existing unknown-outcome tests only check that the confirm button disappears or use the explicit check-wallet button; they miss system navigation.

Fix the unknown-outcome navigation so system Back cannot return to a resendable form; either keep the user on the reconciliation screen or route Back through the wallet reconciliation flow. Preserve the explicit wallet action. Add a regression covering system Back after a committed-but-lost response and verify only one POST is sent.

## Validation and scope

- Isolated detached checkout of the exact PR head; original mobile branch and working files were untouched.
- `flutter pub get --offline` succeeded using installed dependencies.
- `flutter test --reporter expanded`: 109 existing tests passed; the one added review regression failed.
- Focused regression repeated with `flutter test --no-pub test/pr1_navigation_review_test.dart --reporter expanded`: expected 1 POST, actual 2.
- Regression retained in the ignored review checkout at `.aidlc-engine/mobile-pr-1/test/pr1_navigation_review_test.dart` beneath this intent.
- Reviewed auth/session, environment configuration, generated client/wrapper, send flow, wallet/history handling, tests, CI and declared U1 scope. No AWS/provider/device calls, release builds or live verification were performed. English-only U1 and first-page history are explicitly scoped; Arabic/full frontend remains U3 work.

