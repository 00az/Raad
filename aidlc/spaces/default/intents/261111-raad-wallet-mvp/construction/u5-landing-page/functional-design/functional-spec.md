# Functional Specification — U5 Landing Page

Conversation language: English.

## Scope

U5 implements US6.3 and the landing-page part of US6.2 from `stories.md` and `unit-of-work-story-map.md`. The LandingPage component in `components.md` is a public static introduction with no sign-in, wallet data, money-service calls or personal-data collection. All content and controls support Arabic and English (77a32fc9).

## Content and User Workflow

1. Opening the HTTPS page displays RAAD, a short introduction, language selection and Request test access. Draft introduction for review: English, “RAAD is a demo wallet for sending simulated Saudi riyals between RAAD users.” Arabic, “رعد محفظة تجريبية لإرسال مبالغ افتراضية بالريال السعودي بين مستخدمي رعد.” Clearly state that funds are simulated and no real payments are processed.
2. Arabic uses RTL layout and English LTR; the language control changes content, document language and direction without a server account or sign-in. Both language versions remain available without application JavaScript. Language may be expressed in the selected document URL; it contains no user or wallet data.
3. Request test access opens the person's mail application addressed to abdulaziz.alrubai@outlook.com. Translate the accessible label and optional subject; do not include account details or financial information in the URL. If no mail handler exists, the address remains visible and selectable with instructions to email it. Do not claim a request was sent merely because a mail application opened. This public contact differs from the operational alert address jjii0@hotmail.com.
4. No app-store download link is invented. Until tester-channel destinations exist, the access-request action explains how to obtain access. The page has no form backend, analytics registration, cookie consent dependency, wallet call, authentication call or push registration.

## State, Failure and Accessibility

States are language-ar / language-en / page-unavailable at the hosting boundary; there is no user or wallet state. A missing asset retains text RAAD and the contact action. Escape all product text and link attributes. Long text and email reflow at 320dp and 200% text. Provide a first-focus skip link, semantic headings, visible keyboard focus, correct reading order, a named language control and non-colour status. Isolate the email address LTR within Arabic layout. No gesture is required. Static-page failure is a real failed smoke test, never a successful empty page.

## Environment and Acceptance

Each environment publishes its own static build via the U5 infrastructure. Use AWS-generated HTTPS hostnames without domain purchase as requested; concrete hosting and certificate policy belong in Infrastructure Design. Smoke checks fetch each deployed language page, verify product/description/contact, usable HTTPS and no unexpected money/auth requests. Acceptance requires real browser keyboard/accessibility checks and native Arabic wording review; neither is claimed by this specification.

## Rules Summary

BR5.1 covers content in both languages; BR5.2 contact behavior; BR5.3 privacy/no wallet integration; BR5.4 accessibility; BR5.5 environment smoke checks. This UI-only specification is authoritative for interactions; `rules.md` is its compact traceability view.

## Sources

- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: U5 and US6.2/US6.3.
- `inception/requirements-analysis/requirements.md`: FR8.1, FR7.1, A9 and simulated-money constraint.
- `inception/user-stories/stories.md`: AC6.2.1–AC6.2.2 and AC6.3.1–AC6.3.2; mobile tester builds remain U3-owned.
- `inception/domain-design/components.md`: LandingPage ownership and no service dependencies.
- `inception/contract-design/contract-summary.md`: no new money or identity boundary for the page.
- Refined mockups/accessibility checklist and answered `functional-design-questions.md` (77a32fc9).
