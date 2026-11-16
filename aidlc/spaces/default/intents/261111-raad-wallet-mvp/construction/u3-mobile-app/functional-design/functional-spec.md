# Functional Specification — U3 Mobile App

Conversation language: English.

## Scope and Ownership

U3 completes the MobileApp component in `unit-of-work.md` and `components.md`; Engineer 2 owns its source. Assigned stories in `unit-of-work-story-map.md` and `stories.md`: US1.1–US1.6, US2.2, US3.3–US3.6, US3.8–US3.9, US4.2–US4.4, US5.1–US5.3, US6.2 and US6.4. Existing U1 balance/review/result/history screens are extended rather than duplicated. All delivered frontend screens, errors, validation, loading states and accessibility text support Arabic and English (person, 77a32fc9). This is a design, not an assertion that these features are implemented.

## Account Workflows

1. Sign-up collects only email, display name and password. Trim/normalize email consistently with C3; show the password rule before entry: at least eight characters, uppercase, lowercase and digit. Keep email/name on refusals; never persist the password. A successful submission opens confirmation; a taken address is a clear sign-up refusal.
2. Confirmation accepts the emailed code. Wrong/expired code keeps the account unconfirmed and shows a local-language error. Resend is an explicit action, disabled while pending and rate-limited; show the same response whether the address exists. Only a new code works after resend, subject to U4's capability/fallback proof. Sign-in always offers the confirmation entry point for any email address.
3. Sign-in maps wrong password, unknown email and unconfirmed account to the same visible refusal, except the documented rate-limit response with retry timing. Use C3's configured actual provider adapter. A successful sign-in calls C1 PUT wallet setup, then loads balance/history; do not expose the wallet screen until setup is ready. Partial setup failure opens a retry state; PUT can safely repeat without another credit.
4. Password reset uses an email request followed by code and compliant new password. Invalid/expired codes change nothing. Do not blindly retry an uncertain account-changing request; explain how to restart safely.
5. Sessions renew silently after access-token expiry while eligible; concurrent requests share one renewal. A 31-day idle gap requires sign-in. Record last use using an explicit clock, reject clock anomalies conservatively, and never extend an expired provider refresh token. Renewal failure masks wallet screens and asks for sign-in. Sign-out clears credentials, account-scoped cached views, pending private state and navigation so back/reopen cannot reveal wallet data. Late responses from the old session are discarded.

## Money Workflow and State Machine

The completed U2 C1 contract is required before enabling same-key retries. Keep U1's uncertain/no-resubmit policy while using its partial prerelease; never infer replay capability from a successful request.

1. An editable draft keeps recipient and amount as text. Normalize the complete email for early feedback and parse decimal SAR digit-by-digit into integer halalas; no floating-point conversion. Enforce 100–50000 halalas inclusively with no daily aggregate limit. Server validation remains authoritative.
2. Resolve the recipient. Unknown/self/too-low/rate-limited outcomes preserve input and show the specific translated message. Lookup and sending both count under U4's abuse policy. Review shows resolved name/email, amount and projected balance; cancel sends nothing.
3. At first Confirm create one unique key and persist a PendingTransfer before sending. Lock recipient, amount, key, owner and environment. Disable additional submissions. The display reference and transferId are separate; preserve both from the response.
4. Definite success shows amount, recipient, reference and authoritative balanceAfter, then refreshes balance/history. A definitive business refusal preserves editable values; a new intentional attempt creates a new key, even for identical details.
5. Timeout, lost connection or ambiguous server response enters uncertain. Do not automatically repeat a transfer. Explain that the outcome is unknown and offer history inspection. Only after U2 replay is enabled may the person choose Try again using exactly the saved key and locked inputs. Changed details require an explicitly new intent, never reuse of the old key. Repeated ambiguity keeps the intent uncertain.
6. Persist pending state in protected account/environment-scoped local storage. After restart or reauthentication as the same account, restore the unresolved intent; another account cannot see or submit it. Explicit sign-out clears local private state, while server history/outcomes remain authoritative. A new session starts with reads, not an automatic send.

