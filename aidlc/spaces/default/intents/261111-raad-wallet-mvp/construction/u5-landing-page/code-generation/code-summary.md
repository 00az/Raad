# Code Summary — U5 Landing Page

Conversation language: English.

## What Was Built

U5 is built in `RaadWeb` (`00az/RaadWeb`) on the branch `aidlc/u5-landing-page`, made from `main` (`3563326`). Nothing is committed, pushed, deployed or uploaded, and no AWS API was called.

- **Pages (S12).** `site/index.html` (Arabic, `lang="ar" dir="rtl"`, served at `/`) and `site/en/index.html` (English, `lang="en" dir="ltr"`, served at `/en/`). Plain HTML with no JavaScript, forms, inputs, cookies, analytics or inline styles. Each page has a skip link as its first focusable item; `header`, `main` and `footer`; one `h1`; the RAAD lockup; a language switch (two plain links with `hreflang`, the current one marked `aria-current="page"`); the description; the simulated-money notice, labelled in text and not only by colour; the "Request test access" `mailto:` link; both public contact addresses as visible, selectable, left-to-right `bdi` text; and `© 2026 RAAD`. Every link has a `data-testid`.
- **Stylesheet.** `site/assets/styles.css` uses the app's colour tokens as CSS variables in one `:root` block. The layout is a single centred column up to 720 px wide with a 16 px side margin. It uses logical properties, so the Arabic page mirrors, and has a 2 px accent focus ring, a 48 px-high main button and 44 px language links. Addresses wrap and do not scroll. Transitions run only under `prefers-reduced-motion: no-preference`. IBM Plex Sans Arabic is self-hosted (Arabic and Latin subsets, weights 400 and 600, from `@fontsource/ibm-plex-sans-arabic` 5.3.0) with its SIL Open Font License in `site/assets/fonts/OFL.txt`, and the system font stack is the fallback.
- **Logo.** `site/assets/raad-logo.webp` is made from the horizontal lockup the person sent during the build. The image was trimmed to the logo (brightness threshold 20, plus 24 px of black padding), resized to 720×337 and saved as lossy WebP at quality 90, which comes to 13,266 bytes (PNG would have been 123,519 bytes). It is shown at 240 px wide, or 200 px at phone width, with `mix-blend-mode: screen` and `alt="رعد RAAD"`. No copy of the original upload or of the sphere image is in the repo.
- **Build step.** `scripts/build_site.py` copies `site/` to `dist/` and gives every stylesheet, font and image under `assets/` a content-hashed name, such as `styles.9d475f05.css`. It rewrites the font URLs in the stylesheet and the asset URLs in both pages. It fails, and writes nothing, on a missing reference, an external URL or a non-root-relative link. It will not replace a folder that it did not build itself.
- **Hosting stack.** `raadweb/stack.py` holds the stack and `app.py` the entry point; `RaadWeb-<env>` is one stack per environment. It has these parts:
  - **Bucket:** private and encrypted (SSE-S3), versioned, with all public access blocked, owner-enforced, and SSL and TLS 1.2 required by the bucket policy. It is `RETAIN` with stack termination protection in `stg` and `prd`.
  - **CloudFront:** origin access control on the S3 REST origin, so only this distribution can read objects. Viewers are redirected to HTTPS, and the custom hostname uses its ACM certificate with the `TLSv1.2_2021` minimum. Only GET and HEAD are allowed, logging is off and there is no WAF.
  - **Security headers:** a response-headers policy sets the planned CSP, HSTS for one year, `nosniff`, `Referrer-Policy: no-referrer` and `X-Frame-Options: DENY`.
  - **Caching:** pages are cached for at most a minute at the edge and revalidated by browsers; `/assets/*` is cached for a year. No query strings, cookies or headers are in the cache key.
  - **Upload:** one `BucketDeployment` per file type sets each type's content type explicitly, uploads the hashed assets first, then the pages, and then invalidates `/index.html` and `/en/index.html`. `prune` is off.
  - **DNS:** optional Route 53 A and AAAA alias records are created when `RAAD_HOSTED_ZONE_ID` is set.
  - **Inputs:** `raadweb/config.py` checks them. It refuses a missing or `cloudfront.net` hostname, a missing certificate, a certificate outside `us-east-1`, an unknown environment and a malformed zone ID.
