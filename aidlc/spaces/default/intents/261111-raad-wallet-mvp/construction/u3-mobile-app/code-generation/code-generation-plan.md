# Code Generation Plan — u3-mobile-app

## Summary

- Builds: the complete bilingual RAAD app on top of U1 and the co-engineer's new UI: account screens, U2 money rules, offline and history paging, Arabic/RTL, accessibility and dev/stg/prd builds.
- Touches: RaadMobile `lib/` (auth, money, screens, l10n, widgets), `test/`, `integration_test/`, `contracts/` (C1 re-pin), `android/` and `ios/` flavour files, `tool/`, CI and README.
- Tests: about 110–150 new unit, widget and contract tests on top of the existing 111, plus fake-backed integration journeys on an iOS simulator and an Android emulator; the 80% line floor stays.

Conversation language: English.

## Ownership and Coordination

U3 is claimed by ziyad-alamri (generation 1) in the Raad checkout, from `main` at `35d3a10` with U1, U2, U4 and U5 merged in the record. U3's code lives in `RaadMobile` only. Raad, RaadMoneyService and RaadWeb are read-only inputs.

The code is built in a separate worktree, `/Users/as/Developer/projects/RaadMobile-u3`, on a new branch `aidlc/u3-mobile-app` created from `origin/aidlc/u1-mobile-skeleton` at `7eb70f9`. That commit holds the approved U1 skeleton, the co-engineer's U3 screens built outside AI-DLC (`9e9fb01`, "u3 imrpoveUi") and the restored C1 re-pin and system-Back fix. The person's main RaadMobile checkout and its uncommitted iOS files are left untouched. U1's mobile PR (00az/RaadMobile#1) is still open, so the U3 PR is stacked on it and retargets `main` once PR #1 merges.

The co-engineer's added UI stays, as the person decided on 17 November (message 3eb4ad2d): the theme, the virtual card carousel, the services tiles and the "Max" amount chip. U3 makes them meet the project rules (integer money, bilingual text, accessibility). The decorative card and the international and bank-transfer tiles stay non-functional; no card or bank detail is ever collected.

No deployment, store upload, purchase or AWS call happens in this stage. Live checks against a deployed `dev` wait for the person's separate cost go-ahead.

## Authoritative Inputs and Decisions

