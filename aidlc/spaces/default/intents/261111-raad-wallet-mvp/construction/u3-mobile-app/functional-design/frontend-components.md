# Frontend Components — U3

## Component Hierarchy

App shell contains environment configuration, language setting, session boundary and navigation. Unauthenticated screens are SignIn, SignUp, Confirmation, ForgotPassword and ResetPassword. Authenticated tabs hold Wallet, Send and History; the shell also hosts setup-failed and session-expired states. Send contains AmountField/RecipientField, Review, SubmissionStatus and Result. Shared components are translated ErrorBanner, LoadingStatus, StaleBalance, TransferListItem and accessible Refresh.

## Props and State

| Component | Inputs | Owned state and outputs |
|---|---|---|
| Account forms | C3 adapter and local-language message catalog | Draft fields, submitting/error, explicit account actions; passwords memory-only |
| Session boundary | Protected tokens, verified account/environment, clock | One renewal, last-use time, navigation reset; discards responses from retired sessions |
| Wallet | Account-scoped BalanceSnapshot, data reader | Loading/error/stale/current, update time, manual refresh |
| Send draft | Current balance, connectivity, recipient resolver | Editable fields and validation; outputs review data, no financial request |
| Review/submission | Immutable reviewed data and submission controller | One persisted key at Confirm, sending/definitive/uncertain; no automatic retry |
| History | C1 page reader and account/environment | Page chain, opaque cursor, request generation and load-more lock; preserves rows on paging failure |
| Language selector | ar/en and installation preference | Updates layout/catalog without mutating financial state |

## Integration and Validation

Follow the ordered workflows in `functional-spec.md`. All data screens have separate loading, successful empty, error and loaded states. Use integer money and complete email validation; server errors preserve drafts. Screen-reader semantics announce state changes and expose labels, focus order and disabled-action reasons. Never bind display language to a request fingerprint. C4 and pinned C1/C3 adapters are the only environment/API integration inputs. Sources: `unit-of-work.md`, `requirements.md`, `components.md`, `stories.md`, `contract-summary.md` and the refined mockups/accessibility checklist.