- **Smoke test.** `scripts/smoke_site.py <base-url>` fetches `/` and `/en/` over HTTPS with TLS 1.2 as the minimum and refuses redirects away from HTTPS. For each page it checks:
  - the status, content type and a non-empty body;
  - `lang` and `dir`;
  - the RAAD name in the title and the logo's alt text;
  - the description;
  - the `mailto:` naming exactly the two contacts, and both addresses shown;
  - that the page names no other host;
  - the four security headers;
  - that the hashed stylesheet loads.

  Any failed check exits 1; an empty page is never a pass. It retries the whole run (3 attempts, 20 s apart by default) to ride out DNS propagation after a deploy.
- **Shared policy.** `raadweb/web_policy.py` is the single source of truth for the headers, cache-control values and content types; the stack, the smoke test and the test server all use it. `raadweb/content.py` holds the approved public facts that the smoke test checks.
- **CI and deploy.**
  - **`ci.yml`** runs on every pull request and push to `main`, with `contents: read`, `pull-requests: read` and full history. It runs `uv sync --locked`, Ruff format and lint, mypy, the full pytest suite including the browser scan with the 80% floor, the build, `pip-audit`, `cdk synth` with cdk-nag for `dev`, `stg` and `prd` using fixture inputs and no AWS credentials, and gitleaks with `GITHUB_TOKEN`.
  - **`deploy-dev.yml`** runs on push to `main`. Its first step checks `AWS_ROLE_ARN_DEV` inside the job, where `dev` environment variables are visible. Until the role is set, every later step is skipped and the run stays green. Once it is set, the workflow reruns the checks, assumes the role through GitHub OIDC, deploys `RaadWeb-dev` and smoke-tests `https://$RAADWEB_DOMAIN_NAME`.
- **README.** `README.md` keeps the person's existing text and adds:
  - what is in the repo;
  - prerequisites;
  - one setup command and one test command;
  - the other checks;
  - build, synth, smoke and rollback;
  - the deploy inputs.

  It contains no account ID, alert address or secret.

## Files Created and Modified (RaadWeb)