- **C1:** re-pin from U1's development pin (`1.0.0-u1.2`) to U2's contract `1.0.0-u2.1`: `00az/RaadMoneyService` `openapi/raad-money-v1.yaml` at commit `2b3660b`, sha256 `31780d203ceb04f4a9e16e99e53573addab97dc7b1713e6918d5615237a9ece0`. It is still a development pin; no release tag exists. Same-key retry after a lost answer is enabled only because U2 now replays a repeated request key (C1 replay cutover). If a pinned field or behaviour differs from what this plan expects, the gap goes back to the person, not into a workaround.
- **C3:** native Cognito through the existing `amazon_cognito_identity_dart_2` adapter. Sign-up, confirmation, resend, forgot and reset are added to it. The A4 password rule (8+ characters, upper, lower, digit, no symbol) is shown before entry. Wrong password, unknown email and unconfirmed account give one refusal; rate-limited is separate.
- **C4:** one validated non-secret file per environment (`config/c4-<env>.json`), produced by U4's `write_platform_config.py` from real deploy outputs. Until dev is deployed only the example file exists, so builds for real environments fail closed; that is expected.
- **A8 (proposed, not yet a person's decision):** Western digits 0–9 in both languages, with "SAR" and "ر.س" labels. The person can change this at Plan Approval.
- **Brand:** the app uses the person's horizontal lockup (bolt plus "رعد RAAD") in the app and the bolt alone for the launcher icon (person, 17 November). The bolt-only file is cut from the supplied lockup if no separate file exists, and shown to the person in the code summary.
- **Dependencies:** `flutter_localizations` (Flutter SDK) and `connectivity_plus` (advisory offline signal) are added at runtime, and `flutter_launcher_icons` as a dev dependency. No analytics, crash, payment or backend SDK is added, and no Flutter or Dart upgrade.

## Implementation Steps

Each checkbox is one sequential Step. Every app layer is implemented first, then its tests are written and run (test-after for the Flutter app, as the Testing Contract says). Test-runner readiness is proved in Step 2, before the first new test.

- [x] **Step 1 — Set up the U3 worktree and record the baseline.** Create `/Users/as/Developer/projects/RaadMobile-u3` with `git -C /Users/as/Developer/projects/RaadMobile worktree add -b aidlc/u3-mobile-app ../RaadMobile-u3 origin/aidlc/u1-mobile-skeleton`, then register it for the review with `aidlc engine intent add-checkout /Users/as/Developer/projects/RaadMobile-u3`. On the unchanged tree record: `flutter pub get --enforce-lockfile`, `dart format --output=none --set-exit-if-changed lib test integration_test tool`, `flutter analyze`, `dart run swagger_parser --check`, `flutter test --coverage` with `dart run tool/check_coverage.dart coverage/lcov.info 80`. Inventory the existing screens, services, messages and tests, and note each place the co-engineer's UI does money maths in decimals or shows text not in `messages.dart`. Stories: all U3 stories; NFR14.
- [x] **Step 2 — Prepare the runner, localisation tooling and dependencies.** Add `flutter_localizations` (SDK), `connectivity_plus` and the dev dependency `flutter_launcher_icons` through `flutter pub add`, with `pubspec.lock` committed. Add `l10n.yaml` and `flutter: generate: true` for `gen-l10n` with empty `lib/l10n/app_en.arb` and `app_ar.arb` catalogs. Add `test/support/` helpers for a fake clock, a fake connectivity signal, in-memory secure storage and a locale/text-scale harness. Prove `flutter test test/money_test.dart` runs before the first new test. Stories: US5.1, US6.2; NFR14.
- [x] **Step 3 — Re-pin C1 to U2 and regenerate the client, then contract tests.** Use `tool/pin_contract.dart` to replace the pinned copy and `contracts/pins.yaml` entry with U2's `1.0.0-u2.1` file (commit `2b3660b`, sha256 above). Regenerate `lib/api/generated` with `dart run swagger_parser`. Update `lib/api/money_service.dart` and `lib/dev/fake_money_backend.dart` for U2 behaviour: wallet setup `PUT /wallet` repeatable without a second credit, recipient refusals, the 100–50000 halala range with no daily limit, `429 RATE_LIMITED` with Retry-After, same-key replay returning the original result, and opaque `nextCursor` paging. Then extend `test/contract_test.dart` for the new hash, schema shapes, unknown `Error.code` mapping to a safe message, ignored unknown optional fields and strict request validation. Stories: US3.3–US3.6, US3.8, US4.3, US6.2; C1.
- [x] **Step 4 — Money core in the app: integer amounts, the pending transfer and the submission controller, then tests.** Keep all amounts as integer halalas, parsed digit by digit from typed SAR (no `double`, no `/ 100` on money). Fix the co-engineer's "Max" chip to format the balance from integer halalas. Add `PendingTransfer` in protected storage, scoped to account and environment, holding the request key, recipient, amount, owner and environment, written before the first send; failure to save blocks the send. Add a submission controller with the states `draft -> review -> submitting -> completed | business-refused | uncertain`; one key per confirmed intent; double taps send once; a definitive refusal keeps the typed values and the next attempt gets a new key; after a lost answer **Try again** reuses exactly the saved key and locked values; changed details start a new intent. Restart or re-sign-in as the same account restores the unresolved intent without sending; another account never sees it. Then unit tests for amount boundaries (99, 100, 50000, 50001, zero, negative, over-precise, long input, exact balance), key reuse rules, double tap, process death before send, after a possible commit and after the response, and account isolation. Stories: US3.3, US3.4, US3.6, US3.8; NFR4; BR3.3, BR3.4.
- [x] **Step 5 — Account services and the session boundary, then tests.** Extend `AuthService` and `CognitoAuthService` (and the fake) with sign-up, confirmation, resend, forgot-password and reset, always with the trimmed, lowercased email. Map provider errors to stable codes (one sign-in refusal; separate rate-limited, code-wrong-or-expired, password-rule, email-taken and network). Add a session boundary: one shared token renewal for concurrent requests; a 31-day idle limit read from an injected clock, refusing clock anomalies conservatively; renewal failure masks private screens and asks for sign-in; sign-out clears tokens, cached balance and history, the pending transfer and navigation, and bumps a session epoch so late responses from the old session are dropped. Then unit tests for each mapping, renewal sharing, idle expiry at 30 and 31 days, clock going backwards, sign-out clearing and late-response discard. Stories: US1.1–US1.6; C3; BR3.1, BR3.2; NFR1.
- [x] **Step 6 — Wallet setup, balance snapshot and refresh, then tests.** After sign-in call `PUT /wallet` before showing the wallet, with a "We could not set up your wallet" screen and a safe **Try again**. Keep a `BalanceSnapshot` (integer halalas plus the last successful UTC update time) per account and environment; a failed or offline refresh shows the old snapshot with an out-of-date label and its time; with no snapshot show an error, never a zero. Add a visible **Refresh** button and pull to refresh; only the newest request for the current session may update the screen. Then widget and unit tests for setup retry, stale label on and off, no fabricated zero and stale responses ignored. Stories: US1.2, US2.2, US5.3; BR3.5; NFR15.
- [x] **Step 7 — Complete the send flow and offline rules, then tests.** Resolve the recipient and show the specific message for unknown recipient, own wallet, too-low or too-high amount, insufficient balance and rate limit, keeping every typed value. Review shows the resolved name and email, the amount and the balance after; Cancel sends nothing. Wire Confirm, the uncertain view (outcome unknown, check history, **Try again** with the saved key) and the result (amount, recipient, reference, authoritative balance after, then refresh). Use `connectivity_plus` as an advisory signal: offline disables Send, Confirm and Try again with a stated reason and re-enables them when the connection returns; nothing is queued; a transport failure while "online" still lands in uncertain for a transfer. Then widget tests for every refusal with values kept, review cancel, uncertain retry with the same key, offline disable and re-enable, and no automatic resend. Stories: US3.3–US3.6, US3.8, US3.9; BR3.3–BR3.5.
- [x] **Step 8 — History paging and states, then tests.** Show sent and received rows with counterparty name and email, the amount, the reference and the device-local time of the UTC instant, in the order the service returns. Add **Load more** with the exact opaque cursor and unchanged page size (20 by default, 100 at most); repeated taps share one request; a paging failure keeps the rows and retries the same cursor; an invalid or expired cursor restarts page one with a message; a refresh replaces the chain and drops late answers from the old chain; only a null cursor ends the list. Separate loading, empty ("no transfers yet"), error with Retry and loaded views. Then widget tests including a 1000-entry journey with no duplicate or skipped rows and no duplicate requests. Stories: US4.2–US4.4, US5.3; BR3.6.
- [x] **Step 9 — Account screens, then widget tests.** Add Sign-up (email, display name, password with the A4 rule shown first; the password is never stored), Confirmation with **Send the code again** (disabled while pending, same reply for any address), the **Have a confirmation code?** link on Sign-in, Forgot password and Reset password (code plus a new compliant password; no blind retry of an uncertain reset), Sign out, the session-expired screen and the setup-failed screen. Refusals keep the email and name. Then widget tests for each screen's success, refusal and rate-limit paths. Stories: US1.1–US1.6; BR3.1.
- [x] **Step 10 — Arabic and English, then tests.** Move every visible string, including the co-engineer's card, services and "Max" text, into the `en` and `ar` ARB catalogs and use the generated localizations everywhere; `lib/ui/messages.dart` becomes a thin lookup or is retired. Add a language selector stored per installation; switching changes text and direction at once without signing out, losing a draft, changing a request key or restarting a request. Arabic is right-to-left with email, passwords, references and amounts kept as isolated left-to-right text; digits follow A8. Then tests: a catalog completeness check (every key in both languages, no empty value), RTL layout widget tests, LTR isolation of technical values and a language switch mid-draft and mid-uncertain transfer. Arabic wording still needs a native speaker's review before release. Stories: US5.1; BR3.7; FR6.
- [x] **Step 11 — Accessibility, then tests.** Give every control a label and role, a logical focus order and visible focus; announce status changes (sending, sent, refused, uncertain, out of date, loading, empty, error); use 44dp minimum targets; never show status by colour alone; let text grow to 200% with reflow and scrolling at 320dp width with no clipped action. The decorative card and the non-working services tiles are announced as not available. Then widget tests with Flutter's `meetsGuideline` checks (tap target size, labelled tap targets, text contrast) and 200% text at 320dp for sign-in, wallet, send, review and history. VoiceOver and TalkBack walkthroughs on real devices remain release evidence. Stories: US5.2, US5.3; BR3.7.
- [x] **Step 12 — dev/stg/prd builds and the app icon, then tests.** Add Android product flavours and iOS build configurations and schemes for `dev`, `stg` and `prd`, each with its own app identifier suffix and display name, reading its own C4 file through `--dart-define-from-file`. Extend `tool/check_env_config.dart` and `lib/config/environment_config.dart` so a missing, extra, secret-looking or cross-environment value fails the build and the app refuses to start before showing private data. Generate launcher icons from the bolt-only mark with `flutter_launcher_icons`. Then tests for config validation in all three environments and the fail-closed start. Stories: US6.2; BR3.8; NFR9.
- [x] **Step 13 — Fake-backed integration journeys, then run them.** Extend `integration_test/` with journeys that run on an iOS simulator and an Android emulator against `lib/main_fake.dart`: sign-up, confirm, sign-in, wallet, send, result, history; a lost answer then **Try again** with the same key; offline disable; Arabic layout and a language switch. Record iOS and Android results separately, and label them fake-backed. Live journeys against a deployed `dev` (real Cognito and U2) stay pending until the person authorises the dev deploy. Stories: US6.2, US6.4; NFR14.
- [x] **Step 14 — CI, README and local gates.** Keep the existing CI steps (lockfile, format, analyze, `swagger_parser --check`, tests with coverage, the 80% floor as its own step, C4 example check, Gitleaks) and add the ARB catalog check and an Android debug build of the `dev` flavour with the example C4. Update the README with the one setup command, the one test command, the flavour build commands and the prerequisites. Run every local gate. Stories: US6.2; NFR14.
- [x] **Step 15 — Written acceptance journey.** Add `docs/acceptance-journey.md` in RaadMobile: the steps that check the SOW success criteria on a deployed environment (secure sign-in, the 1000 simulated SAR opening credit, a correct transfer and balance, duplicate refusal and replay, history, and that it runs on AWS), with what each step proves and where its evidence goes. It is a procedure; nothing in it is claimed as run. Stories: US6.4; BR3.8.
- [x] **Step 16 — Rework for review findings R-01 and R-03 (the person reopened U3 for them on 18 November, message 8200a3be).** (a) R-01, log privacy: add `test/log_privacy_test.dart`, which runs the sign-in, wallet, send (including a lost answer and Try again), history and sign-out flows against the fakes while capturing everything written through `print`, `debugPrint` and `dart:developer` `log` (zone print override and a `debugPrint` replacement), and fails if any captured text contains a synthetic password, confirmation code, token, email address, display name, amount, request key or cursor. Add `tool/check_no_logging.dart`, which fails when any file under `lib/` outside `lib/api/generated/` and `lib/l10n/` calls `print(`, `debugPrint(`, `log(` from `dart:developer` or `stdout`/`stderr`, and run it as its own step in `.github/workflows/ci.yml` and in the README's local gates. (b) R-03, third-party marks: remove the "VISA" wordmark and the "Add to Apple Wallet" chip from the decorative card in `lib/widgets/virtual_card.dart`, and the Apple Pay "coming soon" message with them; keep the card visibly a simulated RAAD card (RAAD wordmark, masked number, and a "Demo card" label in both languages, announced as not available). Update the ARB catalogs and the card's widget and accessibility tests. Then re-run format, analyze, the catalog check, the full suite with coverage and the 80% check, and the Android dev debug build. No AWS call. Stories: US5.1, US5.2; NFR10.10; review-01 R-01, R-03.
- [ ] **Step 17 — Record evidence, independent review and handoff.** Update checked steps only when actually done. Write the source manifest (paths named through the registered RaadMobile-u3 checkout), the code summary with exact command results, and requirement-level traceability. Separate fake-backed results from live checks, and list what is still owed: live dev journeys, VoiceOver/TalkBack walkthroughs, Arabic wording review, the A8 digit decision, TestFlight and Play distribution. Obtain the architecture review and the person's U3 checkpoint, then publish through `aidlc unit publish u3-mobile-app`. Push the branch and open the stacked RaadMobile PR only when the person approves. Stories: all U3 stories.

## Story-to-Step Traceability

| Story | Steps | Boundary |
|---|---|---|
| US1.1 Sign up | 5, 9, 10, 13 | C3 provider behaviour belongs to U4 |
| US1.2 Confirm my email and get my wallet | 5, 6, 9, 13 | U2 creates the wallet; the app retries setup safely |
| US1.3 Sign in | 5, 9, 13 | One refusal for wrong password, unknown and unconfirmed |
| US1.4 Sign out | 5, 9 | Clears private state and navigation |
| US1.5 Reset a forgotten password | 5, 9 | Code invalidation is U4's P7 check |
| US1.6 Stay signed in | 5 | Fixed 30-day refresh from U4; the 31-day idle rule is the app's |
| US2.2 See when my balance may be out of date | 6 | No fabricated zero |
| US3.3 Stay within the amount limits | 3, 4, 7 | Server stays authoritative |
| US3.4 Be stopped when my balance is too low | 4, 7 | |
| US3.5 Be stopped when the recipient is not valid | 3, 7 | Rate limits are U4's |
| US3.6 Never send the same transfer twice | 3, 4, 7, 13 | Replay is U2's; the app keeps one key per intent |
| US3.8 Know what happened when the answer is lost | 3, 4, 7, 13 | Same-key Try again only with U2 replay |
| US3.9 Not send while offline | 7, 13 | No queued writes |
| US4.2 See money I have received | 8 | |
| US4.3 Load a long history page by page | 3, 8 | Opaque cursor from U2 |
| US4.4 See a clear message when there is nothing to show | 8 | |
| US5.1 Use the app in Arabic or English | 2, 10, 13 | Native wording review is release evidence |
| US5.2 Use the app with a screen reader and larger text | 11 | Device walkthroughs are release evidence |
| US5.3 See a loading, empty or error view on every data screen | 6, 8, 11 | |
| US6.2 Check the app in every environment | 2, 3, 12, 13, 14 | Real C4 files need deployed environments |
| US6.4 Accept the MVP against the SOW's success criteria | 13, 15 | Live acceptance waits for the deploy |
| All | 1, 17 | Baseline and evidence |
| Review-01 R-01 (log privacy) and R-03 (third-party marks) | 16 | A test and a CI check guard logging; the decorative card carries no third-party marks |

## Change Surface and Compatibility

Primary changes in RaadMobile: `lib/auth/`, `lib/money/`, `lib/api/` (regenerated client and `money_service.dart`), `lib/screens/`, `lib/widgets/`, `lib/ui/`, new `lib/l10n/`, `lib/config/`, `lib/dev/`, `lib/app/`; `test/` and `integration_test/`; `contracts/pinned/` and `contracts/pins.yaml`; `pubspec.yaml` and `pubspec.lock`; `l10n.yaml`; `android/` and `ios/` flavour, scheme and icon files; `tool/`; `.github/workflows/ci.yml`; `README.md`; new `docs/acceptance-journey.md`. Existing U1 behaviour and the co-engineer's screens are extended in place, never duplicated. Existing tests change only where behaviour changes on purpose (for example English text moving to the catalogs, or U2 paging replacing U1's first-page-only rule).

