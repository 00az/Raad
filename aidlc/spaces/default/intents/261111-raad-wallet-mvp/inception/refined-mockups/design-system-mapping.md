# Design System Mapping: RAAD Digital Wallet MVP

Conversation language: English.

RAAD has no design system of its own yet, so the app uses Flutter's Material 3 components, themed from the logo the person supplied (Q1). The landing page uses plain HTML and CSS with the same values (`team-practices.md`, Code Style). Every value below lives in one place in each codebase: a single theme file in `RaadMobile` and a single `:root` block of CSS variables in `RaadWeb`. Changing the brand later means editing those two places.

## Colour Tokens (dark theme)

The colours are proposed from how the supplied logo looks in the chat image: a near-black ground, silver-white chrome for the bolt and lettering, an electric-blue glint as the accent, and a warm peach highlight. No file was available to sample, so the hex values are the designer's choice in that style, not measurements. They must be checked against the real logo file, and adjusted if the logo's blue or silver differs, before the theme is treated as final. Contrast ratios were calculated with the WCAG 2.1 formula for these proposed values and must be recalculated if a value changes.

| Token | Value | Use | Contrast on `surface` (#12151B) |
|---|---|---|---|
| `bg` | #0A0C10 | Screen background | n/a |
| `surface` | #12151B | Cards, fields, tab bar | n/a |
| `surface-variant` | #1A1F28 | Balance card, pressed rows | n/a |
| `outline` | #6B7487 | Field borders, dividers, icon outlines | 3.89 to 1 |
| `text-primary` | #F2F4F8 | Titles, amounts, body | 16.60 to 1 |
| `text-secondary` | #AEB6C4 | Labels, hints, dates | 8.96 to 1 |
| `accent` | #5BA8FF | Primary button fill, links, focus ring | 7.39 to 1 |
| `on-accent` | #06121F | Text on the accent fill | 7.62 to 1 (on #5BA8FF) |
| `error` | #FF7A7A | Error text and outlines (always with an icon) | 7.24 to 1 |
| `success` | #5BDB8C | Received amounts, "Transfer sent" tick | 10.41 to 1 |
| `warning` | #F5C26B | "Out of date" notice (always with a clock icon) | 11.15 to 1 |
| `highlight` | #F3C9A9 | A 1 dp edge on the balance card; decoration only, carries no meaning | not text |

Full results: `text-primary` on `bg` 17.77 to 1, `text-secondary` on `bg` 9.59 to 1, `accent` on `bg` 7.91 to 1, `error` on `bg` 7.75 to 1, `outline` on `bg` 4.17 to 1. Every text pair is above the 4.5 to 1 minimum and every outline above the 3 to 1 minimum for interface parts.

Mapping to Flutter `ColorScheme`: `primary` = `accent`, `onPrimary` = `on-accent`, `surface` = `surface`, `onSurface` = `text-primary`, `onSurfaceVariant` = `text-secondary`, `outline` = `outline`, `error` = `error`, `background` = `bg`. `success` and `warning` are two extra theme colours held beside the `ColorScheme`.

## Typography

| Role | Size and weight | Used for |
|---|---|---|
| Display | 36 sp, semibold, tabular figures | The balance on S6, the amount on S8 and S9 |
| Title | 22 sp, semibold | Screen titles |
| Body | 16 sp, regular | Fields, list rows, messages |
| Label | 14 sp, medium | Field labels, hints, dates, tab names |

Font: one family that holds both Arabic and Latin letters, bundled with the app so it looks the same on every phone and in both directions. The proposed family is IBM Plex Sans Arabic, which is under the SIL Open Font License; the licence and the choice are confirmed at Construction. Text sizes scale with the phone's text-size setting up to 200% (AC5.2.2); no layout uses a fixed height for text.

Figures use Western digits (0 to 9) in both languages and tabular spacing, so amounts line up (assumption A8, accepted on Q9).

## Spacing and Shape

| Item | Value |
|---|---|
| Spacing scale | 4, 8, 16, 24, 32, 48 dp |
| Screen side margin | 16 dp |
| Corner radius | 12 dp for cards and fields, 24 dp for buttons |
| Minimum touch target | 44 by 44 dp; main buttons 48 dp high |
| Gap between touch targets | 8 dp at least |
| Elevation | None; depth comes from the `surface` and `surface-variant` colours |

## Component Mapping (Flutter, Material 3)

| Design element | Flutter widget | Notes |
|---|---|---|
| Primary button | `FilledButton` | `accent` fill, `on-accent` label, 48 dp high |
| Secondary button (Sign out) | `OutlinedButton` | `outline` border, `text-primary` label |
| Text button and links | `TextButton` | `accent` label |
| Text fields | `TextField` with `InputDecoration` | Label above, helper text below; error text with an icon |
| Password field | `TextField` with `obscureText` and a visibility `IconButton` | The toggle has a text label for screen readers |
| Bottom tab bar | `NavigationBar` with three `NavigationDestination`s | Wallet, Send, History; icon and label both always shown |
| Top bar | `AppBar` | Bolt mark at the start on S6; back arrow elsewhere |
| Cards | `Card` (filled style) | `surface-variant` with the `highlight` edge on the balance card |
| List rows | `ListTile` | Transfer entries |
| Loading placeholders | A shimmer built from `Container`s | Shape of the content they stand in for |
| Pull to refresh | `RefreshIndicator` | S6 and S10 |
| Banners | `MaterialBanner` | Offline and notices |
| Language choice | `RadioListTile` | S11 |
| Spinners | `CircularProgressIndicator` | Inside buttons and on first load |

No custom widgets are needed beyond `AmountField`, `RecipientField`, `BalanceCard`, `TransferListItem`, `StatusBanner` and `ConfirmationCodeField`, whose specifications are in `interaction-spec.md`.

## Direction and Language

- The app is built with Flutter's built-in text direction: Arabic uses right to left and mirrors the layout, English uses left to right.
- Icons that show direction (back arrows, the send and receive arrows) mirror; the bolt mark and the check mark do not.
- Strings live in one resource file per language. Nothing is typed into a screen as a literal.
- Dates and amounts follow the formats in `interaction-spec.md`.

## Responsive Behaviour

| Size | Behaviour | Source |
|---|---|---|
| Phone, portrait (320 to 480 dp wide) | The layouts in `mockups.md`. | Q6, answer A |
| Larger than a phone | The phone layout is shown centred in a column no wider than 480 dp. | Q6, answer A |
| Landscape | Turned off; the app stays in portrait. | Q6, answer A |
| Landing page, phone | Single column, 16 px side margin. | Q8, answer A |
| Landing page, larger | The same single column, centred, no wider than 720 px. | Q8, answer A |

## Motion

Transitions last under 300 ms. The "Transfer sent" tick fades in over 200 ms. When the phone asks to reduce motion, transitions and the placeholder shimmer are turned off.

## Landing Page Mapping

The page uses the same tokens as CSS variables (`--bg`, `--surface`, `--text-primary`, `--text-secondary`, `--accent`, `--on-accent`), a system font stack with the same bundled family as a web font, and a native `<a>` styled as a button with a `mailto:` link. It uses semantic elements (`header`, `main`, `footer`), a `lang` attribute that follows the language switch, and `dir="rtl"` in Arabic. It has no scripts that call the app's services (AC6.3.2).

## Assets

| Asset | Source | Status |
|---|---|---|
| Full lockup, transparent background | The supplied logo (Q1); the person provides the file | To be added; the colour tokens above are checked against it |
| Bolt mark alone, transparent background | The supplied logo (Q1); the person provides the file | To be added; the colour tokens above are checked against it |
| App icon (iOS and Android sizes) | Bolt mark on `bg` | To be made at Construction |
| Font files | IBM Plex Sans Arabic, proposed | To be bundled at Construction |
