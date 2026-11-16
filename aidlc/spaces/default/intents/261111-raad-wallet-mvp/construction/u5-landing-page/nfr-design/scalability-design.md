# scalability design — u5-landing-page

Conversation language: English.

## Isolation
Static assets/CDN only, no database or per-visitor compute and no money-service capacity dependency. Concurrent fetch smoke verifies documents/assets at approved demo scale. Versioned assets allow cache reuse without hiding a bad deployment; no separate numerical throughput commitment.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
