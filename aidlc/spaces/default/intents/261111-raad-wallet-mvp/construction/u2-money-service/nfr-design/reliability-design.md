# reliability design — u2-money-service

Conversation language: English.

## Atomic success and replay
Ledger transaction adapter alone mutates money: conditionally debit/credit, canonical Transactions row, required unique reference markers, both wallet sequence/version changes and final immutable request outcome in one transaction. No separately durable reserved/pending key. Precommit failure has no financial effect. Timeout after possible commit requires strong outcome reread with original key; never send a new key to resolve uncertainty. Competing conditional result writers reread and replay the winner or report fingerprint conflict.

## Refusal and setup behavior
Validate authentication/schema first; malformed/noninteger amount returns 400 without a consumed key. Missing caller wallet also consumes none. Existing-key replay/conflict precedes new business evaluation. For a new valid request, C1 refusal order is unknown recipient, integer amount range, self-transfer, then balance. Save a final business refusal conditionally without money/history mutation; re-evaluate optimistic conflicts before choosing a new final result.
Wallet setup is wallet commit followed by Directory readiness. A retained DirectoryPending wallet is repaired by PUT without another credit; precommit-absent setup may retry creation. Exactly one opening 100000-halala simulated credit per wallet in every environment including prd. Record C2 receipt only after ready; same event ID/different user conflicts, later distinct event/same initialized user is a no-op. Accepted events retry for 24 hours then DLQ/alarm; publish failure does not fail account confirmation, and PUT is the safety net.

## Recovery
Retain and enable PITR for all three persistent stg/prd tables, including Directory profile versions, outcomes/receipts and canonical transfer history. Dev reset only by explicit authorization. Restore to a common selected instant into new tables; a timestamp alone is not cross-table atomicity proof. Reconcile opening credits plus every canonical debit/credit with wallet balances, ordinals/references, outcomes, profile references and receipts before cutover. If inconsistent, select an earlier consistent point within RPO or fail the release gate; never reset or fabricate adjustments.
Selected targets remain RPO <=5 minutes, RTO <=3 hours and prd calendar-month availability >=99.5%. Measure detection, restoration, validation and cutover in a timed drill. PITR alone does not prove the 5-minute RPO; verify latest restorable point and actual lost committed work. Infrastructure supplies alarms and retained configuration. No active-active failover is claimed.

## Bounded failures
Read/setup retry at most once for permitted timeout/500/503, jitter 250–750 ms within deadline; honor Retry-After, no automatic 429 retry and no automatic transfer retry. Business refusals do not open technical-failure alarms. Financial dependency failure fails closed; no stale balance success or queued money writes.

## Acceptance and readiness
Money remains integer halalas, conserved across transfers except one-time opening credits, never negative. Test property-based and concurrent real-store cases; money-core coverage >=95% line AND branch, each owning repo >=80% line with strict typing/lint/audit/pinned-contract checks and the affirmed PR process. Store offset-bearing UTC instants. Separate process liveness from authenticated internal persistence readiness; dependency probes return safe status only and never expose resource names or profile data. Public technical failure contributes to availability even when handler liveness passes.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design/functional-spec.md and rules.md; shared inception/contract-design/contract-summary.md and domain-design/components.md; U1 nfr-design/nfr-design-questions.md (free DNS decision b8664859). No target is lowered by this revision.
