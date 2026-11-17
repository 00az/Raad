# Aziz U4 collaboration handoff

The person adopted the colleague's coordination instructions on 2026-11-16.

- Raad: fetched shared `aidlc/u1-money-service`, including requested `43a4bc3`; remote had advanced to `36861cd`. Created `aidlc/u4-platform-aziz` from that shared branch, not `main`.
- RaadMoneyService: fast-forwarded existing local branch to shared `bf7b19b`. Preserved local generated build/runtime files before pulling tracked deletions, restored them as ignored files, and verified a clean working tree. `cdk.out`, `.venv`, and `.hypothesis` are ignored and untracked. Preservation archive remains in the intent's ignored `.aidlc-engine/pull-backups/`.
- Claim only `u4-platform`. U2 belongs to Ziyad's Mac; no local U2 application implementation was made during the interrupted attempt. Do not publish or change U2 here.
- Dev account is now **305780340110**, with domain **raadwallet.com**. Do not deploy using the previous account. Confirm actual dev outputs/hostname from the shared platform deployment before configuring dependent integrations.
- Wait for Ziyad's first dev platform deployment before deploying U4 changes because the stacks overlap. Local U4 design/code/checks can proceed after its claim and approval requirements are satisfied. No deployment was made here.
- When U4 work is complete, use `aidlc unit publish u4-platform`; merge into the shared record is performed from Ziyad's side. U4 is not yet complete or published.
- First review task completed locally: see `mobile-pr-1-review.md`. No GitHub review/comment/approval or merge was submitted.
