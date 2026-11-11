# Evidence: Practices Discovery

**Stage:** practices-discovery (greenfield)
**Lead:** aidlc-pipeline-deploy-agent, working alone. Collaborators are off for the classic scope, so there were no support reviews and no contribution files.
**Drafted:** 2026-11-11T15:31:44Z at commit `81b2522`
**Interview:** 12 questions, answered in chat; answers recorded 2026-11-11T16:22:53Z in `practices-discovery-questions.md`
**Integrated:** 2026-11-11T16:28:04Z at commit `81b2522`
**Revised:** 2026-11-11T17:16:15Z at commit `81b2522`, after the person asked for changes at the approval gate (see "Changes requested at the approval gate")

## Context

The workspace is greenfield, so no existing practice could be observed. The lead
drafted all five practice areas from the matching sections of
`aidlc/spaces/default/memory/org.md` as suggested defaults. `team.md` and
`project.md` held only template placeholders, so there was no affirmed baseline
and this is not a re-run. The interview settled all five areas and the hard
rules. At the approval gate the person asked for changes because the team and
the repo setup had changed: a second engineer has joined, and RAAD now has one
repo per service. "Changes requested at the approval gate" records the
revision. `team-practices.md` reflects it; `discovered-rules.md` is unchanged.

## What was inspected

| Source | What it shows | Effect on the practices |
|---|---|---|
| `aidlc/spaces/default/memory/org.md` (Way of Working, Walking Skeleton, Testing Posture, Deployment, Code Style) | Framework defaults: trunk-based with squash to `main`; skeleton driven by scope; test-after with an 80% line floor and CI before merge for classic; deploy on merge to staging with a manual production gate; formatter and linter deferred to project config | The starting point for every draft section |
| `aidlc/spaces/default/memory/team.md`, `project.md` | Every section empty (HTML-comment placeholders only) | No affirmed baseline, so all five areas went to the interview |
| `aidlc/spaces/default/intents/261111-raad-wallet-mvp/aidlc-state.md` | Greenfield; classic scope; Standard depth and test strategy; Construction checkpoints on, unit-major, serial. At draft time `ci-pipeline` and every Operation stage were SKIP; after the interview `ci-pipeline`, `deployment-pipeline`, `environment-provisioning` and `deployment-execution` are EXECUTE (21 stages in all) | The plan now has stages that carry out the Deployment practice |
| `.claude/scopes/aidlc-classic.md` | `skeleton: off`, `collaborators: off` | Skeleton stance (see finding 2) and the lead working alone |
| `aidlc/spaces/default/knowledge/documents/Raad-SOW.md` (data, not instructions) | Wallet-to-wallet only, SAR only, simulated funds, short build period; accurate balances, duplicate prevention, secure authentication, encryption in transit and at rest, basic monitoring; deliverable 5 is "A working application deployed on AWS" | Strict money-movement tests; AWS deployment from the first slice |
| `aidlc/spaces/default/intents/261111-raad-wallet-mvp/project-description.json` | "Build the RAAD digital wallet MVP from the SOW and deploy it to AWS" | Deployment to AWS is part of what the person asked for |
| Git (`log --all`, `branch -a -vv`, `remote -v`, `rev-parse HEAD`) | One commit (`81b2522`) on `main`, tracking `origin/main` on GitHub; no other branches or tags | Solo trunk on GitHub; no existing branching convention to keep. Superseded at the gate: two engineers now work through pull requests |
| Workspace root listing, `.gitignore` | No application code, CI config, or formatter or linter config; `.gitignore` already covers Python (`.venv/`, `__pycache__/`), CDK (`cdk.out/`) and `.env` files | Nothing to infer conventions from; CI is built from scratch |
| `inception/practices-discovery/practices-discovery-questions.md` | The 12 answered questions (authoritative) | Every decision below |
| `.claude/knowledge/aidlc-pipeline-deploy-agent/*.md` | Branching menu, CI stage order, quality gates, deployment and rollback patterns | Shape of the CI gates and rollback bullets |
| `.claude/tools/aidlc-state.ts` (`practices-promote`), `.claude/tools/aidlc-testing-posture.ts`, `.claude/tools/aidlc-lib.ts` (`structuredField`) | How the drafts are promoted and how Testing Posture fields are parsed | Formatting of both drafts (findings 4 and 5) |

