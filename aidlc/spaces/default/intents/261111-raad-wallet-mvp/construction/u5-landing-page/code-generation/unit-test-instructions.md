# Unit Test Instructions — U5 Landing Page

Conversation language: English.

## Framework and Configuration

- Repository: `RaadWeb` (`00az/RaadWeb`), branch `aidlc/u5-landing-page`. Python 3.12 pinned, `uv` with a committed `uv.lock`, pytest with pytest-cov, Ruff, strict mypy, `pip-audit`, AWS CDK v2 and cdk-nag. Step 1 creates the runner and confirms it runs before the first test.
- Setup: `uv sync --locked --all-groups` from the `RaadWeb` root. The CDK CLI comes from Node.js at the exact version CI uses (`npm install --global aws-cdk@2.1148.1`).
- The browser scan needs Playwright's Chromium: `uv run playwright install chromium`.

## How to Run This Unit's Tests

Run from the `RaadWeb` root. Each command names U5's test files.

| Purpose | Command |
|---|---|
| Pages, build, smoke and stack tests | `uv run pytest tests/test_pages.py tests/test_build_site.py tests/test_smoke_site.py tests/test_stack.py --no-cov -q` |
| Accessibility scan (headless Chromium) | `uv run pytest tests/browser/test_axe.py -m browser --no-cov -q` |
| Repository floor (own command) | `uv run pytest tests --cov=raadweb --cov=scripts --cov-fail-under=80 -q` |
| Format, lint, types | `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy raadweb scripts app.py` |
| Build | `uv run python scripts/build_site.py --out dist` |
| Synth with bundling and cdk-nag | `RAAD_ENVIRONMENT=<dev\|stg\|prd> uv run cdk synth -q` with the CI fixture inputs, no AWS credentials |

## Expected Coverage Targets

- Standard strategy: five to eight focused tests per component (each page, stylesheet rules, build step, smoke script, hosting stack), plus the browser scan of both pages.
- The team sets no coverage floor for `RaadWeb`'s static files. The repo's Python (`raadweb/` and `scripts/`) holds at least 80% line coverage, checked by its own command above. Build and Test runs it on the full suite.
- No coverage-ignore pragma is used.

## Mocking and Stubbing

- Pages: parsed with the standard-library HTML parser; no network.
- Smoke script: a local HTTP server on `127.0.0.1` serving `dist/` with configurable headers and failures, plus stubbed responses for the TLS checks. No real host is contacted.
- Stack: `aws_cdk.assertions.Template` on synthesized stacks; no AWS calls.
- Browser scan: Playwright against the local server only.

## Test Data

- The only email addresses in pages and tests are the two person-supplied public contacts, `abdulaziz.alrubai@outlook.com` and `zyad.alamri777@gmail.com`; test fixtures for wrong-contact cases use `example.com`.
- The logo source is the horizontal lockup the person clarified during the build; only the resized web copy and the bolt favicon derived from it are committed.
- Revision 1 adds tests to the existing files (`tests/test_pages.py` for the 404 page, favicon and language alternates; `tests/test_stack.py` for error responses, lifecycle and removal settings; `tests/test_smoke_site.py` for the unknown-path check) and a workflow pinning test, `tests/test_workflows.py`. Run it with the other unit tests: `uv run pytest tests/test_workflows.py --no-cov -q`.
- No account IDs, alert email, credentials or visitor data in any test, fixture or log.
