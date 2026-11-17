## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-17T02:26:28Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Minor | RaadWeb@checkout/raadweb/stack.py > `_distribution` (no custom error responses); RaadWeb@checkout/site/ (no favicon or robots file) | The origin is private behind origin access control, so any path that is not a file (an unknown URL, or `/favicon.ico`, which browsers request on every visit) returns S3's raw 403 AccessDenied XML. The edge function also redirects `/foo` to `/foo/` and then asks S3 for `/foo/index.html`, which fails the same way. A grep for `error_responses`, `favicon` and `robots` in `raadweb`, `site` and `tests` finds nothing, and the smoke test does not check an unknown path. Visitors who mistype the address see an XML error, not a page. | Add a CloudFront custom error response that maps 403 and 404 to a small branded 404 page (Arabic and English, no script). Add a favicon (the logo mark would do). Add one smoke check that an unknown path returns a 404 page and not S3 XML. This can follow the MVP demo. | Resolved (reviewer) |
| R-02 | Minor | RaadWeb@checkout/.github/workflows/deploy-dev.yml > the "Install" and credentials steps; ci.yml > `npm install --global aws-cdk` | The dev deploy job holds an OIDC role, yet it installs an unpinned CDK CLI (`npm install --global aws-cdk`) and uses third-party actions by moving tag (`aws-actions/configure-aws-credentials@v4`, `astral-sh/setup-uv@v5`, `gitleaks/gitleaks-action@v2`). The Python side is locked by `uv.lock`, so the CLI and the actions are the only unpinned inputs. An unpinned CLI can also drift from the pinned `aws-cdk-lib` 2.277.0 cloud-assembly schema. | Pin the CDK CLI to a version matching the lock (`aws-cdk@2.x.y`). Pin the credentials action and gitleaks to full commit SHAs, at least before the `stg` and `prd` promotion work copies this workflow. | Resolved (reviewer) |
| R-03 | Minor | RaadWeb@checkout/raadweb/stack.py > `_bucket`, `_publish` (`versioned=True`, `prune=False`, `RemovalPolicy.DESTROY` in `dev`) | Versioned objects are never pruned and the bucket has no lifecycle rule. Every deploy adds hashed assets and a new HTML version, so the bucket grows without bound. In `dev` the stack will fail to delete until the bucket and all its object versions are emptied by hand. Both are small for a page of about 160 KB, and the README documents the dev emptying, but nothing enforces an upper bound. | Add a lifecycle rule that expires noncurrent versions after a set number of days (for example 90). Alternatively, record in the README that this is accepted for the MVP. | Resolved (reviewer) |
| R-04 | Minor | RaadWeb@checkout/raadweb/stack.py > `INDEX_REWRITE_CODE`; tests/test_stack.py (index rewrite cases) | The CloudFront Function that makes `/` and `/en/` work on an OAC origin was executed only in local Node.js (4 cases), not in the CloudFront JS 2.0 runtime, as code-summary.md states. The pages depend on it, so a runtime difference would break `/en/` on first deploy. The smoke test against `dev` would catch it, which makes this a deploy-time check and not a design flaw. | Treat the first `dev` smoke test of `/en/` as the acceptance evidence for this function. Optionally add a CloudFront `test-function` call to the deploy workflow before the smoke test. | Unresolved |
| R-05 | Minor | RaadWeb@checkout/site/index.html and site/en/index.html > `<head>` | The two pages link to each other only through anchors in the body. There is no `<link rel="alternate" hreflang>` pair or canonical link in the head, and no social preview metadata. This is a discoverability gap, not a defect. Search engines are the main readers of these hints, and the page is a private demo. | Optional: add `rel="alternate" hreflang` and `rel="canonical"` links to both heads when the page becomes public beyond the test group. | Resolved (reviewer) |
| R-06 | Minor | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u5-landing-page/code-generation/code-summary.md > Checks Still Open and Deviations | Several product claims have no executed evidence yet, and the summary lists them honestly: the smoke test against a real host, a keyboard and screen-reader pass, a native Arabic wording review, the customer's copy approval (A9), and the ACM certificate request. The logo changed from the planned sphere icon to the horizontal lockup, with `alt="رعد RAAD"` and no visible text name. The deviation is recorded and tested. Approving this stage does not clear any of these. | Keep them as gating items for the deployment and release stages. The first `dev` deploy must pass the smoke test for both languages, and the native Arabic review and the copy approval must be recorded before `prd`. | Unresolved |
| R-07 | Minor | RaadWeb@checkout/site/index.html and site/en/index.html > `<head>` `canonical` and `alternate` links | The `canonical` and `alternate` links use root-relative addresses (`/`, `/en/`). Search engines expect absolute URLs for these hints and may ignore them, so the language pairing does nothing for discovery until the production hostname is written in. The summary records this, and the page is a private demo, so nothing breaks now. | Before the page is public beyond the test group, write the `prd` hostname into these links at deploy time, or drop them until then. | New |

> R-01 Reviewer note: `stack.py` `_distribution` now maps S3 403 and 404 to `/404.html` with a real 404 status and a short error cache time. `site/404.html` is bilingual, has no script, carries `noindex`, and uses root-absolute asset and link paths, so it renders correctly at any depth. `site/favicon.ico` and `assets/icon-180.png` exist and both pages and the 404 page link them. The edge function redirects only folders found in the build (`/en`); any other path goes to S3 and comes back as the not-found page. `smoke_site.py` has an unknown-path check that requires status 404 and the not-found page.

> R-02 Reviewer note: Both workflows install `aws-cdk@2.1148.1`, and every `uses:` line in `deploy-dev.yml` and `ci.yml` is a 40-character commit SHA with a release comment. `tests/test_workflows.py` enforces both rules and passes.

> R-03 Reviewer note: The bucket has an `ExpireOldVersions` lifecycle rule: noncurrent versions expire after 30 days (3 kept) and incomplete uploads abort after 7 days. `dev` sets `auto_delete_objects`. `stg` and `prd` are retained and the stack is termination-protected. Current objects are never expired, which matches the `prune=False` design.

> R-04 Reviewer note: The edge function still has no run in the CloudFront JS 2.0 runtime. It is now generated from the build's page folders and Node-tested on the synthesized code. The first `dev` smoke test of `/en/` and of the unknown path is its acceptance evidence.

> R-05 Reviewer note: Both pages now have `canonical`, `alternate hreflang` (ar, en, x-default) and icon links in the head. The addresses are root-relative, which the summary records as a limitation. See the new finding below.

> R-06 Reviewer note: Unchanged and honestly listed: smoke test on a real host, keyboard and screen-reader pass, native Arabic review, copy approval (A9) and the ACM certificate request. Approving this stage does not clear them. They stay gating items for deployment and release.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `uv run ruff check .` | PASS (All checks passed) | No lint errors. |
| `uv run mypy raadweb scripts app.py` | PASS (no issues in 10 source files) | Types are clean. |
| `RAADWEB_REQUIRE_BROWSER=1 uv run pytest tests -p no:cacheprovider --cov=raadweb --cov=scripts --cov-fail-under=80` | PASS: 133 passed, coverage 95.74% (floor 80%) | The browser tests ran, and the stack, workflow pinning and smoke tests are included. |

### Summary

The revision fixes R-01, R-02, R-03 and R-05 with evidence in the code and in passing tests. Only deploy-time and human checks remain (R-04, R-06), plus a minor note that the root-relative canonical links are ineffective for search engines until the hostname is written in. A developer could take this to the first `dev` deploy as it stands.