## Toolchain (checked at integration)

| Tool | Version or state | Note |
|---|---|---|
| Python | 3.14.9 | The pinned version follows the newest Lambda runtime instead; `uv` installs it if it differs |
| uv | 0.13.5 | |
| Docker | 29.1.3 | Needed for the integration and concurrency tests against local containers |
| AWS CDK CLI | 2.1146.1 | The CDK CLI runs on Node.js even though the CDK code is Python |
| Node.js / npm | v26.12.1 / 11.20.0 | Not an application language; still needed for the CDK CLI |
| AWS CLI | 2.38.5 | SSO profile in `us-east-1` |
| GitHub CLI | 2.103.2 | |
| AWS SAM CLI | 1.170.0 | Installed but not chosen |
| Flutter SDK / Dart | not installed | `command -v flutter dart` finds nothing |
| Xcode | Command Line Tools only | `xcode-select -p` points at `/Library/Developer/CommandLineTools`; full Xcode is not installed |
| CocoaPods | not installed | `command -v pod` finds nothing |
| Android SDK | not installed | No `~/Library/Android` folder; `command -v adb` finds nothing |

## Interview decisions

| Q | Area | Decision | How it was decided |
|---|---|---|---|
| Q1 | Way of Working | A: each piece of work squashed into one commit on `main` locally, then pushed; no pull requests or branch protection while one developer works on it. Superseded at the gate: pull requests with the other engineer's approval and a protected `main` | Left to the conductor's recommendation ("your recommendionts") |
| Q2 | Deployment | X: three environments, `dev`, `stg` and `prd` | The person answered directly ("for the envs we want 3: prd, stg and dev") |
| Q3 | Deployment | A: add the CI pipeline, deployment pipeline, environment provisioning and deployment execution stages | Left to the conductor's recommendation |
| Q4 | Walking Skeleton | A, adapted to the mobile app: sign in on the phone, see the SAR balance, send one transfer, see it in history, against `dev` on AWS | Left to the conductor's recommendation, adapted to the mobile app chosen at Q7 |
| Q5 | Testing Posture | A: tests first (TDD) for the money-movement core, tests after the code everywhere else | Left to the conductor's recommendation |
| Q6 | Testing Posture | A: 80% line coverage, 95% line and branch on the money-movement core, plus the conservation, replay, concurrency and rejection tests | Left to the conductor's recommendation |
| Q7 | Code Style | X: Flutter (Dart) mobile app on iOS and Android; Python backend; the web app is only a landing page | The person answered directly |
| Q8 | Deployment / Code Style | X: AWS CDK in Python with cdk-nag | Left to the conductor; resolved as Python instead of the drafted TypeScript because the backend is Python, which keeps the project to two languages (Dart and Python) |
| Q9 | Hard rules | A, B, C, D and E | The person answered directly ("with these rules") |
| Q10 | Deployment | A: `dev` on every push to `main`; `stg` automatically once `dev`'s smoke test passes; `prd` after the person approves a version that passed on `stg` | The person answered directly ("Q10 yes") |
| Q11 | Deployment | A: one AWS account, each environment its own set of stacks and data | The person answered directly ("one account") |
| Q12 | Deployment | A: iOS and Android through TestFlight and Google Play internal testing; no public store release | The person answered directly |

The drafted recommendations at Q7 (TypeScript everywhere) and Q8 (CDK in
TypeScript) were not taken. Every TypeScript, Node.js, Prettier, ESLint, Vitest
and npm practice in the draft has been replaced with the Dart and Python
tooling.

## How the answers changed the draft

- **Way of Working:** unchanged in substance. Added that there are no
  per-environment branches, because the pipeline promotes one commit through
  `dev`, `stg` and `prd`.
- **Walking Skeleton:** the first slice moved into the Flutter app against the
  `dev` backend. The proposed verification adds a Flutter integration test on a
  simulator to the API smoke script. Both remain proposals until the person
  authorises the Construction Verification Command.
