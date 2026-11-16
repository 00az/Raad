# performance design — u5-landing-page

Conversation language: English.

## Static delivery
Publish independent ar/en HTML documents and versioned local CSS/assets via static CDN; primary intro/language/contact links work with JavaScript disabled. No wallet/auth calls, server state or invented transfer-like page-latency SLO. Concurrent fetch smoke at demo100users/~10active checks both language documents and missing assets; unavailable page is a failure.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
