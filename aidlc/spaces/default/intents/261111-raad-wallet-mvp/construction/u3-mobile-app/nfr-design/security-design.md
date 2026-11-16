# security design — u3-mobile-app

Conversation language: English.

## Identity and private state
Use existing Flutter/native secure-storage adapters for access/refresh tokens and account/environment-bound pending intent. Never persist passwords/codes. Validated session subject owns every private state/cache/navigation epoch. Sign-out clears private state and invalidates in-flight epochs; back/reopen/account switch cannot recover the previous account. Use C4 validated HTTPS URLs and native certificate/hostname checks, TLS >=1.2, no debug bypass in release. Revalidate server authority; disabled buttons grant none.

## Safe interaction and accessibility
Persist immutable key/recipient/whole-halalas amount before sending and bind to capability/profile and account. Locale change preserves all financial fields/key. Every string, semantic label, validation/error/empty/loading/stale/uncertain state supports ar/en; isolate email/digits LTR inside RTL. Western-digit choice A8 remains an explicit proposed assumption, not a human decision. Design responsive 320dp/200% text, logical focus, keyboard/switch and screen-reader announcements without relying on color.
No personal diagnostic fields, token/body/cursor/key or crash payload. Unknown server error uses a safe localized fallback. 429 displays Retry-After and requires explicit later action. Validate actual release storage/network adapters and privacy scans; >=80% line coverage plus format/lint/pin checks and actual VoiceOver/TalkBack evidence on both platforms.

## Sources
This unit's six nfr-requirements documents and tech-stack-decisions.md; functional-design artifacts where applicable; shared C1–C5 contracts and domain components. U1 nfr-design/nfr-design-questions.md records the free DNS decision and pending provisioning checks. These are designs, not executed acceptance evidence.
