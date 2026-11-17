# Code Generation Plan — U5 Landing Page

Conversation language: English.

## Summary

- Builds: the static Arabic and English RAAD landing page (S12) and its per-environment hosting (private S3 behind CloudFront) in `RaadWeb`, with a build step, a smoke test and CI.
- Touches: `RaadWeb` (new): `site/` (pages, stylesheet, fonts), `raadweb/` (CDK stack), `scripts/` (build and smoke), `tests/`, `app.py`, `pyproject.toml`, `.github/workflows/`, `README.md`, `.gitignore`.
- Tests: about 40 pytest tests (page content and accessibility structure, build step, smoke script, CDK assertions), cdk-nag on every synth, and an automated axe scan of both pages in a headless browser.

This plan builds only U5, on a new branch `aidlc/u5-landing-page` in `RaadWeb`. Nothing is deployed, no asset is uploaded and no AWS API is called in this stage. The page calls no RAAD service.

## Decisions carried into this plan

1. **Hostnames and DNS.** The person registered `raadwallet.com` in Route 53, which replaces the design's free external DNS. The page is served at `dev.raadwallet.com`, `stg.raadwallet.com` and `raadwallet.com` (`prd`), with alias records in the existing hosted zone. Hostname, certificate ARN and zone ID are deploy inputs, never written into code. The API certificate covers only `*.api.raadwallet.com`, so the page needs its own free ACM certificate in `us-east-1` for `raadwallet.com` and `*.raadwallet.com`. Requesting it is a deploy step, not part of this stage.
2. **Addresses for each language.** `/` opens the Arabic page (`lang="ar" dir="rtl"`) and `/en/` the English page. Each links to the other with `hreflang`. The page has no JavaScript at all, so the language switch is two plain links.
3. **Copy.** The wording follows the S12 mockup and the functional design's draft. Title "Send money in seconds." / "أرسل المال في ثوانٍ." The description says RAAD is a demo wallet for sending simulated Saudi riyals between RAAD users, and that no real payments are processed. It is a draft for the customer to approve (A9), and the Arabic needs a native review before release.
4. **Test access.** "Request test access" is one `mailto:` link addressed to both public contacts: `abdulaziz.alrubai@outlook.com` (from the design) and `zyad.alamri777@gmail.com` (added by the person at plan approval). It has a translated subject. Both addresses are also shown as visible, selectable text, isolated left-to-right inside the Arabic page. The page never says a request was sent. There are no app-store or TestFlight links until real ones exist.
5. **Brand.** The person sent a sphere icon at plan approval, then clarified during the build that the logo is the horizontal lockup: a silver lightning bolt beside the Arabic wordmark "رعد" with "RAAD" underneath. The page uses that lockup, as a web-sized copy in `site/assets/` shown 240 px wide (200 px on phones), with `mix-blend-mode: screen` so its black background merges into the page. The lockup carries the name, so the image has `alt="رعد RAAD"` and there is no repeated visible text name. The sphere image is not used. The page uses the app's colour tokens, which suit the logo's silver-on-black: `bg` #0A0C10, `surface` #12151B, `text-primary` #F2F4F8, `text-secondary` #AEB6C4, `accent` #5BA8FF, `on-accent` #06121F. IBM Plex Sans Arabic is self-hosted under its open font licence, falling back to the system font stack if the files cannot be bundled.
6. **Logging and firewall.** No visitor logging, per the privacy design: CloudFront access logs and S3 server access logs stay off. There is no WAF on this static page, since it has no dynamic content and the cost is not authorized. The matching cdk-nag rules (`AwsSolutions-CFR1`, `CFR2`, `CFR3`, `S1`) are suppressed in code, each with that reason written beside it.
7. **Coverage.** The team practice sets no coverage floor for `RaadWeb`'s static files. The repo's Python (stack, build and smoke scripts) still gets an 80% line floor, matching the other Python repos.

## Implementation Steps

- [x] **Step 1 — Project skeleton and runner.** Create `pyproject.toml` (pinned Python 3.12, `uv`, CDK v2, cdk-nag, pytest with pytest-cov, Ruff, strict mypy, `pip-audit`), `uv.lock`, `cdk.json`, `.gitignore` and the package folders. Run `uv run pytest` once on an empty `tests/` with `conftest.py` so the runner works before the first test, and record the exact unit-scoped commands in `unit-test-instructions.md`.
- [x] **Step 2 — Pages and stylesheet (test-after).**
  - **Pages:** `site/index.html` (Arabic) and `site/en/index.html` (English). Each has:
    - a skip link as the first focusable item;
    - `header`, `main` and `footer`;
    - one `h1`;
    - the logo and the RAAD name;
    - the language links;
    - the description and the simulated-money notice;
    - the "Request test access" link with both visible addresses;
    - `© 2026 RAAD`.
  - **Stylesheet:** `site/assets/styles.css`, a single centred column up to 720 px wide with a 16 px side margin. It has a visible focus ring, 48 px-high main button, logical properties so the Arabic page mirrors, no horizontal scroll at 320 px and with text at 200%, and `prefers-reduced-motion` respected.
  - **Not allowed:** scripts, forms, inputs, cookies, external URLs other than the `mailto:` link, and calls to any RAAD service.