```text
draft -> review -> submitting -> completed | business-refused | uncertain
review -> draft (cancel, no request)
uncertain -> submitting (explicit same-key retry, completed U2 only)
uncertain -> history (read reconciliation, no new send)
offline -> draft/read-only (no queued financial write)
```

## Balance, History and Connectivity

BalanceSnapshot belongs to a verified user and environment and stores integer halalas and last successful UTC update time. Offline or failed refresh shows an old snapshot with an out-of-date label and update time. With no snapshot show an error, never a fabricated zero. Successful refresh replaces the snapshot and removes the stale label. Fetch results apply only to the latest matching screen/session request; stale responses cannot overwrite newer balances.

On open and explicit Refresh/pull-to-refresh, request balance and first history page. Do not add polling, background refresh or push. History shows sent/received, counterparty name/email, integer-formatted amount, reference and device-local time for the stored UTC instant. Preserve the service's completedAt/transferId order. An empty successful page says no transfers yet; a failed request says loading failed with Retry.

Load more uses the exact opaque nextCursor and unchanged page size. A paging failure keeps existing rows and offers retry for that same cursor; it never says the list is complete. Repeated taps share one operation. An invalid/expired cursor restarts page one and explains the refresh. An explicit refresh replaces the old chain; late responses from it are ignored. New transfers do not silently merge into an active snapshot. A null cursor is the only end-of-list signal.

Offline state disables Send/Confirm/Try again with a reason and reenables eligible actions when connectivity returns. Connectivity detection is advisory: transport failure can still occur while apparently online. Do not queue writes. Reads follow C1's one safe retry policy; financial writes and account changes do not inherit it.

## Language, Accessibility and Presentation

LanguageSetting is installation-scoped, Arabic or English. Switching language updates all frontend text/direction immediately without sign-out, losing draft input, changing the key or restarting an in-flight operation. Arabic layout is RTL; email, passwords, references and amounts remain isolated LTR content. Proposed A8 default is Western digits in both languages, with SAR / ر.س labels; explicit digit confirmation remains for review. The person's bilingual requirement is confirmed.

Apply `accessibility-checklist.md`: logical focus, named controls and roles, visible focus, keyboard/switch operation, status announcements, at least 44dp targets, non-colour status cues, 200% text with reflow/scrolling and no clipped actions. Refresh has a visible button; gestures are optional. Sign-in, wallet, review, send and history must pass VoiceOver/TalkBack walkthroughs on both platforms. Native Arabic review and actual logo asset remain release inputs; text RAAD is an acceptable draft brand treatment, not an invented logo.

## Contract and Acceptance Boundary

C1 generated clients read the pinned provider contract, ignore optional unknown response fields, and map unknown Error.code to a safe local message; closed request/configuration validation remains strict. C3 owns provider behavior and C4 supplies environment-bound nonsecret outputs, including the actual CloudFront URL. Reject invalid/cross-environment configuration before showing private data. Never log personal information or tokens.

U3 supplies dev/stg/prd builds plus a written acceptance journey for secure login, correct transfer/balance, duplicate refusal/replay, history and AWS execution. Each fresh account receives 1000 simulated SAR once in every environment, including prd (77a32fc9); no real payment details are accepted. Actual distribution through tester channels, staging proof and manual production approval remain deployment obligations, not results of this design. See `rules.md` for client behavior rules and `frontend-components.md` for state ownership.

## Sources

- `inception/requirements-analysis/requirements.md`: FR1–FR7, A3–A6, A8, NFR1–NFR4, NFR9–NFR11 and NFR15.
- `inception/units-generation/unit-of-work.md` and `unit-of-work-story-map.md`: U3 responsibility and shared stories.
- `inception/user-stories/stories.md`: assigned acceptance criteria named above.
- `inception/domain-design/components.md`: MobileApp, PendingTransfer, BalanceSnapshot and LanguageSetting ownership.
- `inception/contract-design/contract-summary.md`: C1–C5, replay cutover and cursor behavior.
- `inception/refined-mockups/accessibility-checklist.md`: bilingual accessibility and manual checks.
- `functional-design-questions.md` and person's message 77a32fc9.
