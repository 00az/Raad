# U4 start blocker — missing U2 lifecycle evidence

## Confirmed state

- U4 claim generation 1 belongs to AzPsu, from integration commit `5293bbb6afc0b9d64202ad6723f3cabf208a3392`.
- The U4 16-step Code Generation plan and test instructions are approved. No U4 implementation source has been generated.
- `aidlc engine state unit start --stage code-generation --unit u4-platform` refuses because U2 is still open in the lifecycle ledger.
- `aidlc engine audit history --stage code-generation --event UNIT_STARTED --limit 8` identifies the U2 start at `2026-11-16T14:57:46Z`, with run floor `STAGE_JUMPED:2026-11-16T14:12:56Z#3`.
- The original start is also present in the tracked audit shard on `origin/main`; this is not merely an ignored local cache. The current completion history has no U2 Code Generation completion. Earlier U2 receipts cover earlier design work and do not close this start.
- The shared state projection marks U2 approved. The claim path reads that integration state, whereas unit start checks lifecycle receipts. This explains why U4 can be claimed but cannot start.
- The fetched RaadMoneyService U2 branch at `2b3660b` contains no audit shard at the active record's audit path from which to recover the missing receipt.

## Required co-engineer handoff

Please restore/export U2's original Code Generation completion and approval evidence through the supported AI-DLC record path, preserving its actual stage attempt and artifact/review bindings. Keep personal addresses out of the shared export. If no valid completion receipt was recorded, reconcile U2 from its approved source, tests and review in the co-engineer's authoritative checkout using AI-DLC; do not fabricate a receipt or hand-edit the state/audit files.

Land the reconciled shared record through a reviewed PR, then Engineer 1 can pull it and retry the U4 start. If valid completion evidence is present but the refusal persists, the next work is a targeted framework defect report/fix for claimed-unit lifecycle isolation, not weakening the checks.

## Preserved boundaries

Do not mark U2 complete from the U4-scoped checkout, alter the co-engineer's source, disable checks, remove historical audit rows or relinquish/recreate the U4 claim to get around this refusal. No deployment or other AWS operation is required to repair the record. The existing U4 approval stays available while this evidence is reconciled.
