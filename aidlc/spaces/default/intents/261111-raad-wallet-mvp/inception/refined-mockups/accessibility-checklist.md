# Accessibility Checklist: RAAD Digital Wallet MVP

Conversation language: English.

The target is WCAG 2.1 level AA for the app and the landing page (Q7, answer A). Full validation needs testing with real assistive tools and an expert accessibility review; this checklist is what the design commits to and what a tester checks. It serves story US5.2 (screen reader and larger text) and criteria AC5.2.1 to AC5.2.3, and the loading, empty and error views of US5.3. Screens are named as in `mockups.md`; component behaviour is in `interaction-spec.md`.

## How This Is Tested

| Check | Tool | When |
|---|---|---|
| Contrast | The calculation in `design-system-mapping.md`, rechecked on the built screens | Code generation |
| Screen reader | VoiceOver on one iOS simulator or device, TalkBack on one Android emulator or device | Build and test, manual walk-through of S1, S6, S7, S8 and S9 |
| Text size | System text at 200% on both platforms | Build and test, all screens |
| Automated checks | Flutter's accessibility guideline tests (`meetsGuideline` for tap target size, labelled tap target and text contrast) in widget tests | Every pull request |
| Landing page | An automated scan (axe or Lighthouse) plus a keyboard-only pass | Every deploy of `RaadWeb` |

## Perceivable

| # | Requirement | Applied to | Design commitment |
|---|---|---|---|
| P1 | Text contrast of at least 4.5 to 1 | All screens | All text tokens measure 7.2 to 1 or higher on `surface` and `bg` (the lowest is the error colour at 7.24 to 1 on `surface`; see the table in `design-system-mapping.md`). |
| P2 | Contrast of at least 3 to 1 for interface parts and graphics | Field outlines, icons, focus ring | `outline` measures 3.89 to 1 on `surface`; the focus ring (`accent`) measures 7.39 to 1. |
| P3 | Meaning not carried by colour alone (AC5.2.3) | S6, S10 (sent or received), S6 (out of date), all errors | Sent and received differ by an arrow icon, the words "Sent to" or "Received from" and a sign on the amount. Errors have an icon and text. "Out of date" has a clock icon and text. |
| P4 | Text alternatives for non-text content | Logo, icons, arrows | The logo has the text alternative "RAAD". Decorative icons are hidden from screen readers; an icon that carries meaning is read as its words. |
| P5 | Text can be resized to 200% without losing content or function (AC5.2.2) | All screens | No fixed-height text containers; screens scroll when needed; buttons grow with the text. |
| P6 | Reflow: no horizontal scrolling at a 320 dp width | All screens, landing page | Single column layouts. |
| P7 | No content flashes more than three times a second | All screens | The only animations are a fade and a placeholder shimmer. |
| P8 | Text spacing and language | App, landing page | The page language is declared (`lang="ar"` or `lang="en"`) and text direction is set per language. Mixed Arabic and Latin content follows the per-field rules in "Mixed-direction rules" in `mockups.md`: emails, reference codes, passwords and amounts keep left-to-right content with an isolated direction inside the mirrored layout. |

## Operable

| # | Requirement | Applied to | Design commitment |
|---|---|---|---|
| O1 | Touch targets of at least 44 by 44 dp with 8 dp between them | All screens | Main buttons 48 dp; links get a 44 dp tall tap area; tabs 56 dp. |
| O2 | Everything can be done with a screen reader and with a keyboard (switch access on the phone) | App, landing page | Every control is a standard widget with a label; no gesture is the only way to do something. Pull to refresh has an always-visible **Refresh** button (44 dp, labelled "Refresh") in the top bar of S6 and S10, so no one needs the gesture to see money that has arrived. |
| O3 | Logical focus order that follows the reading order, in both directions | All screens | Focus runs top to bottom and, in Arabic, starting from the right. |
| O4 | A visible focus indicator | Fields, buttons, links, tabs | A 2 dp `accent` outline. |
| O5 | No time limit on typing | S2, S3, S5, S7 | There is no timer on any form; the confirmation code expires on the server only. |
| O6 | No keyboard or screen-reader trap | S8 and S9 | While a transfer is sending, buttons are off but focus can still reach the status text. |
| O7 | Reduced motion respected | All screens | Transitions and shimmer are off when the phone asks. |
| O8 | Skip link on the landing page | S12 | "Skip to content" is the first focusable item. |

## Understandable

| # | Requirement | Applied to | Design commitment |
|---|---|---|---|
| U1 | Every field has a visible label | All forms | Labels sit above the fields; a placeholder is never the only label. |
| U2 | Errors are named in text and say how to fix them | All forms | Messages are in the message catalogue; each names the field and the fix. Focus moves to the first field with an error. |
| U3 | The password rule is shown before the user types | S2, S5 | The rule text is always visible under the field. |
| U4 | Important submissions can be reviewed and confirmed (financial) | S7 to S9 | A review screen shows who, how much and the balance after, with a Confirm button (AC3.2.1). |
| U5 | Consistent navigation and labels | All screens | The three tabs are always in the same order and named the same. |
| U6 | The user is told what is happening | S8, S9, S6, S10 | A spinner and text for waiting; "We could not confirm the transfer" explains the next step (AC3.8.1). |
| U7 | Predictable behaviour: no context change on focus or input | All screens | Nothing submits or moves screens until the user presses a button. |

## Robust

| # | Requirement | Applied to | Design commitment |
|---|---|---|---|
| R1 | Controls expose name, role and state to assistive technology | All screens | Standard Flutter widgets with semantic labels; custom components (`AmountField`, `BalanceCard`, `TransferListItem`) set their own labels as listed in `interaction-spec.md`. |
| R2 | Status messages are announced without moving focus | Banners, errors, "Transfer sent" | Announced as live regions (Flutter `SemanticsService.announce` or a live-region `Semantics`). |
| R3 | Valid markup on the landing page | S12 | Semantic HTML; the page is checked by the automated scan. |

## Per-Screen Screen Reader Reading

| Screen | What a screen reader says (English) |
|---|---|
| S1 | "Sign in. Email address, text field. Password, secure text field, show password button. Forgot password, link. Sign in, button." |
| S6 | "Balance, 1,234.56 riyals, updated just now. Send money, button. Latest transfers, heading. Sent to Khalid, khalid at example dot com, 100 riyals, 11 November 2026 at 14:05." |
| S7 | "Send money. Your balance, 1,234.56 riyals. Recipient's email address, text field. Amount in riyals, 0 riyals 0 halalas, text field. From 1.00 to 500.00 riyals. Continue, button." |
| S8 | "Review transfer. You are sending 100 riyals to Khalid Al-Qahtani, khalid at example dot com. Your balance after, 1,134.56 riyals. Confirm, button. Change details, button." |
| S9 | "Transfer sent. 100 riyals to Khalid Al-Qahtani. Reference RAAD 7 K 2 M 9 Q X D. Your balance, 1,134.56 riyals. Done, button." |
| S10 | "History, heading. Then each entry as in S6, and Load more, button." |

## Open Items

- The Arabic screen-reader wording is checked together with the Arabic message catalogue by a native reader (carried from `requirements.md`).
- Contrast on the real screens is rechecked when the final theme is built, because the supplied logo has soft glows whose edges are not text.
- Whole-product WCAG conformance cannot be claimed from this checklist alone; it needs the manual testing listed above and an expert review.
