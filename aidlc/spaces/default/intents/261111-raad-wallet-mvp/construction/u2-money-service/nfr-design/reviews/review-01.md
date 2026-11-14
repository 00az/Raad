## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-11-13T17:42:27Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/nfr-design/reliability-design.md > Atomic Money and Idempotency | The refusal precedence reverses the C1 order: this design evaluates amount range before recipient-not-found, while C1 says unknown recipient precedes amount range, then own-wallet refusal, then insufficient funds. Because the first business refusal is persisted per key, this changes the saved result and replay behavior for requests that violate multiple rules. | Preserve the C1 ordering exactly in the reliability design and its provider tests. | New |
| R-02 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/nfr-design/security-design.md > Identity and Request Authorization; aidlc/spaces/default/intents/261111-raad-wallet-mvp/inception/contract-design/contract-summary.md > C5 key discovery | C5 limits verifier key caching to six hours, throttles unknown-key refreshes to once per minute, and requires continued use of an unexpired cached key set when discovery fails. The design says only to cache keys until key expiry, refresh on every unknown key ID, and fail closed on any failed refresh. This can cause unnecessary discovery load and reject otherwise valid tokens during a temporary discovery outage. | Specify C5's cache maximum, refresh throttle, and cached-key fallback behavior, including 503 only when no usable cached key set remains. | New |
| R-03 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/nfr-design/reliability-design.md > Atomic Money and Idempotency; aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/functional-design/functional-spec.md > Create or Replay a Transfer and State Transitions | Functional Design describes `absent -> reserved -> completed/refused`, while this design explicitly forbids a separate durable reservation and commits the request outcome atomically with the final result. These lead to different persisted states and crash/retry behavior, so implementation cannot follow both artifacts as written. | Align the functional state machine and reliability design on whether `reserved` is a persisted state; keep the C1 externally observable behavior and define the matching crash-recovery path. | New |
| R-04 | Major | aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/nfr-design/traceability.json > NFR5.3–NFR5.5; aidlc/spaces/default/intents/261111-raad-wallet-mvp/construction/u2-money-service/nfr-requirements/reliability-requirements.md > NFR5.3–NFR5.5 | The design carries forward NFR5.3 atomic transfer, NFR5.4 idempotent replay, and NFR5.5 duplicate event protection as children of inception NFR5, which is availability. Atomicity belongs under NFR3 and duplicate protection under NFR4; this mislabels the inherited obligations and hides them from the correct NFR trace. | Correct the detailed requirement IDs and update this design's upstream IDs and coverage targets to follow the applicable inception NFR parents. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| traceability sensor | PASS (`fire_id` `676b57ba`) | All listed design inputs map to existing detailed NFR IDs, but the sensor does not identify that some inherited IDs belong to the wrong inception NFR parents. |
| required-sections sensor | PASS (`fire_id` `1b3d6ef8`) | Security design passed the configured section check. |
| upstream-coverage sensor | PASS (`fire_id` `70f2c388`) | Security design references its required upstream inputs. |
| AWS Lambda Function URL documentation | Verified: `AWS_IAM` callers require `lambda:InvokeFunctionUrl` and `lambda:InvokeFunction`; requests require SigV4. [Access control](https://docs.aws.amazon.com/lambda/latest/dg/urls-auth.html), [invocation](https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html). | The design's Function URL permission and SigV4 claims are supported by current AWS documentation. |
| DynamoDB transaction documentation | Verified: transactions are atomic across distinct items and may span tables in the same account and Region. [Transaction constraints](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html). | The proposed cross-table wallet setup and transactional transfer patterns are feasible under the stated single-account, single-Region environment. |
| DynamoDB point-in-time recovery documentation | Verified: the latest restorable point is typically about five minutes behind current time. [PITR behavior](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery_Howitworks.html). | This supports the stated RPO target, subject to the design's required measured restore exercise. |
| linter / type-check sensors | Not run | These inspect TypeScript/JavaScript snippets; the reviewed design artifacts contain no such snippets. |

### Summary

The proposed AWS building blocks and citations support the main implementation claims, and the NFR design traceability sensor passes. However, the persisted refusal order, verifier key-discovery behavior, transfer state model, and inherited NFR IDs disagree with the approved contracts or upstream requirements, so the service cannot be built consistently from these artifacts yet.
