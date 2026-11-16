# scalability design — u2-money-service

Conversation language: English.

## Capacity and isolation
Stateless per-environment Lambda, initial reserved concurrency 20 subject to actual account quota and measured demo load. DynamoDB on-demand, owner/entity partitions, no global counter, no scans, no active-active region or extra cache tier. Alarm before changing limits. Scale changes retain all conditional money invariants.

## Stable history with eventually consistent indexes
One canonical Transactions row carries senderWalletId/recipientWalletId, completedAt/transferId and per-role completion ordinals. Each wallet carries transferSequence and lastCompletedSortKey. In the successful transaction, condition on both wallet versions, increment both sequences and insert the canonical row with their next ordinals plus the final request outcome and required reference markers. Indexes are projections of this row, not separately writable transfer copies.
A new completion key must sort strictly after both wallets' previous completion keys. Generate a trusted UTC completion instant and a tie-breaking ID that meets that condition; if a prior timestamp is ahead of the trusted clock, wait within the deadline or fail safely without a commit. Never invent a future completion timestamp to force progress.
First-page strong wallet read fixes sequence N and maximum sort key. Query both role indexes at or below that snapshot, strict below the last returned key thereafter, with bounded limit+1 per stream; merge by completedAt DESC/transferId DESC. Strongly batch-read candidates from the canonical table, authorize wallet ownership and verify exact descending wallet ordinals N,N-1,... for each returned slot. GSI lag, missing/corrupt rows or ordinal mismatch triggers bounded reread then safe 503; do not return a partial page or an end cursor. A valid end has exhausted expected ordinal down to zero. This detects missing index entries instead of treating GSI reads as strongly consistent.
Authenticated opaque 24-hour cursor binds environment/caller, original snapshot sequence/key, next expected ordinal, last key, limit/sort and expiry. New writes have later keys and do not enter the chain. User restarts fresh paging after cursor expiry.

## Migration and proof
Quiesce financial writes for U1-to-U2 migration. Assign historical per-wallet ordinals in existing ascending C1 order, seed counters/high-watermarks without changing balances/IDs/times, build both GSIs and prove contiguous coverage before switching readers. Retain old reference reads until cutover verified. Test ties, opposing concurrent transfers, delayed index projections, lost response, >1000 records and cursor tampering. This algorithm is a code-generation obligation; no claim it is implemented or load-proven.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design/functional-spec.md and rules.md; shared inception/contract-design/contract-summary.md and domain-design/components.md; U1 nfr-design/nfr-design-questions.md (free DNS decision b8664859). No target is lowered by this revision.