- [x] **Step 3 — Page tests.** `tests/test_pages.py` parses both pages with the standard-library HTML parser. It checks:
  - the `lang` and `dir` values;
  - the title and `h1`;
  - the skip link is first and its target exists;
  - the landmarks;
  - the language links and `hreflang`;
  - the contact link names exactly the two approved addresses, and both are visible and isolated left-to-right;
  - the logo image exists, is local, and has `alt="رعد RAAD"`;
  - the simulated-money notice in both languages;
  - every internal link and asset resolves.

  It also checks what the pages must not contain: `<script>`, `<form>`, `<input>`, `<iframe>`, inline event handlers, external resources, and store or TestFlight links. A matching test checks the stylesheet has no `@import` and no external `url()`.
- [x] **Step 4 — Build step (test-after).** `scripts/build_site.py` copies `site/` to `dist/`, renames the stylesheet and fonts with a content hash (for example `styles.3f2a9c1b.css`), rewrites the references in both pages, and fails on a missing reference. Add `tests/test_build_site.py` covering the hash names, the rewritten links, a stable result when nothing changed, and failure on a broken reference.
- [x] **Step 5 — Hosting stack (test-after).** `raadweb/stack.py` and `app.py`. The site goes on a private, encrypted, versioned S3 bucket with all public access blocked, SSL enforced, and `RETAIN` with deletion protection in `stg` and `prd`. CloudFront uses origin access control on the S3 REST origin, HTTPS only, the custom hostname and certificate, and the `TLSv1.2_2021` minimum protocol. A response-headers policy sets:
  - CSP `default-src 'none'; style-src 'self'; font-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`;
  - HSTS;
  - `X-Content-Type-Options: nosniff`;
  - `Referrer-Policy: no-referrer`.

  The cache policy keeps HTML short and revalidating, and caches hashed assets for a long time. A CDK `BucketDeployment` publishes `dist/` without deleting older objects and invalidates the two HTML paths. An optional Route 53 alias record is made when a zone ID is given. Inputs: `RAAD_ENVIRONMENT`, `RAADWEB_DOMAIN_NAME`, `RAADWEB_CERTIFICATE_ARN` (must be in `us-east-1`) and optional `RAAD_HOSTED_ZONE_ID`. A `cloudfront.net` hostname or a missing certificate is refused.
- [x] **Step 6 — Stack tests.** `tests/test_stack.py` uses CDK assertions to check:
  - the bucket settings and the OAC-only bucket policy for this distribution;
  - the TLS minimum, redirect to HTTPS and the security headers;
  - the cache behaviours, no logging and the alias record;
  - the `dev`/`stg`/`prd` differences and the input validation;
  - cdk-nag has no unsuppressed finding, and every suppression has a reason.
- [x] **Step 7 — Smoke test (test-after).** `scripts/smoke_site.py <base-url>` fetches `/` and `/en/` over HTTPS with TLS 1.2 as the minimum. For each page it checks:
  - the status, `lang` and `dir`;
  - the product name, description and both contact addresses;
  - the hashed stylesheet loads;
  - the security headers are present;
  - no request goes to a RAAD API or sign-in host.

  Any failure exits non-zero; an empty page is never a pass. Add `tests/test_smoke_site.py` against a local test server and stubbed responses, including a missing page, the wrong contact and a missing header.
- [x] **Step 8 — Automated accessibility scan.** `tests/browser/test_axe.py` serves `dist/` locally and runs axe-core on both pages in headless Chromium through Playwright. It requires no WCAG 2.1 AA violations and checks reflow at 320 px. It carries a `browser` marker. If a browser can't be installed on a machine, the run is reported as not run, never as passed.
- [x] **Step 9 — CI and deploy workflow.**
  - **`ci.yml`, on every pull request and push to `main`:** `uv sync --locked`, Ruff, mypy, pytest with the coverage floor, the build step, the browser scan, `pip-audit`, `cdk synth` for `dev`, `stg` and `prd` with fixture inputs and cdk-nag, and gitleaks with `GITHUB_TOKEN`, `pull-requests: read` and full history.
  - **`deploy-dev.yml`, on push to `main`:** it runs only when `AWS_ROLE_ARN_DEV` is configured, so it is skipped cleanly until then. It builds, deploys with GitHub OIDC and then runs the smoke test against the real host.
  - **`stg`/`prd` promotion** is left to the Deployment Pipeline stage.
