## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-13T17:00:40Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/functional-design/functional-spec.md > Workflow: Create or Replay a Transfer, steps 3–5; State Transitions | A key is reserved before the first business outcome is written, but the design has no lease, expiry, or recovery path for a process that stops after reservation. Such a key can remain `reserved` indefinitely, leaving identical retries waiting without a result. | Define how an abandoned reservation is detected and recovered without allowing two workers to move money, or make the reservation and terminal outcome part of one recoverable atomic protocol. Add a crash-after-reservation recovery scenario. | New |
| R-02 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/functional-design/functional-spec.md > Workflow: Create or Replay a Transfer, step 4; aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/functional-design/rules.md > BR2.4–BR2.7 | C1 fixes the persisted refusal order as unknown recipient, amount out of range, own wallet, then insufficient balance. The functional design does not preserve that order: it places self-transfer and amount checks together and does not state which wins when a request violates both. Different implementations can persist different replay results for the same key and request. | State the C1 refusal order explicitly in the workflow and rules, including the precedence when a request violates multiple business rules. | New |
| R-03 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/functional-design/functional-spec.md > Workflow: Wallet Setup, step 1; aidlc/spaces/default/intents/261111-raad-wallet-mvp/inception/contract-design/contract-summary.md > C5 verifier configuration, `profileAttributeSource` | C5 permits wallet profile attributes to come from access-token claims or a configured user-profile endpoint. U2's setup workflow only specifies verified token claims or the event payload, so it does not define what happens when the environment selects `user-profile-endpoint` or requires `userProfileUri`. | Define wallet setup behavior for each configured profile source, including endpoint subject matching and safe failure when the configured profile cannot be retrieved. | New |
| R-04 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/functional-design/entities.md > UserConfirmedEventReceipt attributes and constraints; aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/functional-design/rules.md > BR2.11 | The design promises idempotency by both `eventId` and `userId`, but the receipt entity marks only `eventId` unique and does not define a uniqueness constraint or conditional operation for `userId`. Two distinct or concurrent events for one user can therefore create multiple receipt records, contrary to BR2.11's no-op behavior. | Define the environment-scoped uniqueness and conditional-write behavior for both event ID and user ID, including the result when the two identifiers point to conflicting receipts. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| traceability sensor | PASS (`fire_id` `e766c60e`) | Traceability structure and targets passed the configured sensor. |
| required-sections sensor | PASS (`fire_id` `76a67027`) | Functional specification required sections passed. |
| upstream-coverage sensor | PASS (`fire_id` `54f8e48c`) | The functional specification references its required upstream design inputs. |
| linter / type-check sensors | Not run | The stage definition limits these to TypeScript/JavaScript snippets; the reviewed artifacts contain no such snippets. |

### Summary

The design covers the requested money-service workflows and its traceability sensors pass. It still leaves recovery for abandoned idempotency reservations, the contract's persisted refusal precedence, the C5 profile-source choice, and event receipt uniqueness under-specified, so implementers could produce incompatible or stuck behavior.
