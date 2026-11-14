# U1 mobile — start now

Conversation language: English.

Engineer 2 owns RaadMobile. Start the mobile half of U1 now, in a short-lived branch in your own clone. Engineer 1 owns Raad and RaadMoneyService and is implementing the real backend. You can build against contract-based fixtures or a mock server until the deployed dev handoff is ready. Do not wait for U2 or change the backend repositories.

## Contract available now

The existing contract is published in RaadMoneyService on branch aidlc/u1-contract-handoff at commit `5dd760d2086c3b1fd2f017ed3999c07d0d4ee2d8`, verified against GitHub on 2026-11-14. Read `openapi/raad-money-v1.yaml` at that exact commit; generate the Dart request/response models from it rather than hand-maintaining another wire schema. This commit is an available development pin; the formal contract pre-release tag and full conformance remain separate delivery checks.

- [Published OpenAPI file](https://github.com/00az/RaadMoneyService/blob/5dd760d2086c3b1fd2f017ed3999c07d0d4ee2d8/openapi/raad-money-v1.yaml)

This guide is the current published mobile work allocation. The revised shared plan and test instructions are still local backend work; older copies on this branch do not mean the mobile mock/screen work must wait.

The published OpenAPI describes the completed v1 contract. The updated partial-U1 implementation and its contract annotations are still local work and have not yet been pushed. Use this published pin to begin screens/client/mock work, then update the pin at the integration handoff. U1 implements only the walking-skeleton subset below. Persistent transfer replay, full amount-limit rules and cursor pagination are U2 work. Do not enable those features from the full schema during U1.

## Work you own

- Bootstrap and pin the Flutter project and generate the C1 client. Keep authentication/session, client, integer money parsing and screens independently testable.
- Implement sign-in and explicit `PUT /money/v1/wallet` setup. Accept both existing-wallet 200 and created-wallet 201. `GET /wallet` does not create a wallet; handle WALLET_NOT_FOUND by setup.
- Implement wallet/balance, exact-email recipient entry, recipient review and confirmation, transfer result, and the first history page. A cancelled review sends no transfer.
- Parse SAR text into whole integer halalas; format with integer arithmetic and two fractional digits. Do not calculate money with floating point.
- Send the Cognito access token as Bearer authorization. Do not send caller identity fields. Keep the API base URL and Cognito settings configurable using the C4 nonsecret environment shape; use local mock configuration while real dev values are pending.
- Write `test/sign_in_test.dart`, `test/wallet_screen_test.dart`, `test/transfer_flow_test.dart`, `test/history_screen_test.dart` and `integration_test/walking_skeleton_test.dart`. Enforce at least 80% mobile line coverage. Run the journey on both iOS and Android when the real dev handoff is ready.

## Mock behavior that must match U1

- Preserve exact C1 response nesting and public fields from the pinned OpenAPI. Display the human reference separately from transferId and show the normalized recipient email on review. The UI never chooses a transfer's ID from a wallet ID.
- Errors have top-level `code`, `message` and `correlationId`. Branch on top-level `code`, not `error.code` or English message text. The older mobile README's `error.code` sentence is stale.
- Generate and send Idempotency-Key for a new intent, disable repeat taps while sending, and preserve input on a definitive business refusal. U1 validates the header but does not save replay outcomes or guarantee repeat-request safety.
- After timeout, lost response or any uncertain transfer outcome, block both automatic and manual resubmission. Reconcile using balance and history reads. Do not make the mock claim that an uncertain transfer was aborted or replay-protected.
- Keep history first-page-only. Do not promise complete history or pagination when the partial U1 response reports truncation. Coordinate the actual dev partial-release behavior before connecting the client.
- Exercise success, recipient not found, insufficient funds, invalid amount, expired/invalid authentication, missing wallet and uncertain submission. Never log credentials, tokens, personal details or request/response bodies.

## Integration handoff

Engineer 1 will provide the real dev URL, Cognito/C4 nonsecret values, contract revision and prepared test accounts through the approved secret mechanism. Do not hard-code a hostname or commit passwords. API, iOS and Android verification use separate fresh funded account pairs, initialized through PUT; never reset real users or directly seed deployed tables.

Open your mobile pull request with source revision, generated-client pin, widget/coverage results and both device results or explicit missing prerequisites. Engineer 1 reviews mobile; Engineer 2 reviews platform/service. The shared `scripts/verify-dev.sh` must pass API plus both device journeys before the integrated skeleton is complete.

U1 remains open until both workstreams and real integration checks are done. The backend's dedicated Transactions table is internal and does not prevent screen/client work against the agreed public contract.
