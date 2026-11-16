# Client Rules — u3-mobile-app

Conversation language: English.

The UI interaction sequences in `functional-spec.md` are authoritative. This compact YAML view supports traceability without moving server business rules into the client.

```yaml
rules:
  - id: "BR3.1"
    statement: "Account screens use confirmed C3 rules and safe setup"
    category: "authorization"
    applies_to: "Account screens"
    trigger: "Account action"
    logic: "Validate email/password/code, map sign-in refusals uniformly, and require safe wallet setup before private screens; sign-out clears private navigation and old-session responses."
    violation_behaviour: "Show translated safe refusal; preserve nonsecret form values."
    source: "FR1.1, FR1.2, FR1.3, FR1.4, FR1.5, FR1.6"
  - id: "BR3.2"
    statement: "Session renewal and idle expiry preserve identity boundaries"
    category: "authorization"
    applies_to: "Session"
    trigger: "Authenticated request or reopen"
    logic: "Share a silent renewal for eligible sessions; after 31 days idle require sign-in; never reuse a pending request under another account/environment."
    violation_behaviour: "Mask private data and require sign-in on failure."
    source: "A5, NFR1"
  - id: "BR3.3"
    statement: "Client money validation uses integer halalas and keeps inputs"
    category: "validation"
    applies_to: "Send form"
    trigger: "Review request or refusal"
    logic: "Accept inclusive 100 through 50000 halalas, normalize complete recipient email, refuse known self/insufficient amounts and show server refusals without erasing fields; no daily limit."
    violation_behaviour: "No financial request until review and Confirm."
    source: "FR3.1, FR3.2, FR3.5, FR3.6, FR3.12"
  - id: "BR3.4"
    statement: "One confirmed intent has one immutable key and explicit uncertain retry"
    category: "constraint"
    applies_to: "PendingTransfer"
    trigger: "Confirm, timeout, restart or retry"
    logic: "Persist owner/environment/key/recipient/amount before first send; suppress double taps; only explicit U2-capable same-key retry may repeat an uncertain intent; new intent gets a new key."
    violation_behaviour: "Keep uncertain state and offer history inspection; no automatic resubmission."
    source: "FR3.7, FR3.9, FR3.10, NFR4"
  - id: "BR3.5"
    statement: "Offline state disables writes and labels stale balance"
    category: "policy"
    applies_to: "Connectivity and BalanceSnapshot"
    trigger: "Network failure, refresh or recovery"
    logic: "Never queue transfers; show last successful account-scoped balance with update time and stale label, or an error if none; successful refresh removes the stale label."
    violation_behaviour: "Never show missing balance as zero."
    source: "FR2.3, FR6.4"
  - id: "BR3.6"
    statement: "History uses explicit refresh and one bound paging chain"
    category: "policy"
    applies_to: "History"
    trigger: "Open, Refresh or Load more"
    logic: "Render completed caller-only rows in supplied order and device time; retain rows on paging failure, restart expired cursor chains, ignore stale responses; no polling or push."
    violation_behaviour: "Separate empty/loading/error and provide retry without duplicate page append."
    source: "FR4.1, FR4.2, FR5.1, FR5.2, FR5.3, FR5.4, FR5.5, FR5.6, NFR15"
  - id: "BR3.7"
    statement: "Every frontend supports Arabic and English accessibly"
    category: "policy"
    applies_to: "All mobile screens"
    trigger: "Render or language change"
    logic: "Switch language/direction immediately without changing identity/key/input; isolate LTR technical values; label every control and status, support 200 percent text and screen readers."
    violation_behaviour: "Do not ship clipped, untranslated or colour-only status."
    source: "FR6.1, FR6.2, FR6.3"
  - id: "BR3.8"
    statement: "Environment builds and acceptance keep simulated funds isolated"
    category: "constraint"
    applies_to: "Build and acceptance journey"
    trigger: "Build or acceptance run"
    logic: "Validate C4 against selected environment, generate from pinned C1, use separate identities, and verify the six success criteria including one 1000 simulated SAR opening credit in prd; production requires passing staging and manual release approval."
    violation_behaviour: "Reject mismatched config; report unrun live checks as unverified."
    source: "FR7.1, FR7.2, NFR14"
```

## Rules Summary

- BR3.1: Account screens use confirmed C3 rules and safe setup.
- BR3.2: Session renewal and idle expiry preserve identity boundaries.
- BR3.3: Client money validation uses integer halalas and keeps inputs.
- BR3.4: One confirmed intent has one immutable key and explicit uncertain retry.
- BR3.5: Offline state disables writes and labels stale balance.
- BR3.6: History uses explicit refresh and one bound paging chain.
- BR3.7: Every frontend supports Arabic and English accessibly.
- BR3.8: Environment builds and acceptance keep simulated funds isolated.

## Sources

`unit-of-work.md`, `unit-of-work-story-map.md`, `stories.md`, `requirements.md`, `components.md`, `contract-summary.md`, the refined accessibility checklist and this unit's `functional-spec.md`.