- **Testing Posture:** coverage floors now apply separately to the backend and
  the Flutter app; Hypothesis is named for the property-based tests; test types
  cover the Flutter app. The lead filled two gaps that the answers left open:
  the infrastructure layer, which the Ordering names as test-after, gets pytest
  tests of the CDK stacks; and the post-deploy smoke test also fetches the
  landing page, because the landing page is deployed per environment and every
  deploy needs a smoke test to count as done.
- **Deployment:** `dev` and `prod` became `dev`, `stg` and `prd`; CDK moved to
  Python; hosting for the landing page and build and distribution for the
  mobile app were added. The lead added two details: rolling back the mobile app
  means rebuilding the last known-good commit with a new build number, because
  TestFlight and Google Play accept only increasing build numbers; and a cdk-nag
  suppression carries its reason in the code, which cdk-nag itself requires.
- **Code Style:** the TypeScript toolchain was replaced with the Python and
  Dart toolchains. The lead added a committed `pubspec.lock`, which Dart
  recommends for applications and which mirrors the committed `uv.lock`. The
  OpenAPI contract as the single source of truth comes from the conductor's
  integration brief for Code Style, and the spec itself is produced by the
  contract design stage already in the plan. The lead also listed Node.js among
  the setup prerequisites, because the CDK CLI runs on it.

## Plan change

At Q3 the person left the choice to the conductor, who took the recommended
option and added four stages: `ci-pipeline` (3.7), `deployment-pipeline` (4.1),
`environment-provisioning` (4.2) and `deployment-execution` (4.3). The Deployment
practice now has stages that carry it out, and the draft's first framework
finding is resolved. `observability-setup` (4.4) and the remaining Operation
stages stay SKIP.

## Changes requested at the approval gate

### What the person changed

These are the person's changes at the gate, as the conductor relayed them in
the revision brief.

1. **A second engineer.** The person works with another engineer, and both use
   AI-DLC on the same GitHub account. Who owns which repo is not decided yet;
   it is settled in delivery planning.
2. **Pull requests in every repo.** The Q1 practice (no pull requests while one
   developer works on the project) no longer holds. Every change goes through a
   pull request into `main`. A pull request needs the CI checks to pass and an
   approval from the other engineer. `main` is protected (no direct pushes, no
   force-pushes), pull requests are squash-merged, and branches are
   short-lived. The work stays trunk-based, with no `develop`, release or
   per-environment branches. The rule to fix or revert a red `main` before
   anything else lands stays.
3. **A repo per service.** The person decided on these repos. All are private,
   under `00az`, with default branch `main` (the person chose `main` everywhere).

   | Repo | Role | When |
   |---|---|---|
   | `Raad` (this repo) | Platform: the public API domain and certificate, with API mappings that send each path prefix to the service that owns it (`/money` to the money service; later `/ai` and `/qattah`); one shared user pool for sign-in; the shared event bus; the API firewall and rate limits. Also the planning and design record (`aidlc/`). The platform is a proposed design for domain design to confirm | MVP |
   | `RaadMoneyService` | The money core: accounts, wallets, wallet-to-wallet transfers and transfer history, in Python on AWS. The only service that changes wallet balances; other services ask it to move money | MVP |
   | `RaadMobile` | The Flutter app for iOS and Android | MVP |
   | `RaadWeb` | The landing page, a static site on S3 and CloudFront | MVP |
   | `RaadAiService` | The AI assistant that summarises transaction history and gives recommendations | After the MVP |
   | Qattah (not created yet) | Group money pooling, modelled on how the Barq app does it, in its own service repo created the same way. It moves money only by asking `RaadMoneyService` | After the MVP |

   Putting the AI assistant and Qattah after the MVP fits the SOW constraint
   that the MVP focuses only on wallet-to-wallet transfers.
4. **Deployment per repo.** Each deployable repo has its own pipeline with the
   same promotion flow as before (`dev` on every merge to `main`, `stg`
   automatically once `dev`'s smoke test passes, `prd` only after a person
   approves a version that passed on `stg`), all in the one AWS account.
   `Raad`'s platform deploys first in each environment because the services
   depend on its sign-in, API domain and event bus. Everything else in the
   Deployment practice stays.