## Acceptance Boundaries and Remaining Gates

Local completion means the source and tests above, format, analyze, the client-generation check, the 80% line floor, the catalog check, the flavour build and fake-backed simulator and emulator journeys. It does not prove the live system. Still owed after this stage: journeys against a deployed `dev` with real Cognito and U2, the U4 P1–P13 provider checks (P7 and P10 especially), VoiceOver and TalkBack walkthroughs on both platforms, a native Arabic wording review, the person's A8 digit decision, and TestFlight and Play internal distribution (which may need existing paid developer accounts; nothing is bought).

## Inputs

- U3 functional design (`functional-spec.md`, `rules.md`, `frontend-components.md`), the six NFR requirement and NFR design documents, and the infrastructure, pipeline and monitoring designs.
- Shared `requirements.md`, `stories.md`, `unit-of-work.md`, `unit-of-work-story-map.md`, `components.md`, `contract-summary.md` and the refined mockups and accessibility checklist.
- U2's C1 file at RaadMoneyService `2b3660b`; U4's C3/C4 contracts on Raad `main`.
- The person's decisions: bilingual frontend and the prd opening credit (77a32fc9); keep the co-engineer's UI (3eb4ad2d); the logo lockup and bolt-only icon.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.",
  "scope": "classic",
  "test_strategy": "standard",
  "project_type": "greenfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Methodology evidence**: We chose this mixed cadence at the practices interview. RAAD's central risk is money movement: balances must be right after every transfer, and a repeated request must never move money twice. In that small core of `RaadMoneyService` the tests are the specification, so writing them first costs little and catches the defects that matter most. Everywhere else, the org default cadence (test-after) keeps us on the short timeline. This posture differs from the org default only for the money-movement core.\n- **Ordering**: For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.\n- **Coverage**: Each backend repo (`Raad`, `RaadMoneyService` and later `RaadAiService`) and the mobile repo (`RaadMobile`) holds at least 80% line coverage on its own. The money-movement core in `RaadMoneyService` also holds at least 95% line and branch coverage. We never lower a floor to make a step pass, and coverage on `main` never decreases in any repo. `RaadWeb` is static HTML and CSS with no code to measure; its smoke test checks it after every deploy.\n- **Money-movement checks** (in `RaadMoneyService`, required in addition to coverage):\n  - Property-based tests with Hypothesis show that, for any sequence of transfers, the total money across all wallets stays the same and no balance goes below zero.\n  - A replay test shows that sending the same transfer request again returns the original result and moves money exactly once.\n  - A concurrency test shows that simultaneous transfers out of one wallet can never overdraw it. It runs against a real local container of the data store in Docker, not a mock.\n  - Rejection tests cover insufficient funds; a zero, negative or over-precise amount; an unknown recipient; a transfer to oneself; an unauthenticated caller; and access to another user's wallet.\n- **Test types** (Standard test strategy):\n  - Service repos (`RaadMoneyService`, and later `RaadAiService`): unit tests with pytest and Hypothesis, and integration tests against local containers in Docker.\n  - Infrastructure (`Raad`'s platform stacks and each service's own stacks): pytest tests of the CDK stacks, alongside the cdk-nag checks that run on every synth.\n  - `RaadMobile`: unit and widget tests with `flutter test`, and end-to-end tests with `integration_test` on an iOS simulator and an Android emulator.\n  - Deployed environments: each deployable repo's pipeline runs a smoke test against the environment after every deploy. A service's smoke test calls its deployed API, `RaadWeb`'s fetches the landing page, and `Raad`'s checks the shared pieces it deployed (for example that the API domain answers and a test user can sign in).\n- **CI**: Each repo's full suite runs in GitHub Actions on every pull request, and a pull request merges only when the suite is green. The suite runs again on every push to `main`. Any failure blocks.\n- **Setup**: Each repo's README documents one setup command and one test command, and lists that repo's prerequisites: in the Python repos, `uv`, Node.js for the AWS CDK CLI, and Docker where the tests or builds need it; in `RaadMobile`, the pinned Flutter SDK and, for the simulator tests and app builds, Xcode with CocoaPods and the Android SDK."
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - For the money-movement core in `RaadMoneyService` (amount validation, balance arithmetic, transfer rules and duplicate-request handling) we work test-driven (TDD), writing the failing tests first and then the code that makes them pass, and for every other layer in every repo (API handlers, data access, the platform and service infrastructure, the Flutter app and the landing page) we work test-after, implementing the layer and then writing and running its tests before the work lands.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:67e5bbb80db5d51b2847a7275866f774aaee32fcb4f9b6c3ad6d429836b14ece",
  "contract_sha256": "sha256:7d7f077a74e1c8ed59b1ec6ddd9f041d8db0c6a93d62e46cc8c573d062f59d5e"
}
```
