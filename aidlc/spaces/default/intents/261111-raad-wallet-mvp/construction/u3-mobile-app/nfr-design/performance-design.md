# performance design — u3-mobile-app

Conversation language: English.

## Requests and rendering
Use a 15-second total request deadline. Only C1-permitted read/setup methods receive one retry for timeout/500/503, jitter 250–750 ms within deadline, respecting Retry-After; no automatic 429/write retry. Request-generation and account/environment epochs reject late responses. One in-flight operation per control; lazy history pages 20 default/100 max with no eager all-history fetch. Retain a bounded visible window plus cursor; a 1000-entry test journey must complete without duplicate requests. Offline disables writes and never creates a background financial queue. Device elapsed time stays separate from public API p95.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