5. **Tooling per repo.** The Python tooling applies to `Raad`, `RaadMoneyService`
   and later `RaadAiService`; the Dart and Flutter tooling to `RaadMobile`;
   `RaadWeb` is plain HTML and CSS. Each service's OpenAPI spec lives in that
   service's repo and is the source of truth for its API, and `RaadMobile`
   generates its Dart client from it. Each repo has its own README with one
   documented setup and test command.
6. **A walking skeleton across repos.** The first slice uses `Raad` (sign-in and
   the API domain), `RaadMoneyService` (the balance and one transfer) and
   `RaadMobile` (the screens), against `dev`. The "every greenfield project"
   wording and the verification proposal stay.

The person added no hard rules.

### What the lead checked for the revision

| Check | Result | Effect |
|---|---|---|
| `gh repo list 00az` | `Raad`, `RaadMoneyService`, `RaadMobile`, `RaadWeb` and `RaadAiService` are all private, with default branch `main`. The four new repos were created on 2026-11-11 between 16:42 and 16:47 UTC; `Raad` at 14:33 UTC | Confirms the repo list and `main` everywhere |
| `gh api repos/00az/<repo>/readme` for the four new repos | Each has a `README.md` | Confirms the setup done this session |
| `gh api repos/00az/<repo>/branches/main` for all five repos | `main` exists, and `protected` is `false` in every repo | Branch protection is not configured yet |
| `gh api users/00az` | `"type": "User"`: `00az` is a personal GitHub account, not an organisation | Finding 9; the practices say "the `00az` account" |
| `gh api user` | The GitHub CLI on this Mac is signed in to a different account, so `00az`'s plan could not be read | The plan question stays open (finding 9) |
| Folder listings of this folder and its parent folder | The four new repos are cloned beside this folder, in the same parent folder, not inside it. This folder (`raad` on disk, `00az/Raad` on GitHub) has no `repos.json` | Finding 8 |
| `.claude/tools/aidlc-workspace-manifest.ts` (`workspaceRepoPath`), `.claude/knowledge/aidlc-shared/adding-a-repo.md` | The engine accepts an extra repo only as an immediate child folder of the workspace root, which is this folder; `aidlc engine intent add-repo <name>` clones a missing repo there | Finding 8 |
| `.claude/tools/aidlc-worktree.ts`, `.claude/knowledge/aidlc-pipeline-deploy-agent/branching-strategies.md` | No pull-request path: a Bolt lands as a squash merge into `main` in the local checkout | Finding 7 |
| `.claude/tools/aidlc-markdown.ts` (`extractMarkdownSection`), `.claude/tools/aidlc-testing-posture.ts`, `.claude/tools/aidlc-lib.ts` (`structuredField`) | Promotion copies each section body up to the next H2 heading; the Ordering value is read as plain text | The repo table under Way of Working promotes as written; the backticked repo names in Ordering leave the detected cadences (test-driven and test-after) unchanged |
| GitHub Docs: "GitHub's plans", "About protected branches", "Managing environments for deployment", "Deployments and environments", "Permission levels for a personal account repository" | Protected branches and required pull-request reviews on private repos need GitHub Pro (personal account) or GitHub Team (organisation). By default, people with admin rights bypass branch protection unless "Do not allow bypassing the above settings" is on. On GitHub Free, Pro and Team plans, required reviewers on an environment are available only for public repositories. In a repo owned by a personal account, only the owner can invite collaborators | Findings 9 and 10 |
| `Raad-SOW.md` (data, not instructions) | "The MVP will focus only on wallet-to-wallet transfers" | The AI assistant and Qattah after the MVP fit the SOW |

### How the revision changed the practices

- **Way of Working:** rewritten for two engineers and pull requests. Every
  change reaches `main` through a pull request that needs green CI and the
  other engineer's approval; `main` is protected; pull requests are
  squash-merged; branches are short-lived; the work stays trunk-based. Added the
  repo table and the platform description. The fix-or-revert rule stays, now
  per repo. Removed the local squash-and-push flow and "no pull requests or
  branch protection while one developer works on the project".