- [x] **Step 10 — README.** Update `RaadWeb/README.md`, which the person already has, as the team practice requires. Add prerequisites (`uv`, Python 3.12, Node.js for the CDK CLI, a Chromium for the scan), one setup command, one test command, the build and smoke commands, and the deploy inputs. Leave out account IDs, the alert email and secrets.
- [x] **Step 11 — Run every check.** Ruff format and lint, strict mypy, the full suite with the coverage floor, the browser scan, `pip-audit`, the build step, and `cdk synth` with cdk-nag for `dev`, `stg` and `prd` using fixture inputs and no AWS credentials. Report any check that cannot run; never lower a threshold.
- [x] **Step 12 — Record.** Write `source-manifest.json`, `traceability.json` and `code-summary.md`. The summary covers what was built, every command and its result, the decisions above, and the checks that need a deployed site or a person:
  - the landing certificate request and deploy;
  - the both-language smoke test on each environment;
  - a keyboard and screen-reader pass;
  - the native Arabic wording review;
  - the customer's approval of the copy.

  Update `unit-test-instructions.md` if a command changed.

### Revision 1 — fixes the person asked for after the first review ("Fix it and continue")

The first architecture review (`reviews/review-01.md`) raised six minor points. These steps fix R-01, R-02, R-03 and R-05. R-04 (the index-rewrite function runs only in CloudFront) and R-06 (deployed and human checks) need a real deploy or a person, so they are carried forward and recorded, not built.

- [x] **Step 13 — Not-found page and favicon (R-01, test-after).** Add `site/404.html`: a bilingual (Arabic first, then English) static page with the same header, a short "page not found" message and links back to `/` and `/en/`. No scripts, and the same CSP. CloudFront maps S3's 403 and 404 for unknown paths to `/404.html` with a real `404` status and a short error-cache time. Add a favicon from the lockup's bolt (`site/favicon.ico` 32×32 plus `site/assets/icon-180.png` for Apple touch), linked from every page with `<link rel="icon">`. Extend the page tests to cover the 404 page (structure, both languages, no scripts, links resolve) and the favicon links. Extend the stack tests for the error responses. Extend the smoke script to check that an unknown path returns the 404 page with status 404.
- [x] **Step 14 — Pin tool versions (R-02).** In `ci.yml` and `deploy-dev.yml`, install the CDK CLI at an exact version (`npm install --global aws-cdk@<exact>`, matching the `aws-cdk-lib` major in `uv.lock`). Pin every third-party action (`actions/*`, `astral-sh/setup-uv`, `aws-actions/configure-aws-credentials`, `gitleaks/gitleaks-action`) to a full commit SHA, with the version in a comment. Add a test that fails if a workflow uses an action by tag or installs an unpinned CDK CLI.
- [x] **Step 15 — Bucket cleanup (R-03, test-after).** Add a lifecycle rule: delete noncurrent object versions after 30 days, keeping the 3 most recent, and abort incomplete multipart uploads after 7 days. In `dev` only, set the bucket to `DESTROY` with `autoDeleteObjects`, so the `dev` stack can be deleted without emptying it by hand. `stg` and `prd` stay `RETAIN`. Acknowledge any new cdk-nag finding from the auto-delete function with its reason in code. Add stack tests for the rule and for the per-environment removal settings.
- [x] **Step 16 — Language alternates in the page head (R-05).** Each page gets `<link rel="alternate" hreflang="ar" href="/">`, `<link rel="alternate" hreflang="en" href="/en/">`, `<link rel="alternate" hreflang="x-default" href="/">` and a `<link rel="canonical">` to itself. These use root-relative addresses, because the same build is promoted from `dev` to `stg` to `prd`, and that limitation is recorded. Extend the page tests.
- [x] **Step 17 — Run every check again.** Ruff, strict mypy, the full suite with the coverage floor and the browser scan (`RAADWEB_REQUIRE_BROWSER=1`), `pip-audit`, the build step, and `cdk synth` with cdk-nag for `dev`, `stg` and `prd` using fixture inputs and no AWS credentials. Never lower a threshold.
- [x] **Step 18 — Record the revision.** Update `source-manifest.json` with every new or changed path, and add a "Revision after review 1" section to `code-summary.md`. It covers what changed for R-01, R-02, R-03 and R-05, the commands and results, and R-04 and R-06 carried forward with the reason. Update `unit-test-instructions.md` if a command changed.

## Story and Requirement Traceability

| Plan step | Story / acceptance coverage |
|---|---|
| Steps 2–4 | US6.3: product name, short description and how to get access in Arabic and English (AC6.3.1); no money or sign-in calls and no wallet data (AC6.3.2); BR5.1, BR5.2, BR5.3, BR5.4; FR8.1 |
| Step 8 | WCAG 2.1 AA target and the landing checklist rows P6, P8, O2, O8 and R3; BR5.4 |
| Steps 5–7, 9 | US6.2: the landing page deploys to `dev`, `stg` and `prd` and passes its smoke test (AC6.2.1); BR5.5; FR7.1 |
| Steps 13–16 | Review 1 fixes: R-01 not-found page and favicon (BR5.4, NFR9.10), R-02 pinned delivery tools (NFR14.10), R-03 bucket cleanup (NFR5.10), R-05 language alternates (BR5.1) |

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