| Area | Files |
|---|---|
| Modified | `README.md` |
| Project | `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, `cdk.json`, `app.py` |
| Site | `site/index.html`, `site/en/index.html`, `site/assets/styles.css`, `site/assets/raad-logo.webp`, `site/assets/fonts/` (4 `.woff2` files and `OFL.txt`) |
| Stack | `raadweb/__init__.py`, `raadweb/config.py`, `raadweb/content.py`, `raadweb/stack.py`, `raadweb/web_policy.py` |
| Scripts | `scripts/__init__.py`, `scripts/build_site.py`, `scripts/page_parser.py`, `scripts/smoke_site.py` |
| Tests | `tests/__init__.py`, `tests/conftest.py`, `tests/site_server.py`, `tests/test_pages.py`, `tests/test_build_site.py`, `tests/test_smoke_site.py`, `tests/test_stack.py`, `tests/browser/__init__.py`, `tests/browser/conftest.py`, `tests/browser/test_axe.py` |
| CI | `.github/workflows/ci.yml`, `.github/workflows/deploy-dev.yml` |

That is 37 paths, all listed in `source-manifest.json`. `dist/` and `cdk.out/` are build output and are git-ignored.

## Decisions Carried From the Plan

1. **Hostnames and DNS.** The hostname, certificate ARN and zone ID are deploy inputs (`RAADWEB_DOMAIN_NAME`, `RAADWEB_CERTIFICATE_ARN`, `RAAD_HOSTED_ZONE_ID`) and are never written into code. A `cloudfront.net` name or a missing certificate is refused, and the certificate must be in `us-east-1`. Requesting the landing certificate is a deploy step and was not done here.
2. **Addresses for each language.** `/` is Arabic and `/en/` is English. They link to each other with `hreflang`, without JavaScript.
3. **Copy.** The text follows S12 and the functional design's draft: "Send money in seconds." / "أرسل المال في ثوانٍ.", the demo-wallet description, and the notice that money is simulated and no real payments are processed. It is a draft for the customer to approve (A9), and the Arabic needs a native review.
4. **Test access.** One `mailto:` link is addressed to both public contacts named in plan decision 4, with a translated subject: "طلب وصول تجريبي إلى رعد" / "RAAD test access request". Both addresses are visible, selectable and isolated left to right. The page never says a request was sent and has no store or TestFlight links. It says the app is not in the stores yet and explains how to ask for access.
5. **Brand.** The logo sits in the header and uses the app's colour tokens. It changed during the build; see Deviations.
6. **Logging and firewall.** CloudFront and S3 access logs are off and there is no WAF. `AwsSolutions-S1`, `CFR1`, `CFR2` and `CFR3` are acknowledged in code, each with its reason beside it.
7. **Coverage.** The repo's Python (`raadweb/`, `scripts/`) holds an 80% line floor. The result is 95.49% combined line and branch coverage; line coverage alone is 484 of 497 statements, 97.4%.

The team's test-after ordering was followed for every layer: pages, then page tests; build, then build tests; stack, then stack tests; smoke script, then smoke tests; then the browser scan.

## Implementation Decisions

- **cdk-nag 3.0.2.** This is the current release. It drops `NagSuppressions` in favour of CDK's native `Validations.of(construct).acknowledge(id, reason)`, and any unacknowledged finding fails synth with `ValidationFailed`. `app.py` writes the acknowledgements into the template metadata (`write_suppressions_to_cloud_formation=True`), and a test checks that every one carries a reason. There are 14 distinct acknowledgements:
  - four plan-decided: `S1`, `CFR1`, `CFR2`, `CFR3`;
  - ten on the upload function that aws-cdk-lib's `BucketDeployment` creates: `IAM4` (basic execution role); `IAM5` for `s3:GetObject*`, `GetBucket*`, `List*`, `DeleteObject*` and `Abort*`; `IAM5` for objects in the site bucket and in the CDK assets bucket; `IAM5` for `Resource::*` (the CloudFront invalidation grant); and `L1` (the runtime chosen by CDK).

  The assets-bucket finding is built from the stack's own account at synth time, so no account ID is hard-coded. The sibling repos still use cdk-nag 2.x with `NagSuppressions`.
- **Index rewrite at the edge.** S3's REST endpoint, which OAC requires, has no index documents, so `/en/` would not reach `en/index.html`. A small CloudFront Function (viewer request) maps a path ending in `/` to its `index.html` and redirects `/en` to `/en/`. It runs in CloudFront, not in the pages, which still have no JavaScript. A test runs the function in Node.js for `/`, `/en/`, `/en` and an asset path.
- **Content types are set, not guessed.** There is one `BucketDeployment` per file type in the build (`.css`, `.html`, `.txt`, `.webp`, `.woff2`), each with an explicit content type, so `nosniff` never meets a guessed type. The stack refuses a build that contains a type it has no content type for.
- **Hashing.** Hashing covers the logo as well as the stylesheet and fonts. Everything under `/assets/*` is cached for a year, so an unhashed logo would not update.
- **Cache-Control values.** Pages use `public, max-age=0, s-maxage=60, must-revalidate`. Assets use `public, max-age=31536000, immutable`.
- **Other stack choices:**
  - `PRICE_CLASS_200`, which includes the Middle East edge locations;
  - HSTS without `includeSubDomains`, so the page does not commit `api.` or other subdomains;
  - `X-Frame-Options: DENY` added alongside CSP `frame-ancestors 'none'`;
  - A and AAAA alias records, because IPv6 is on;
  - the `dev` bucket uses `DESTROY` without an auto-delete Lambda, so it goes with the stack once emptied.
- **Packaging.** The repo is an editable hatchling package (`raadweb`, `scripts`), so `uv run python scripts/build_site.py` imports the shared parser without editing `sys.path`. That parser is `scripts/page_parser.py`, built on the standard-library `HTMLParser` and used by the build, the smoke test and the page tests.
- **Browser scan.** The local test server sends the production security headers, so the pages are scanned under the real CSP, and it never lists folders, as S3 behind CloudFront would not. If Chromium cannot start, the browser tests are skipped with "NOT RUN: …"; with `RAADWEB_REQUIRE_BROWSER=1`, which CI sets, they fail instead.
- **Approved facts for the smoke test.** The approved public contacts, product name, logo alt text and descriptions live in `raadweb/content.py`, apart from the fetch code.
- **mypy.** mypy is strict on `raadweb`, `scripts` and `app.py`, as planned (configured in `pyproject.toml`, so `uv run mypy` and the documented `uv run mypy raadweb scripts app.py` both work). `uv run mypy tests` is also clean.

## Commands Run and Results

All commands ran from `/Users/as/Developer/projects/RaadWeb` on branch `aidlc/u5-landing-page`, with Python 3.12.15 under uv 0.13.5, Node.js 26.12.1 and CDK CLI 2.1146.1.

| Command | Result |
|---|---|
| `uv lock`, then `uv sync --locked --all-groups` | 58 packages resolved and installed. Versions include aws-cdk-lib 2.277.0, constructs 10.8.1, cdk-nag 3.0.2, pytest 9.2.0, pytest-cov 7.1.0, ruff 0.17.5, mypy 2.4.1, pip-audit 2.10.1, playwright 1.65.2 and axe-playwright-python 0.1.8 (axe-core 4.12.1). |
| `uv run pytest` on the empty `tests/` (Step 1) | "no tests ran", exit 5: the runner works before the first test. |
| `uv run ruff format --check .` | 21 files already formatted, exit 0. |
| `uv run ruff check .` | All checks passed, exit 0. |
| `uv run mypy` / `uv run mypy raadweb scripts app.py` | No issues in 10 source files, exit 0. `uv run mypy tests` also passes. |
| `uv run pytest tests/test_pages.py tests/test_build_site.py tests/test_smoke_site.py tests/test_stack.py --no-cov -q` | 79 passed, exit 0. |
| `uv run playwright install chromium` | Installed, exit 0. |
| `uv run pytest tests/browser/test_axe.py -m browser --no-cov -q` (with `RAADWEB_REQUIRE_BROWSER=1`) | 12 passed, exit 0. |
| `uv run pytest tests --cov=raadweb --cov=scripts --cov-report=term-missing --cov-fail-under=80 -q` (with `RAADWEB_REQUIRE_BROWSER=1`) | 91 passed. Coverage 95.49%, floor 80% reached, exit 0. |
| `uv run python scripts/build_site.py --out dist` | Built 9 files, with 6 assets renamed, for example `/assets/styles.css` to `/assets/styles.9d475f05.css`. Exit 0. |
| `uv run pip-audit` | No known vulnerabilities found, exit 0. The local `raadweb` package itself is not on PyPI and is skipped. |
| `RAAD_ENVIRONMENT=dev RAADWEB_DOMAIN_NAME=dev.raad.example.test uv run cdk synth -q` | Exit 0: 22 resources, no cdk-nag violation. |
| Same for `stg` (`stg.raad.example.test`) and `prd` (`raad.example.test`) | Exit 0 each: 22 resources, no violation. `prd` has termination protection. |
| Same `dev` synth with `CDK_DEFAULT_ACCOUNT` unset | Exit 0: the acknowledgements hold in an account-agnostic synth. |
| First `dev` synth, before the upload-function acknowledgements | Exit 1 with 10 findings. This confirmed that cdk-nag blocks synth. |
| gitleaks v8.30.1 (`ghcr.io/gitleaks/gitleaks`, Docker) `dir` scan over a copy of the 37 files to be committed | No leaks found, exit 0. |
| Content check of the 32 text files to be committed | No alert address. No 12-digit number other than the fixture account (`111111111111`) and the zero tail of the fixture certificate UUID. No email addresses other than the two approved public contacts and one `example.com` address in a wrong-contact test. No JPEG anywhere in the repo. |
| Workflow YAML parse (PyYAML 6.0.3) | `ci.yml` has 1 job with 14 steps; `deploy-dev.yml` has 1 job with 15 steps. |

Every synth ran with the credential chain blanked: `AWS_PROFILE` unset, `AWS_CONFIG_FILE` and `AWS_SHARED_CREDENTIALS_FILE` set to `/dev/null`, `AWS_EC2_METADATA_DISABLED=true`. The fixture inputs were `CDK_DEFAULT_ACCOUNT=111111111111`, `CDK_DEFAULT_REGION=us-east-1` and the certificate `arn:aws:acm:us-east-1:111111111111:certificate/00000000-0000-0000-0000-000000000000`. The CDK CLI also printed an informational note that 85 feature flags are not configured; the sibling repos' `cdk.json` files set none either.

## Test Coverage Summary

| Component | Test file | Tests | What they check |
|---|---|---|---|
| Pages and stylesheet | `tests/test_pages.py` | 28 | For both pages: `lang` and `dir`; the head; title and the single `h1`; the skip link first with its target; landmarks and the named language nav; the language links with `hreflang`; the `mailto:` naming exactly the two contacts with the translated subject; visible LTR addresses; the local logo with `alt="رعد RAAD"`; the description and notice; internal links resolving. They also check for no scripts, forms, frames, inline styles or handlers, no external URLs, no store links, no other addresses, and test IDs on every link. For the stylesheet: no `@import` or external `url()`, and the layout, focus, logo and motion rules. |
| Build step | `tests/test_build_site.py` | 13 | Hashed names; rewritten page and stylesheet links; a stable result when nothing changed; cascading renames; stale files removed; broken page and stylesheet references; unsafe output folders; CLI exit codes. |
| Smoke script | `tests/test_smoke_site.py` | 12 | A correct build passes all 26 checks. These fail: a missing page, an empty page, the wrong contact, a missing CSP, HSTS or `nosniff` header, a reference to another host, and a missing stylesheet. Also: plain HTTP is refused, TLS 1.2 is the minimum, redirects cannot leave HTTPS, and the CLI retries and reports a down site. |
| Hosting stack and inputs | `tests/test_stack.py` | 26 | The bucket; the OAC-only bucket policy for this distribution; HTTPS and TLS on the custom host with no logs or WAF; the headers; the cache policies; the upload content types, cache-control and invalidation paths; upload order; the index rewrite run in Node.js (4 cases); alias records only with a zone; `dev`/`stg`/`prd` retention and termination protection; cdk-nag passes with a reason on every acknowledgement; cdk-nag blocks an unacknowledged bucket; an unbuilt site is refused; input validation (1 accepting test and 8 refusals). |
| Browser scan | `tests/browser/test_axe.py` | 12 | For both pages in headless Chromium, served with the production headers: axe-core 4.12.1 with the WCAG 2.0/2.1 A and AA tags finds no violation (18 applicable rules passed per page, none incomplete); no horizontal scroll at 320 px, also with text at 200%; the first Tab reaches the skip link, Enter moves to `main`, and the next Tab reaches the button with a 2 px solid focus ring; every request goes to the page's own origin with no CSP violation; the logo loads at 720 px natural width, shows at 240 px (200 px at 320 px wide) with `screen` blend; the language switch works with JavaScript off; and when the logo is blocked, the image's accessible name is still "رعد RAAD". |

Total: 91 tests, all passing.

## Tests and Checks Written but Not Executed Here

- **`deploy-dev.yml`** was not run. It needs `AWS_ROLE_ARN_DEV` and the `dev` deploy inputs in GitHub, and this stage deploys nothing.
- **`ci.yml` on GitHub** has not run, because nothing is pushed. Each of its commands was run locally with the results above, and gitleaks ran through Docker on the working-tree files rather than through `gitleaks-action` on git history.
- **`scripts/smoke_site.py` against a real host** has not run, because nothing is deployed. It was exercised only against a local server and stubbed HTTPS responses.
- **The CloudFront Function** was executed only in Node.js locally, not in the CloudFront JavaScript runtime.

## Deviations From the Plan

1. **Logo (plan decision 5).** The person clarified the logo during the build (message 3370b0e8). The sphere icon had been sent by mistake, and the horizontal lockup replaces it; no copy of the sphere image was ever made. Because the lockup carries the name itself, the header shows only the image, with `alt="رعد RAAD"` on both pages, instead of the planned empty `alt` beside visible "رعد RAAD" text. If the image fails, the alt text shows, and "RAAD" stays in the title and the footer. The image is 240 px wide on desktop and 200 px on phones (not the planned 120 px), and the web copy is 720 px wide (not 480 px), both as instructed. The page tests and the browser scan check the new alt text. One small note: the brief described the source as 923×2048, but the file on disk is 1290×2796; the trim instructions were applied to the actual file.
2. **`traceability.json`.** Step 12 of the plan lists it, but the conductor writes it, as the build brief asked. It maps all 20 assigned IDs: 19 `OK`, each with one `RaadWeb@checkout/...` file (the same labels as `source-manifest.json`), and `AC6.2.2` as `N/A` because U3 owns the per-environment mobile builds. Every `OK` target was checked to exist in `RaadWeb`. The advisory traceability check reports those 19 targets as missing because it resolves only paths inside the `Raad` project, not sibling-repo labels (the same limitation as U2). Rows that need a deployed site (`AC6.2.1`, `NFR2.10`, `NFR5.10`, `NFR7.10`, `BR5.5`) point to the code or script that implements them; their evidence is in Checks Still Open.
3. **Additions not named in the plan text:**
   - the CloudFront index-rewrite function, needed for `/en/` on an OAC origin;
   - `X-Frame-Options: DENY`;
   - the AAAA alias record;
   - hashing of the logo;
   - one upload per file type with explicit content types;
   - the `RAADWEB_REQUIRE_BROWSER` switch;
   - the `raadweb/content.py` and `raadweb/web_policy.py` modules.

   None of them changes a planned behaviour.
4. **cdk-nag 3.x.** The plan says cdk-nag without a version. The current major version (3.0.2) uses CDK's `Validations` acknowledgements rather than `NagSuppressions`, unlike the sibling repos' 2.x.

No threshold was lowered, and nothing was skipped to make a run pass.

## Checks Still Open (need a deployed site or a person)

- **Landing certificate and deploy.** Request the free ACM certificate in `us-east-1` for `raadwallet.com` and `*.raadwallet.com`. Set the `dev` environment's `RAADWEB_DOMAIN_NAME`, `RAADWEB_CERTIFICATE_ARN`, `RAAD_HOSTED_ZONE_ID` and `AWS_ROLE_ARN_DEV`, and create the OIDC role, scoped to this repo and environment. Then deploy. Hosting, request and CI costs apply, and the CloudFront Function adds a small per-request charge.
- **Both-language smoke on each environment.** Run `scripts/smoke_site.py` against `dev.raadwallet.com`, `stg.raadwallet.com` and `raadwallet.com` after each deploy. `stg` and `prd` promotion belongs to the Deployment Pipeline stage.
- **Keyboard and screen-reader pass.** A person needs to go through both pages in a real browser with VoiceOver or TalkBack, including the case with no mail handler. The automated scan above does not replace it.
- **Native Arabic review** of every Arabic string: title, description, notice, access text, button, fallback line, skip link, language-nav label and `mailto:` subject.
- **Customer approval of the copy** in both languages (assumption A9).

## Revision after review 1

The person approved "Fix it and continue" after the first architecture review (`reviews/review-01.md`, verdict READY with six minor findings). Plan steps 13 to 18 fix R-01, R-02, R-03 and R-05; R-04 and R-06 are carried forward. The work stays on branch `aidlc/u5-landing-page` in `RaadWeb`, still uncommitted, with nothing deployed and no AWS call made. Each layer was again built first and tested after.

### What Changed

**R-01 — Not-found page and favicon (Step 13).**

- **`site/404.html`.** A bilingual page with the same header as the others, Arabic first (`lang="ar" dir="rtl"`) and English after it in a `section lang="en" dir="ltr"`.
  - It has one `h1` ("الصفحة غير موجودة") and an English `h2` ("Page not found").
  - It has links back to `/` and `/en/`, a bilingual skip link, `<meta name="robots" content="noindex">` and no canonical link.
  - Like the other pages, it has no script and is served under the same CSP.
- **CloudFront error responses.** The distribution maps S3's 403 and 404 for a missing object to `/404.html` with a real 404 status and a 30-second error-cache time (`ERROR_CACHE_SECONDS`). The page is uploaded with the other pages and invalidated with them on every deploy (`/index.html`, `/en/index.html`, `/404.html`).
- **Edge function.** The function now redirects only real page folders, which are read from the build (today only `/en`). Any other path without a slash goes to S3 as it is, so `/foo` reaches the 404 page in one hop instead of bouncing through `/foo/`. The stack test runs the function code exactly as synthesized, including a new pass-through case.
- **Favicon.** Both icons are cut from the bolt in the same lockup source as the logo. The bolt was found as the first lit column run at brightness above 20, centred in a black square with 12% padding, with the wordmark blanked.
  - `site/favicon.ico` is 32×32 and 1,419 bytes.
  - `site/assets/icon-180.png` is 180×180 and 19,339 bytes; it is the Apple touch icon and gets a hashed name in the build.
  - Every page links both with `<link rel="icon" href="/favicon.ico" sizes="32x32">` and `<link rel="apple-touch-icon">`.
  - Only these two small files are committed.
- **Caching by name.** Files whose names don't change (`favicon.ico`, the font licence) are now cached for a day (`public, max-age=86400`) instead of a year. The build refuses any hashable file type (`.css`, `.woff2`, `.webp`, `.png`, `.svg`) outside `assets/`, so nothing with a fixed name is ever marked immutable. The build and the stack share that list (`HASHED_SUFFIXES` in `raadweb/web_policy.py`), and `.ico` has its explicit content type (`image/x-icon`).
- **Smoke script.** It now also checks that an unknown path (`/raadweb-smoke-no-such-page`) answers 404 with the not-found page, not the bucket's XML error, and that `/favicon.ico` loads. That makes 2 × 13 page checks plus these 2 site checks.
- **Test server.** The local server answers a miss with `404.html` and status 404, as the distribution does.

**R-02 — Pinned tools (Step 14).**

- **CDK CLI.** Both workflows install `aws-cdk@2.1148.1`, the newest 2.x CLI (released 11 Nov 2026). The locked `aws-cdk-lib` is 2.277.0, and that exact CLI synthesized all three environments locally (below).
- **Actions.** Every action is pinned to a full commit SHA, with its release in a comment. Each SHA was looked up with `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`. All five tags are lightweight, so the ref's object was already the commit and needed no dereferencing.

  | Action | Release | Commit |
  |---|---|---|
  | `actions/checkout` | v4.4.0 | `11d5960a326750d5838078e36cf38b85af677262` |
  | `astral-sh/setup-uv` | v5.4.2 | `d4b2f3b6ecc6e67c4457f6d3e41ec42d3d0fcb86` |
  | `actions/setup-node` | v4.4.0 | `49933ea5288caeca8642d1e84afbd3f7d6820020` |
  | `aws-actions/configure-aws-credentials` | v4.3.1 | `7474bc4690e29a8392af63c5b98e7449536d5c3a` |
  | `gitleaks/gitleaks-action` | v2.3.9 | `ff98106e4c7b2bc287b24eaf42907196329070c7` |

  Each is the newest release within the major version the reviewed workflows already used, and each major tag points at that same commit, so behaviour is unchanged.
- **New test.** `tests/test_workflows.py` (16 tests) fails on any action used by tag, branch or short SHA, or without a release comment. It also fails on an unpinned or wrong-major `aws-cdk` install, checked against `aws-cdk-lib` in `uv.lock`, and on two workflows that disagree on the CLI version. The README setup line names the pinned CLI.

**R-03 — Bucket cleanup (Step 15).**

- **Lifecycle rule `ExpireOldVersions`.** It applies in every environment. A replaced (noncurrent) object version expires after 30 days, the 3 most recent replaced versions are always kept, and an incomplete multipart upload is aborted after 7 days. Current objects never expire. That includes older hashed assets that a cached page may still name, because `prune` stays off.
- **`dev`.** The bucket is now `DESTROY` with `autoDeleteObjects`, so deleting the stack empties and removes it.
- **`stg` and `prd`.** These stay `RETAIN`, with termination protection and no auto-delete resource.
- **cdk-nag.** It raised no new finding. CDK's auto-delete provider is built from raw `CfnResource` objects, which the AwsSolutions rules do not inspect, so nothing new needed acknowledging and the 14 existing acknowledgements are unchanged. For the record:
  - the provider's role uses the AWS managed basic execution role;
  - its delete, list and get-bucket rights, plus `PutBucketPolicy`, come only from a statement in the `dev` bucket policy, which a stack test checks.

**R-05 — Language alternates (Step 16).**

- **Links.** Both pages declare a `<link rel="canonical">` to themselves and `<link rel="alternate">` for `hreflang` `ar` (`/`), `en` (`/en/`) and `x-default` (`/`).
- **Known limitation.** These addresses are root-relative on purpose, because one build is promoted from `dev` to `stg` to `prd` and no hostname can be written into it. Search engines expect absolute URLs in these hints, so a crawler may ignore them until a later change writes the `prd` hostname into them at build or deploy time. An HTML comment beside the links records the reason.

### Files Changed in This Revision (RaadWeb)

- **New:**
  - `site/404.html`
  - `site/favicon.ico`
  - `site/assets/icon-180.png`
  - `tests/test_workflows.py`
- **Modified:**
  - pages, stylesheet, README and workflows: `site/index.html`, `site/en/index.html`, `site/assets/styles.css`, `README.md`, `.github/workflows/ci.yml`, `.github/workflows/deploy-dev.yml`
  - stack and scripts: `raadweb/stack.py`, `raadweb/web_policy.py`, `scripts/build_site.py`, `scripts/smoke_site.py`
  - tests: `tests/site_server.py`, `tests/test_pages.py`, `tests/test_build_site.py`, `tests/test_smoke_site.py`, `tests/test_stack.py`, `tests/browser/test_axe.py`

`source-manifest.json` now lists 41 paths, the earlier 37 plus the 4 new ones. In `unit-test-instructions.md`, only the CDK CLI install line changed, to the pinned version.

### Commands Run and Results (Step 17)

All runs used the same toolchain as before. The test runs set `RAADWEB_REQUIRE_BROWSER=1`, so a missing browser would have failed, not skipped.

| Command | Result |
|---|---|
| `uv sync --locked --all-groups` | 58 packages; lock unchanged, exit 0. |
| `uv run ruff format --check .` | 22 files already formatted, exit 0. |
| `uv run ruff check .` | All checks passed, exit 0. |
| `uv run mypy raadweb scripts app.py` | No issues in 10 source files, exit 0. `uv run mypy tests` also reports no issues in 11 files. |
| `uv run pytest tests/test_pages.py tests/test_build_site.py tests/test_smoke_site.py tests/test_stack.py tests/test_workflows.py --no-cov -q` | 117 passed, exit 0. |
| `uv run pytest tests/browser/test_axe.py -m browser --no-cov -q` | 16 passed, exit 0. For both language pages and the not-found page (served for an unknown path with status 404), axe-core 4.12.1 found 0 WCAG 2.0/2.1 A and AA violations. The scan also checked reflow at 320 px and with text at 200%, the skip link, the focus ring, own-origin requests with no CSP violation, and `/favicon.ico` loading as `image/x-icon`. |
| `uv run pytest tests --cov=raadweb --cov=scripts --cov-report=term-missing --cov-fail-under=80 -q` | 133 passed. Coverage 95.74% against the 80% floor; line coverage alone is 516 of 529 statements, 97.5%. Exit 0. |
| `uv run python scripts/build_site.py --out dist` | Built 12 files, with 7 assets renamed (now including `icon-180.f6d4ceb2.png`); the stylesheet is now `styles.9ebf3933.css`. Exit 0. |
| `uv run pip-audit` | No known vulnerabilities found, exit 0. |
| `RAAD_ENVIRONMENT=<env> RAADWEB_DOMAIN_NAME=<fixture host> uv run cdk synth -q` for `dev`, `stg` and `prd` | Exit 0 each, with 0 cdk-nag errors and 14 distinct acknowledgements. `dev` has 29 resources: a `Delete` bucket, auto-delete, and no termination protection. `stg` and `prd` have 26 resources each: a `Retain` bucket, no auto-delete, and termination protection. |
| The same three synths with `npx --yes aws-cdk@2.1148.1 synth -q` | Exit 0 each, with 0 cdk-nag errors. This is the CLI CI now installs. |
| gitleaks v8.30.1 (Docker) `dir` scan over a copy of the 41 files to be committed | No leaks found, exit 0. |
| Content check of the 34 text files to be committed | No alert address. No 12-digit number other than the fixtures. The only email addresses are the two approved public contacts and one `example.com` address in a wrong-contact test. No JPEG in the repo. |
| Workflow YAML parse (PyYAML 6.0.3) | `ci.yml` has 14 steps and `deploy-dev.yml` has 15. Every `uses:` is SHA-pinned. |

All synths ran with the credential chain blanked and the same fixture inputs as before.

Test counts by file:

| File | Tests |
|---|---|
| `tests/test_pages.py` | 40 |
| `tests/test_build_site.py` | 14 |
| `tests/test_smoke_site.py` | 14 |
| `tests/test_stack.py` | 33 |
| `tests/test_workflows.py` | 16 |
| `tests/browser/test_axe.py` | 16 |

### Carried Forward, Not Built

- **R-04 — the edge function has not run in CloudFront.** The function is now generated from the build's page folders and tested in Node.js on the exact synthesized code, but proving it in the CloudFront JS 2.0 runtime needs a deployed distribution. The first `dev` smoke test of `/en/` and of the unknown path is its acceptance evidence. An optional CloudFront `test-function` call before the smoke test in the deploy workflow was not added, because it would call AWS and needs the dev role.
- **R-06 — deployed and human checks.** These need a deployed site or a person and remain gating items for the deployment and release stages:
  - the landing certificate and the first deploy;
  - the both-language smoke test (now including the not-found page and favicon) on `dev`, `stg` and `prd`;
  - a keyboard and screen-reader pass, now also of the not-found page;
  - the native Arabic review, which now includes the not-found page's Arabic text and the bilingual skip-link label;
  - the customer's approval of the copy.

### Notes for the Next Stages

- **Newer action majors.** All five pinned actions declare the `node20` runtime, and newer majors exist: `actions/checkout` v7.0.1, `astral-sh/setup-uv` v10.3.3, `actions/setup-node` v7.1.0, `aws-actions/configure-aws-credentials` v6.3.0 and `gitleaks/gitleaks-action` v3.0.0. Moving to them changes behaviour that cannot be run here, so it is left for a separate change, ideally made across all RAAD repos together.
- **Plan checkboxes.** When this revision was added, the plan's Steps 1 to 12 were reset to unticked. Only Steps 13 to 18 were ticked in this revision, as instructed. Steps 1 to 12 were completed in the first build, as recorded above.
- **`traceability.json`** is left to the conductor.