- **Walking Skeleton:** the slice names the repo each part comes from. The
  wording "on every greenfield project" is kept, so the stance still classifies
  as `on`. The verification proposal is unchanged and still waits for the
  person's authorisation at Construction.
- **Testing Posture:** `Methodology` (`custom`), its evidence and the
  one-sentence Ordering are unchanged in substance; repo names replace "the
  backend", and the Ordering now covers every layer in every repo. Coverage
  floors apply per repo. CI runs on every pull request and again on every push
  to `main`. Each deployable repo has its own smoke test, and setup is
  documented per repo README.
- **Deployment:** one pipeline per deployable repo, each with the same
  promotion flow; `Raad` deploys first in each environment; each repo keeps the
  infrastructure it deploys. Kept: CDK in Python with cdk-nag, OIDC from GitHub
  Actions, no stored AWS keys, the smoke test defines "done", rollback by
  redeploying the last good commit, `prd` data retained with point-in-time
  recovery, additive schema changes, and mobile builds per environment through
  TestFlight and Google Play internal testing.
- **Code Style:** the tooling is grouped by repo; the OpenAPI source of truth is
  now one spec per service in its own repo; agents read the configuration of
  the repo they work in.

### What the lead added beyond the person's words

The person can strike any of these at the gate.

1. **The `prd` approval mechanism.** The earlier version said the approval runs
   through a GitHub Environment named `prd` with a required reviewer. On GitHub
   Free, Pro and Team plans, required reviewers are available only for public
   repositories, and every RAAD repo is private. The revised practice keeps the
   rule (a person approves a version that passed on `stg`, as a step in that
   repo's pipeline) and leaves the mechanism to the deployment pipeline stage
   (finding 10).
2. **Platform changes first, every time.** "`Raad`'s platform deploys first in
   each environment" also covers later changes: a platform piece a service
   needs reaches the environment through `Raad`'s pipeline before the service
   change that uses it. With separate pipelines, that is what "first" can mean
   after the first deploy.
3. **`Raad` counts as a backend repo** for the 80% line floor, because its
   platform code is Python and uses the same tooling.
4. **`RaadWeb` has no coverage floor.** It is static HTML and CSS with nothing
   to measure, and its smoke test checks it after every deploy.
5. **Per-repo smoke tests.** A service's smoke test calls its deployed API,
   `RaadWeb`'s fetches the landing page, and `Raad`'s checks the shared pieces
   it deployed; the API domain answering and a test user signing in are given
   as examples.
6. **Reverts go through a pull request,** like any other change, because `main`
   is protected.
7. **The landing page is not part of the walking skeleton.** The person named
   three repos for the first slice, and `RaadWeb` is not one of them.
8. **"The `00az` account" instead of "organisation",** because GitHub reports
   `00az` as a personal account (finding 9).
9. **One Python version across the Python repos,** carried over from "we pin one
   Python version".

### Setup status

- **Done this session:** the four new repos (`RaadMoneyService`, `RaadMobile`,
  `RaadWeb`, `RaadAiService`) were created on GitHub and set up with `main` and
  a README. The checks above confirm both.
- **Not done yet:** branch protection on `main` and the second engineer's
  access, in every repo. `main` reports `protected: false` in all five repos.
- **Open before Construction:** how this piece of work tracks the other repos.
  The AI-DLC record for it currently treats only this `Raad` folder as its code
  repo (finding 8).

## Framework findings

1. **Deployment had no stages.** Resolved by the plan change above.
2. **Walking skeleton stance and scope.** `aidlc-classic.md` declares
   `skeleton: off`. At Construction entry the conductor classifies team.md's
   `## Walking Skeleton`. The integrated wording ("We build a walking skeleton
   first on every greenfield project") says the team always builds one, so it
   classifies as `on`, which matches the person's Q4 answer. The revision keeps
   that wording.
3. **The classic 80% floor is stated in org.md but not built into the engine.**
   The engine's `combineTestObligations` applies the 80% floor only to `mvp`,
   `enterprise`, `feature` and `infra`. team.md's Testing Posture states the
   floors explicitly, so they bind through the team layer whatever the engine's
   scope table says.
4. **How promotion reads the drafts.** `practices-promote` copies each of the
   five section bodies into team.md and takes every non-blank, non-comment line
   under `## Mandated` and `## Forbidden` as a rule. The draft banner and every
   per-section `DRAFT` comment have been removed, and the rules are written one
   per line without list bullets.
5. **The Testing Posture parse.** `Methodology` is the bare value `custom`, with
   the reasons in a separate `Methodology evidence` line. The single-sentence
   `Ordering` names "test-driven (TDD)" and "test-after", so the engine detects
   both component cadences.
6. **AWS credentials.** The draft's note that no AWS credentials were available
   is out of date: AWS SSO credentials are now active for this project. In the
   integration session, and again in the revision session, the `aws-mcp` server
   failed to connect at start-up for lack of credentials, probably because it
   started without the SSO profile selected. Check this before a stage relies on
   live AWS lookups.
7. **Bolt landings and a protected `main`.** AI-DLC's Construction worktrees
   land each Bolt as a squash merge into `main` in the local checkout;
   `aidlc-worktree.ts` has no pull-request path. Once `main` is protected, that
   local commit cannot be pushed. Before Construction, the conductor and the
   person settle how a Bolt reaches `main` through a pull request (for example:
   push the Bolt branch, open a pull request, let GitHub squash-merge it after
   CI passes and the other engineer approves, then bring the local `main` up to
   date). The same rule applies to the AI-DLC record: `aidlc/` lives in `Raad`,
   so committing stage artifacts, state and audit shards to `main` also needs a
   pull request and the other engineer's approval.
8. **Repos outside the workspace.** The engine accepts an extra repo only as an
   immediate child folder of the workspace root (`workspaceRepoPath` in
   `aidlc-workspace-manifest.ts`). `aidlc engine intent add-repo <name>` clones
   a missing repo there, writes its `repos.json` entry and refreshes a managed
   `.gitignore` block. The workspace root is this folder, while the four new
   repos are cloned one level up, beside it, and there is no `repos.json`. So
   the record treats only `Raad` as its code repo. How it tracks the others
   must be settled before Construction: for example, adding each repo to the
   work, which clones a second copy inside this folder, or changing the folder
   layout.
9. **`00az` is a personal account.** The person described `00az` as a GitHub
   organisation; GitHub reports it as a personal account. That changes three
   things:
   - The second engineer joins each repo as a collaborator, and only the owner
     can invite one.
   - Protecting `main` and requiring an approving review on a private repo
     needs GitHub Pro on `00az`, or the repos moved into an organisation on
     GitHub Team. `00az`'s plan could not be read here. Until protection is
     on, the pull-request rule holds by agreement only.
   - By default, people with admin rights, which on a personal account means
     the owner, bypass branch protection. The approval rule binds both
     engineers only with "Do not allow bypassing the above settings" turned on.
10. **`prd` approval on private repos.** A GitHub Environment with required
    reviewers is not available for private repositories on GitHub Free, Pro or
    Team plans, so the earlier mechanism cannot be used as the repos stand. The
    deployment pipeline stage chooses the approval step. Options include a
    `prd` deploy that a person starts by hand and that accepts only a version
    that passed on `stg`, or an approval step outside GitHub, such as a manual
    approval in AWS CodePipeline.

## Hard rules (Q9)

The person picked all five offered rules, and they are written in
`discovered-rules.md` as one `ALWAYS` line and four `NEVER` lines. Three
wordings differ slightly from the option text, as the conductor's brief set
them:

- Rule E names `prd` and `dev`, following the three-environment decision (the
  option said `prod`).
- Rule D says "personal details" where the option said "full personal details",
  which is the stricter reading.
- Rule A's note on SSO and short-lived credentials is carried by the Deployment
  practice instead of the rule itself.

Two draft candidates were not offered as rules: moving money atomically and
requiring a request identifier on every transfer. They are design decisions as
much as practices, so they are settled in requirements analysis and domain
design, and the money-movement tests already check their effects.

The revision leaves `discovered-rules.md` unchanged: the person added no rules,
and the five rules read the same with one repo per service.

## Remaining uncertainty

- **Mobile toolchain.** The Flutter SDK, full Xcode, CocoaPods and the Android
  SDK are not installed on the developer's Mac (checked at integration; see the
  toolchain table). They are needed before Construction, because the walking
  skeleton's verification runs a Flutter integration test on a simulator.
- **Store accounts.** TestFlight needs an Apple Developer Program membership and
  Google Play internal testing needs a Google Play Console account. Neither has
  been confirmed.
- **AWS region.** `us-east-1` is used for now. Whether to move to a Middle East
  region for latency to Saudi users is decided in infrastructure design.
- **Cost.** Three environments are not priced. GitHub Actions minutes are now
  spread across five private repos, and iOS builds in `RaadMobile` on macOS
  runners cost more minutes than Linux runners. Enforcing branch protection
  needs a paid GitHub plan (finding 9).
- **Setup effort.** Each of the four MVP repos needs its own pipeline, branch
  protection, OIDC trust and README before the walking skeleton can run.
  Delivery planning sizes this against the SOW's short build period.
- **Monitoring.** The observability stage was not added, so the SOW's "basic
  monitoring" must be covered in NFR requirements, NFR design and
  infrastructure design.
- **One account.** `prd` shares an AWS account with `dev` and `stg`, so its
  isolation rests on separate stacks and IAM permissions. How each repo's role
  for deploying to `prd` is limited to that repo's approved `prd` step is
  settled in deployment pipeline design.
- **Second engineer's AWS access.** Whether the second engineer signs in to the
  AWS account through AWS SSO has not been recorded.
- **Sharing the AI-DLC record.** Both engineers use AI-DLC, and this piece of
  work's record lives in `Raad`. Who runs which stage, and how the two keep the
  record's state in step, is settled in delivery planning together with repo
  ownership.
- **Platform design.** `Raad`'s platform is the repo's intended responsibility,
  in the person's words: an API domain with API mappings per path prefix, one
  shared user pool, a shared event bus, an API firewall and rate limits. Domain
  design confirms it.
- **Platform outputs per environment.** How each service's stacks and pipeline
  find the platform's shared pieces in each environment, and how a service's
  API is attached to the shared API domain, is settled in infrastructure
  design.
- **`RaadWeb`'s hosting.** Where the landing page's S3 bucket and CloudFront
  distribution are defined is settled in infrastructure design: either a small
  CDK app in `RaadWeb`, which would bring the Python tooling into that repo, or
  the platform stacks in `Raad`, with `RaadWeb`'s pipeline only uploading the
  files.
- **`RaadMobile`'s smoke test.** What counts as the mobile app's smoke test
  before its `stg` build is made (for example the Flutter integration test
  against `dev`) is settled in the deployment pipeline stage.
- **Sharing the specs.** How `RaadMobile` gets each service's OpenAPI spec (for
  example a copy pinned to a tagged version of the service repo) is settled in
  contract design.
- **Qattah and Barq.** How the Barq app does group money pooling has not been
  looked at. That happens when Qattah is planned, after the MVP.
- **Dependency audit severity.** `pip-audit` lists known advisories but has no
  built-in severity threshold, so the CI pipeline stage must decide how "a high
  or critical finding blocks" is enforced (look up each advisory's severity, or
  block on every finding with reviewed, documented ignores).
- **Dart dependency audit.** The practices name a dependency audit for Python
  only. The CI pipeline stage may add one for the app's pub packages (for
  example OSV-Scanner, which reads `pubspec.lock`).
- **Data store for the concurrency test.** The concurrency test needs a real
  local container of the data store. Domain and infrastructure design should
  choose a data store that has a faithful local container, or record how the
  test is run instead.
- **Concrete AWS services.** The platform description uses the person's words,
  which point to particular AWS services. The concrete services for sign-in,
  the API, events and the data store are still decided in domain and
  infrastructure design. Beyond that, the practices name only CDK, S3 and
  CloudFront for the landing page, and the GitHub Actions to AWS access path.
