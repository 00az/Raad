# security design — u5-landing-page

Conversation language: English.

## Static boundary and privacy
No session, login, payment fields, analytics, cookies or third-party tracking. Only approved public contact abdulaziz.alrubai@outlook.com, visibly selectable and isolated LTR. mailto opens a handler without claiming delivery; no-handler state retains the address. No invented store/tester links.
Serve both documents/assets on controlled free subdomain plus custom ACM certificate with >=TLS1.2 as U1 DNS handoff requires; no default-certificate compliance assumption. Separate landing node/certificate validation records must fit free provider limits; otherwise block publication. Restrict content sources to self, no inline executable code, deny framing, nosniff and HSTS after HTTPS validation. Disable arbitrary query/referrer/access-body collection, no visitor telemetry.

## ar/en accessibility and verification
Semantic landmarks/skip link, correct lang/dir, keyboard focus and visible labels; Arabic/English copy and accessibility names complete. Reflow320dp/200% text, email LTR isolation and no horizontal content loss. Static HTML/CSS has no executable coverage percentage; require both-language deployed smoke, automated accessibility scan and actual keyboard/screen-reader/native Arabic review before release.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
