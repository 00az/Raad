# Client Rules — u5-landing-page

Conversation language: English.

The UI interaction sequences in `functional-spec.md` are authoritative. This compact YAML view supports traceability without moving server business rules into the client.

```yaml
rules:
  - id: "BR5.1"
    statement: "RAAD introduction is available in Arabic and English"
    category: "policy"
    applies_to: "LandingPage"
    trigger: "Page load or language selection"
    logic: "Show RAAD, short reviewed description and access information in ar/en with matching document direction."
    violation_behaviour: "No untranslated or invented app-store availability."
    source: "FR8.1"
  - id: "BR5.2"
    statement: "Access requests go to the supplied public address"
    category: "policy"
    applies_to: "Contact action"
    trigger: "Request test access"
    logic: "Open a mail action to abdulaziz.alrubai@outlook.com and display the address for manual use; do not assert email delivery."
    violation_behaviour: "Keep the visible address usable when no mail handler exists."
    source: "FR8.1"
  - id: "BR5.3"
    statement: "Landing page contains no wallet or authentication data flow"
    category: "authorization"
    applies_to: "LandingPage"
    trigger: "Every render or network request"
    logic: "Load only static assets; never call money or sign-in services, collect payment details, or display wallet data."
    violation_behaviour: "Reject introduction of a money/auth integration."
    source: "FR8.1, NFR11"
  - id: "BR5.4"
    statement: "Both languages remain keyboard and assistive-tool usable"
    category: "policy"
    applies_to: "LandingPage controls"
    trigger: "Render or navigation"
    logic: "Provide semantic headings, skip link, visible focus, language/direction, LTR email isolation, 200 percent text and 320dp reflow."
    violation_behaviour: "Block release on inaccessible primary action."
    source: "FR6.3"
  - id: "BR5.5"
    statement: "Each site environment is checked independently over HTTPS"
    category: "constraint"
    applies_to: "LandingPage release"
    trigger: "Deploy smoke test"
    logic: "Fetch and check both language documents and contact target on the actual environment URL; U3 owns mobile tester builds."
    violation_behaviour: "Failed fetch is a failed deploy, not an empty page."
    source: "FR7.1, FR8.1"
```

## Rules Summary

- BR5.1: RAAD introduction is available in Arabic and English.
- BR5.2: Access requests go to the supplied public address.
- BR5.3: Landing page contains no wallet or authentication data flow.
- BR5.4: Both languages remain keyboard and assistive-tool usable.
- BR5.5: Each site environment is checked independently over HTTPS.

## Sources

`unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md`, `contract-summary.md`, the refined accessibility checklist and this unit's `functional-spec.md`.

