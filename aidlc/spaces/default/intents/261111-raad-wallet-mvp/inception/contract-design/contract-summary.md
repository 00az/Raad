# Contract Summary: RAAD Digital Wallet MVP

Conversation language: English.

This document fixes every formal boundary needed by the five units in `unit-of-work.md` and the dependency graph in `unit-of-work-dependency.md`. It follows the choices in `contract-design-questions.md` (Q1 to Q7, all answer A), the building blocks in `components.md`, and the measurable behavior in `requirements.md`.

The shared-code edges from U1 to U2, U3 and U4 are not runtime boundaries: later units extend code introduced by U1 in the same repos. U5's edge on U1 is a sequencing constraint from the walking-skeleton practice, not an integration. Those edges therefore need no protocol contract. Five actual boundaries remain.

## Contracts

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---|---|---|---|
| C1 | U2 `u2-money-service`, behind the U4 edge | U3 `u3-mobile-app`; External: any later approved RAAD client | Synchronous REST/HTTPS with JSON, OpenAPI 3.1, base path `/money/v1` | U2 owns the API behavior and OpenAPI; U4 owns edge behavior in C5 |
| C2 | U4 `u4-platform` | U2 `u2-money-service` | Asynchronous `UserConfirmed` event on the shared event bus, AsyncAPI 3.0 | U4 / `Raad` owns the event; U2 owns its consumer |
| C3 | U4 `u4-platform` (configures the external sign-in service) | U3 `u3-mobile-app`; U2 consumes the verified token claims through C5 | Sign-in SDK behavior profile and token-claim contract | U4 / `Raad` |
| C4 | U4 `u4-platform` | U3 `u3-mobile-app` | Versioned, non-secret build-time mobile environment configuration | U4 / `Raad` owns the schema; each environment supplies its values |
| C5 | U4 `u4-platform` | U2 `u2-money-service` | HTTPS edge forwarding plus a non-secret JWT-verifier configuration | U4 owns routing/edge responses and publishes verifier configuration; U2 owns defense-in-depth token verification |

The account-confirmed event in C2 is a narrow exception to Domain Design ADR-005. No transfer-completed event is published in the MVP. C2 and C5 pin U4-to-U2 boundaries that the Units Generation review found even though the approved unit graph leaves U2 and U4 independent. Contract tests must therefore run in both units, and U3's end-to-end tests remain the integration check across them.

---

## C1 — RAAD Money API v1

### Purpose and boundary

C1 is the only public API for wallet data and money movement. MobileApp calls it through the shared public API address. The `/money` mapping sends `/money/v1` to MoneyApi. Later services may consume an approved operation through the same contract; they never read the Ledger or WalletDirectory stores directly.

The API description is owned in `RaadMoneyService` at `openapi/raad-money-v1.yaml`. U1 commits the v1 description and builds the walking-skeleton operations against it. U2 completes the behavior behind it. `RaadMobile` pins an exact released revision, as Contract Files, Releases and Pinning describes, and generates its Dart client from the pinned copy in CI (Q3 A). Handwritten request and response models in `RaadMobile` are not allowed.

### OpenAPI specification

```yaml
openapi: 3.1.0
info:
  title: RAAD Money API
  version: 1.0.0
  description: >
    Wallet balance, recipient resolution, wallet-to-wallet transfer and transfer
    history for the RAAD MVP. Every amount is a whole number of halalas and the
    only currency is SAR.
servers:
  - url: https://{apiHost}/money/v1
    variables:
      apiHost:
        default: api.dev.raad.example
        description: Environment-specific API host supplied by C4.
security:
  - bearerAuth: []
paths:
  /wallet:
    put:
      operationId: ensureWallet
      summary: Open the caller's wallet if absent, or return the existing wallet.
      description: >
        The safety-net path for wallet setup. Safe under retries and simultaneous
        calls: one wallet exists per caller and the 100000-halalah opening balance
        is credited once. The caller is taken only from the verified access token.
      responses:
        '200':
          description: The existing wallet.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Wallet'
        '201':
          description: A wallet was opened with the starting balance.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Wallet'
        '401':
          $ref: '#/components/responses/AuthenticationRequired'
        '403':
          $ref: '#/components/responses/Forbidden'
        '409':
          description: The user's verified email is already held by another wallet holder.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
        '503':
          $ref: '#/components/responses/Unavailable'
    get:
      operationId: getWallet
      summary: Read the caller's wallet balance.
      responses:
        '200':
          description: The caller's wallet.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Wallet'
        '401':
          $ref: '#/components/responses/AuthenticationRequired'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          description: The caller has no wallet; the app should call PUT /wallet.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
        '503':
          $ref: '#/components/responses/Unavailable'
  /recipients/resolve:
    post:
      operationId: resolveRecipient
      summary: Resolve one complete email address for the transfer review screen.
      description: >
        POST keeps the email address out of the URL and normal access logs. This is
        an exact lookup only: no partial matching, list or search. It counts toward
        the same per-user recipient-lookup limit as POST /transfers, so sending to
        an unknown address cannot bypass the limit.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ResolveRecipientRequest'
      responses:
        '200':
          description: One recipient for the review screen.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Recipient'
        '400':
          $ref: '#/components/responses/ValidationError'
        '401':
          $ref: '#/components/responses/AuthenticationRequired'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/RecipientNotFound'
        '409':
          description: The email belongs to the caller; a transfer to oneself is not allowed.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
        '503':
          $ref: '#/components/responses/Unavailable'
  /transfers:
    post:
      operationId: createTransfer
      summary: Transfer simulated SAR from the caller's wallet to another RAAD wallet.
      parameters:
        - $ref: '#/components/parameters/IdempotencyKey'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTransferRequest'
      responses:
        '201':
          description: The transfer completed. Replayed completed requests return this same body.
          headers:
            Idempotency-Replayed:
              $ref: '#/components/headers/IdempotencyReplayed'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TransferResult'
        '400':
          $ref: '#/components/responses/ValidationError'
        '401':
          $ref: '#/components/responses/AuthenticationRequired'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          description: >
            RECIPIENT_NOT_FOUND: no recipient has the normalized email address. It
            is a persisted first business outcome for this caller and idempotency
            key. WALLET_NOT_FOUND: the caller has no wallet yet. Nothing is
            persisted against the key and Idempotency-Replayed is omitted, so the
            app calls PUT /wallet and may then send the same request with the
            same key.
          headers:
            Idempotency-Replayed:
              $ref: '#/components/headers/IdempotencyReplayed'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '409':
          description: >
            SELF_TRANSFER is a persisted first business outcome. IDEMPOTENCY_KEY_REUSED
            means this caller already used the key with a different normalized recipient
            or amount; it never replaces the first outcome.
          headers:
            Idempotency-Replayed:
              $ref: '#/components/headers/IdempotencyReplayed'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '422':
          description: >
            A persisted first business refusal: AMOUNT_OUT_OF_RANGE or
            INSUFFICIENT_FUNDS.
          headers:
            Idempotency-Replayed:
              $ref: '#/components/headers/IdempotencyReplayed'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
        '503':
          $ref: '#/components/responses/Unavailable'
    get:
      operationId: listTransfers
      summary: Read one stable page of the caller's completed sent and received transfers.
      parameters:
        - name: cursor
          in: query
          required: false
          description: Opaque nextCursor returned by the preceding page. The app never parses or changes it.
          schema:
            type: string
            minLength: 1
            maxLength: 2048
        - name: limit
          in: query
          required: false
          description: >
            Page size; defaults to 20 and cannot exceed 100. A request that sends
            a cursor must use the same page size as the request that started that
            cursor's chain.
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        '200':
          description: A stable page, newest first with a fixed tiebreaker.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TransferPage'
        '400':
          description: Invalid or expired cursor; code CURSOR_INVALID_OR_EXPIRED tells the app to reload the first page.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          $ref: '#/components/responses/AuthenticationRequired'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          description: The caller has no wallet (WALLET_NOT_FOUND); the app should call PUT /wallet.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '429':
          $ref: '#/components/responses/RateLimited'
        '500':
          $ref: '#/components/responses/InternalError'
        '503':
          $ref: '#/components/responses/Unavailable'
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: Access token from the environment's shared sign-in service (C3).
  parameters:
    IdempotencyKey:
      name: Idempotency-Key
      in: header
      required: true
      description: >
        Opaque key generated by MobileApp for one transfer intent. It is scoped to
        the verified caller. Reuse with identical recipientEmail and amountHalalas
        returns the first completed or refused outcome; reuse with different details
        returns IDEMPOTENCY_KEY_REUSED.
      schema:
        type: string
        minLength: 16
        maxLength: 128
        pattern: '^[A-Za-z0-9._~-]+$'
  headers:
    IdempotencyReplayed:
      description: >
        Sent only on a response that reports a persisted outcome or a key
        conflict. false on the first response for a persisted outcome and on
        IDEMPOTENCY_KEY_REUSED; true when this response replays the persisted
        first outcome of an earlier request with this caller and key. Omitted on
        every response that persists nothing (400, 401, 403, WALLET_NOT_FOUND,
        429, 500 and 503).
      schema:
        type: boolean
  schemas:
    Wallet:
      type: object
      additionalProperties: true
      required: [balance]
      properties:
        balance:
          $ref: '#/components/schemas/Money'
    Money:
      type: object
      additionalProperties: true
      required: [amountHalalas, currency]
      properties:
        amountHalalas:
          type: integer
          format: int64
          minimum: 0
          description: Whole halalas; never a decimal or floating-point number.
        currency:
          type: string
          const: SAR
    ResolveRecipientRequest:
      type: object
      additionalProperties: false
      required: [email]
      properties:
        email:
          type: string
          maxLength: 512
          description: >
            Raw user input. MoneyApi trims surrounding Unicode whitespace,
            normalizes to NFC, lowercases for comparison, then validates the
            normalized complete address (maximum 254 characters).
          x-normalization: trim-unicode-whitespace+nfc+lowercase-before-validation
    Recipient:
      type: object
      additionalProperties: true
      required: [displayName, email]
      properties:
        displayName:
          type: string
          minLength: 1
          maxLength: 200
        email:
          type: string
          format: email
          maxLength: 254
    CreateTransferRequest:
      type: object
      additionalProperties: false
      required: [recipientEmail, amountHalalas]
      properties:
        recipientEmail:
          type: string
          maxLength: 512
          description: >
            Raw user input. MoneyApi trims surrounding Unicode whitespace,
            normalizes to NFC, lowercases for lookup, self-transfer comparison
            and the idempotency fingerprint, then validates the normalized
            complete address (maximum 254 characters).
          x-normalization: trim-unicode-whitespace+nfc+lowercase-before-validation
        amountHalalas:
          type: integer
          format: int64
          description: >
            Whole halalas. Schema validation accepts any int64 so the Ledger can
            persist AMOUNT_OUT_OF_RANGE as the first idempotent business outcome;
            the allowed business range is 100 through 50000 inclusive.
    TransferResult:
      type: object
      additionalProperties: true
      required: [transferId, reference, recipient, amount, completedAt, balanceAfter]
      properties:
        transferId:
          type: string
          format: uuid
        reference:
          type: string
          minLength: 1
          maxLength: 64
        recipient:
          $ref: '#/components/schemas/Recipient'
        amount:
          $ref: '#/components/schemas/Money'
        completedAt:
          type: string
          format: date-time
          description: UTC instant with an offset.
        balanceAfter:
          $ref: '#/components/schemas/Money'
    TransferListItem:
      type: object
      additionalProperties: true
      required: [transferId, reference, direction, otherParty, amount, completedAt]
      properties:
        transferId:
          type: string
          format: uuid
        reference:
          type: string
          minLength: 1
          maxLength: 64
        direction:
          type: string
          enum: [sent, received]
        otherParty:
          $ref: '#/components/schemas/Recipient'
        amount:
          $ref: '#/components/schemas/Money'
        completedAt:
          type: string
          format: date-time
    TransferPage:
      type: object
      additionalProperties: true
      required: [items, nextCursor]
      properties:
        items:
          type: array
          maxItems: 100
          items:
            $ref: '#/components/schemas/TransferListItem'
        nextCursor:
          type: [string, 'null']
          maxLength: 2048
          description: >
            Opaque cursor for the next page. Non-null exactly when another page
            exists and null at the end. It expires 24 hours after the first page
            of its chain was issued.
    FieldError:
      type: object
      additionalProperties: true
      required: [field, code]
      properties:
        field:
          type: string
        code:
          type: string
        message:
          type: string
    Error:
      type: object
      additionalProperties: true
      required: [code, message, correlationId]
      properties:
        code:
          type: string
          enum:
            - VALIDATION_ERROR
            - AUTHENTICATION_REQUIRED
            - FORBIDDEN
            - WALLET_NOT_FOUND
            - RECIPIENT_NOT_FOUND
            - SELF_TRANSFER
            - AMOUNT_OUT_OF_RANGE
            - INSUFFICIENT_FUNDS
            - IDEMPOTENCY_KEY_REUSED
            - CURSOR_INVALID_OR_EXPIRED
            - RATE_LIMITED
            - INTERNAL_ERROR
            - SERVICE_UNAVAILABLE
            - TOKEN_VERIFIER_UNAVAILABLE
        message:
          type: string
          description: Safe fallback message with no personal or internal detail. The app branches on code, not this text.
        correlationId:
          type: string
          minLength: 1
          maxLength: 128
        fieldErrors:
          type: array
          items:
            $ref: '#/components/schemas/FieldError'
  responses:
    ValidationError:
      description: The request shape or a field is invalid.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    AuthenticationRequired:
      description: The token is missing, invalid or expired. The response reveals no wallet data.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Forbidden:
      description: >
        The public API edge refused the request under a firewall rule (C5), code
        FORBIDDEN. The response reveals no wallet data and nothing about the rule.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    RecipientNotFound:
      description: No RAAD wallet holder has this complete normalized email address.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    RateLimited:
      description: The per-verified-user or endpoint limit was reached.
      headers:
        Retry-After:
          description: Whole seconds until the client may retry.
          schema:
            type: integer
            minimum: 1
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    InternalError:
      description: Unexpected failure; no stack trace or internal name is returned.
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    Unavailable:
      description: A required store or service is unavailable.
      headers:
        Retry-After:
          description: Whole seconds until a read may be retried.
          schema:
            type: integer
            minimum: 1
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

### Caller identity and authorization

The app sends `Authorization: Bearer <access token>` (Q7 A). C5 governs the U4 edge and U2 verification layers: both verify signature, issuer, audience binding, expiry, token type and the pinned asymmetric algorithm against the environment's verifier configuration, including key rotation and discovery failure. The edge forwards the access token unchanged and strips caller-supplied identity headers. MoneyApi takes the user ID only from the independently verified token's `sub`. No request contains a caller user ID or a source wallet ID. MoneyApi uses that `sub` for wallet setup, wallet reads, transfers, history and the idempotency-key scope. For wallet setup it takes the email address and display name from the source that the verifier configuration names (C3 check P2), never from a request body. A token, issuer, audience or key configuration from `dev` cannot authorize `stg` or `prd`. Every edge- or service-generated response carries the same `X-Correlation-Id`; every error body follows the C1 `Error` schema.

### Error and retry behavior

- Every error body follows `Error`. The Dart app branches on `code` and displays its own Arabic or English text; `message` is only a safe fallback.
- The app's request timeout is 15 seconds. The service target remains NFR6: 95% of transfers answer within 2 seconds at 10 concurrent users.
- The app may retry `PUT /wallet`, `GET /wallet`, `POST /recipients/resolve` and `GET /transfers` once after a timeout, 500 or 503. It respects `Retry-After` on 429 and 503.
- It never automatically retries validation, authentication, authorization, recipient, self-transfer, amount, low-balance, idempotency-conflict or cursor errors.
- A transfer is retried only after the user chooses **Try again**, with the same locked recipient, amount and `Idempotency-Key` (Q6 A). A key with different normalized recipient or amount returns 409 / `IDEMPOTENCY_KEY_REUSED` and never changes the first outcome.
- Requests are strict: an unknown request field is refused. Provider emission is checked against the documented response fields, but consumers tolerate and ignore unknown response fields as described under Compatibility behavior.

### Transfer idempotency matrix

MoneyApi processes `POST /transfers` in this order: verify C5 identity and rate limits; parse the header and body; normalize the recipient email; find the caller's wallet; build a fingerprint from contract major version `1`, the normalized recipient email and `amountHalalas`; then conditionally create the first `TransferRequest` for the unique pair `(verified sub, Idempotency-Key)`. The client-supplied key is opaque and never used without the verified `sub`. Only a one-way digest of the fingerprint is kept with the request, so the Ledger still holds no email address (ADR-002).

When a new request breaks more than one business rule, the first rule in this order decides the one outcome that is persisted: unknown recipient, amount out of range, own wallet, balance too low. This is the order in which `components.md` has MoneyApi find the recipient and the Ledger then apply its rules.

The first business outcome and its fingerprint remain for the lifetime of the environment in this MVP. A key is never made available for another transfer. If a later retention policy erases the owning account and its transfer data, it may erase the key with that data; no active app session may retain it afterward.

| First attempt or repeat | Key reserved or outcome persisted? | HTTP and code | Repeat with identical fingerprint | `Idempotency-Replayed` |
|---|---|---|---|---|
| Malformed JSON, missing/unknown field, invalid key syntax, non-integer amount or email invalid after normalization | No | 400 `VALIDATION_ERROR` | Evaluated as a new attempt after the request is corrected | Header omitted |
| Missing, invalid, expired, wrong-environment or wrong-type token; authorization refusal | No | 401 `AUTHENTICATION_REQUIRED` or 403 `FORBIDDEN` | Evaluated again | Header omitted |
| Rate limit reached | No | 429 `RATE_LIMITED` | Evaluated again after `Retry-After` | Header omitted |
| Caller has no wallet yet | No | 404 `WALLET_NOT_FOUND` | Evaluated again after `PUT /wallet` succeeds; the same key may be used | Header omitted |
| No recipient has the normalized email | Yes, as a final refused outcome | 404 `RECIPIENT_NOT_FOUND` | Same status, code and business result; a fresh request correlation ID | `true` on repeat, `false` first |
| Recipient is the caller | Yes, as a final refused outcome | 409 `SELF_TRANSFER` | Same status, code and business result; a fresh request correlation ID | `true` on repeat, `false` first |
| Amount is below 100 or above 50,000 halalas | Yes, as a final refused outcome | 422 `AMOUNT_OUT_OF_RANGE` | Same status, code and business result; a fresh request correlation ID | `true` on repeat, `false` first |
| Balance is too low | Yes, as a final refused outcome | 422 `INSUFFICIENT_FUNDS` | Same status, code and business result even if money arrives later; a fresh request correlation ID | `true` on repeat, `false` first |
| Transfer completed | Yes, in the same all-or-nothing change as both balances and the Transfer | 201 with `TransferResult` | Same transfer ID, reference, amount, recipient, completion time and resulting balance; a fresh request correlation ID | `true` on repeat, `false` first |
| Same `(sub, key)` already exists with a different fingerprint | No new outcome; original remains unchanged | 409 `IDEMPOTENCY_KEY_REUSED` | Not applicable | `false` |
| Store or service fails before the all-or-nothing outcome commits | No | 500 `INTERNAL_ERROR`, 503 `SERVICE_UNAVAILABLE`, or no response | May execute when the person retries; no money moved on the failed attempt | Header omitted |
| Outcome commits but the response is lost | Already final | The first caller may receive no response | Retry returns the persisted business outcome as above | `true` on retry |

For two simultaneous requests with the same `(sub, key)` and fingerprint, one conditional operation creates the outcome. The other waits for that atomic operation to resolve, then reads and returns that same final business outcome. No externally visible `pending` outcome exists. If the store fails before either commits, neither reserves the key or changes a balance and both may receive a transient failure. Two simultaneous requests with one key and different fingerprints result in one first outcome and one 409 `IDEMPOTENCY_KEY_REUSED`; which fingerprint wins is not promised, so the app must never do this.

`AMOUNT_OUT_OF_RANGE` is a Ledger business refusal, not schema validation: the OpenAPI request accepts any int64 and the Ledger applies the 100–50,000 range, so an out-of-range amount always answers 422 and never 400. `WALLET_NOT_FOUND`, if the safety-net `PUT /wallet` has not completed, is not persisted against the transfer key; the app ensures the wallet and may then retry with the same key.

### Compatibility behavior

- Request schemas are closed (`additionalProperties: false`) and provider request validation runs after the normalization described below.
- Response schemas and the C2 event payload are open to unknown fields for consumers. U2 and U4 provider-emission tests separately refuse undeclared output fields unless the field has first been added to the current owned contract.
- Generated C1 clients must deserialize a response containing an unknown optional field and continue using all known fields. The C2 consumer must do the same for an event. These are compatibility tests in U3 and U2 respectively.
- Removing, renaming or changing a field, making an optional field required, or adding an enum value when a consumer lacks an unknown-value fallback remains breaking and requires a new major version.
- `Error.code` is the one enum that may grow within v1. The generated client maps a code it does not know to an `unknown` fallback, and MobileApp then handles the response by its HTTP status and shows its generic failure message. Adding a value to any other enum (`direction`, `currency`, `environment`) is breaking.
- C2 consumers accept every `specVersion` whose major version is 1.
- C4 and the C5 verifier configuration are closed on purpose: a build or a service start must fail on a missing, extra or cross-environment value. Every added, removed or changed key in either is therefore a new `configVersion`, and U4 supplies a new version to an environment only after the consumer's release for that environment accepts it.

### Email normalization

For `ResolveRecipientRequest.email` and `CreateTransferRequest.recipientEmail`, MoneyApi performs these steps before email-format validation, lookup, self-transfer comparison or idempotency fingerprinting: remove leading and trailing Unicode whitespace; normalize Unicode to NFC; lowercase the complete address with locale-independent Unicode lowercasing; then validate the normalized complete address. The normalized value must be at most 254 characters. WalletDirectory uses this same value as `emailKey`. MobileApp performs the same trim and lowercase for early feedback, but server correctness never depends on the client doing it. The confirmed display spelling from WalletDirectory is returned in `Recipient.email`. U2's provider tests cover surrounding spaces, capitals, and composed against decomposed characters for the lookup, the own-wallet comparison and the idempotency fingerprint (AC3.5.3).

### Pagination stability

`GET /transfers` returns 20 entries by default and at most 100 (Q5 A). Every response includes `nextCursor`: it is non-null exactly when another page exists and `null` at the end. The first page fixes a snapshot boundary and an expiry 24 hours after that first page was issued. Every cursor in that chain carries the same expiry and is bound cryptographically to the verified `sub`, environment, page size, sort order (`completedAt` descending, then `transferId` descending), snapshot boundary and last returned sort key. The app cannot change any bound value and never parses the cursor. Transfers completed after the first page was issued do not shift or repeat entries in its later pages. An invalid, altered, expired, wrong-user, wrong-environment or wrong-page-size cursor returns `CURSOR_INVALID_OR_EXPIRED`, and the app reloads page one.

---

## C2 — UserConfirmed event v1

### Purpose and boundary

When an account is confirmed, U4 publishes this event to the shared event bus. U2 consumes it and runs the same idempotent wallet-setup procedure as `PUT /wallet`. Delivery never delays or fails account confirmation. If the money service is absent or fails, the event is retried and the public `PUT /wallet` safety net still completes setup at first sign-in (ADR-003).

This event is the only event in the MVP. It is not a transfer event and does not give later services access to money data.

### AsyncAPI specification

```yaml
asyncapi: 3.0.0
info:
  title: RAAD Identity Events
  version: 1.0.0
  description: Account lifecycle facts emitted by the shared sign-in platform.
defaultContentType: application/json
channels:
  userConfirmedV1:
    address: raad.identity.user-confirmed.v1
    messages:
      UserConfirmed:
        $ref: '#/components/messages/UserConfirmed'
operations:
  sendUserConfirmed:
    action: send
    channel:
      $ref: '#/channels/userConfirmedV1'
    summary: U4 publishes after the sign-in service confirms an account.
    messages:
      - $ref: '#/channels/userConfirmedV1/messages/UserConfirmed'
  receiveUserConfirmed:
    action: receive
    channel:
      $ref: '#/channels/userConfirmedV1'
    summary: U2 opens or returns the user's wallet, then registers the holder.
    messages:
      - $ref: '#/channels/userConfirmedV1/messages/UserConfirmed'
components:
  messages:
    UserConfirmed:
      name: UserConfirmed
      title: A user account was confirmed in one RAAD environment.
      correlationId:
        location: $message.payload#/eventId
      payload:
        $ref: '#/components/schemas/UserConfirmedPayload'
  schemas:
    UserConfirmedPayload:
      type: object
      additionalProperties: true
      required:
        - specVersion
        - eventId
        - occurredAt
        - environment
        - userId
        - email
        - displayName
      properties:
        specVersion:
          type: string
          pattern: '^1\.[0-9]+$'
          description: >
            Major version 1 with any minor version. U4 emits the minor version of
            its released contract. A consumer accepts every 1.x and ignores the
            fields it does not know.
        eventId:
          type: string
          format: uuid
        occurredAt:
          type: string
          format: date-time
          description: UTC instant with an offset.
        environment:
          type: string
          enum: [dev, stg, prd]
        userId:
          type: string
          minLength: 1
          maxLength: 128
          description: Opaque subject identifier from that environment's sign-in service.
        email:
          type: string
          format: email
          maxLength: 254
          description: Confirmed email address; personal data, never written to logs.
        displayName:
          type: string
          minLength: 1
          maxLength: 200
          description: Personal data, never written to logs.
```

### Delivery, failure and security behavior

- Delivery is at least once after the event bus accepts an event. U2 treats both `eventId` and `userId` idempotently: duplicate and simultaneous deliveries produce one wallet and one holder, and credit 100,000 halalas once.
- Account confirmation succeeds independently of event publication. After confirmation, U4 attempts to publish asynchronously. A failure before the bus accepts the event is explicitly permitted event loss: U4 records a non-personal metric and event ID, never rolls confirmation back, and never tells the user confirmation failed. The public `PUT /wallet` safety net is authoritative and opens the wallet at first sign-in. U4 tests this exact failure path end to end. Once the bus accepts the event, the 24-hour delivery and dead-letter guarantee below applies.
- The event bus retries accepted events with bounded backoff for 24 hours. After the retry window, it moves the event to a dead-letter destination and raises the wallet-setup alarm. Exact retry intervals and the AWS resources are chosen in Infrastructure Design; the 24-hour window starts when the bus accepts the event.
- U4's producer-emission test permits only fields declared by its current owned C2 contract. U2's consumer accepts and ignores unknown fields so an optional field can be added safely; its compatibility test proves this behavior.
- U2 consumes only from the same environment's channel and checks `environment` against its own immutable environment setting. A `dev` event cannot open a `stg` or `prd` wallet.
- The event bus policy permits only the same environment's sign-in integration to publish and only the same environment's U2 consumer to receive.
- The event is encrypted in transit and at rest. Logs contain `eventId`, environment and an opaque hash or the final characters of `userId`; they never contain email, display name, token or the full user ID.
- An invalid payload is not retried forever. It goes to the dead-letter destination immediately and raises the same alarm with the event ID only.

---

## C3 — Sign-in client behavior profile v1

### Purpose and boundary

MobileApp calls the shared sign-in service directly for account actions (ADR-007). U4 owns its configuration and this behavior profile. It is not a second RAAD REST API and contains no service-specific SDK names; Infrastructure Design maps these operations to the chosen AWS sign-in service.

### Behavior specification

```yaml
contract: raad-sign-in-client-profile
version: '1.0'
owner: u4-platform
consumer: u3-mobile-app
transport: provider SDK over TLS
email_normalization:
  client_before_send:
    - remove surrounding Unicode whitespace
    - lowercase for comparison
  provider:
    uniqueness: one account per normalized email
    preserves_for_display: confirmed email
  mutable_after_signup:
    email: false
    displayName: false
operations:
  signUp:
    input: [email, displayName, password]
    success: unconfirmed account and one emailed confirmation code
    expected_failures: [EMAIL_IN_USE, PASSWORD_RULE_FAILED, RATE_LIMITED]
  confirmEmail:
    input: [email, confirmationCode]
    success: >
      Confirmed account. Event publication is asynchronous and is not part of
      this client-visible success; pre-acceptance event loss is permitted and
      PUT /wallet remains the authoritative safety net as C2 specifies.
    expected_failures: [CODE_INVALID_OR_EXPIRED, RATE_LIMITED]
  resendConfirmationCode:
    input: [email]
    success: generic acknowledgement; a new code replaces every earlier code
    privacy_rule: >
      Every outcome except rate limiting is presented by MobileApp as "We sent a
      new code", whether the address is unknown, already confirmed or unconfirmed.
    expected_failures: [RATE_LIMITED]
  signIn:
    input: [email, password]
    success: access token and refresh token
    privacy_rule: >
      Wrong password, unknown email and unconfirmed account produce one client-visible
      code SIGN_IN_FAILED and the same message. The provider may retain a private reason
      for security monitoring, without email or password in logs.
    expected_failures: [SIGN_IN_FAILED, RATE_LIMITED]
  refreshSession:
    input: [refreshToken]
    success: new access token without showing sign-in
    session_policy:
      access_token_lifetime_minutes: 60
      refresh_allowed_until_idle_days: 30
      idle_rule_enforced_by: the provider when it has an idle limit; otherwise MobileApp (check P9)
    expected_failures: [SESSION_EXPIRED]
  requestPasswordReset:
    input: [email]
    success: generic acknowledgement
    privacy_rule: >
      MobileApp always displays "If an account exists for this address, we sent
      a code", whether or not an account exists.
    expected_failures: [RATE_LIMITED]
  confirmPasswordReset:
    input: [email, resetCode, newPassword]
    success: password changed; old password no longer works
    expected_failures: [CODE_INVALID_OR_EXPIRED, PASSWORD_RULE_FAILED, RATE_LIMITED]
  signOut:
    input: [refreshToken]
    success: local tokens removed and refresh token revoked when supported
password_rule:
  minimum_characters: 8
  requires_latin_lowercase: true
  requires_latin_uppercase: true
  requires_digit: true
stored_user_attributes: [email, displayName]
access_token:
  required_claims: [sub, iss, audience_binding, exp, iat, token_type_marker]
  claim_rules:
    sub: immutable opaque user identifier within one environment
    iss: unique issuer for one environment
    audience_binding: >
      The claim that names the mobile app client of one environment: aud, or
      client_id when the provider's access tokens carry no aud. C5's verifier
      configuration names which one applies.
    token_type_marker: >
      The provider's mark that the token is an access token and not an ID or
      refresh token. C5's verifier configuration names it and its expected value.
  profile_attributes:
    email: confirmed address used by the C1 wallet-setup safety net
    displayName: display name used by the C1 wallet-setup safety net
    source: >
      Claims in the access token when the provider can put them there; otherwise
      the provider's own-profile call, made by MoneyApi with the caller's access
      token. C5's verifier configuration says which source an environment uses.
      They never come from a request body or from an ID token sent by the app.
privacy:
  never_log: [password, confirmationCode, resetCode, accessToken, refreshToken, email, displayName]
  generic_client_errors:
    - SIGN_IN_FAILED
    - confirmation resend acknowledgement
    - password reset request acknowledgement
```

### Failure and abuse behavior

- MobileApp branches on the stable client code, not provider-specific text. It owns the Arabic and English messages in `interaction-spec.md`.
- Sign-up is the one account-enumerating operation allowed by FR1.6: it may return `EMAIL_IN_USE`. Sign-in, resend and password-reset request do not reveal whether an account exists.
- U4 applies per-caller limits to sign-up, confirmation, resend, sign-in and password-reset operations, with the provider's own limits or with the fallback in check P10. These direct account calls do not pass through the public API edge; NFR12 and AC1.3.5 depend on these limits.
- MobileApp never sends passwords or codes to C1. It sends C1 only the access token, in the `Authorization` header. Access and refresh tokens are held only in phone secure storage.

### Provider capability acceptance

The choice of sign-in provider stays with Infrastructure Design. Whichever provider is chosen must pass every check below on `dev`. U1's Infrastructure Design runs the checks the walking skeleton relies on (P1, P2 and P13). U4's runs the rest before U3 builds the account screens. A check that fails takes the fallback in its row, and the unit named there owns it. A fallback that would change a requirement or an acceptance criterion goes back to the person first.

| # | Guarantee in this profile | Acceptance check on `dev` | If the provider cannot do it | Fallback owner |
|---|---|---|---|---|
| P1 | The access token carries `sub`, the issuer, an audience binding and a token-type marker | Decode an access token and find the claims that C5's verifier configuration names; two sign-ins by one user give the same `sub` | The configuration names whichever claim the provider uses (`aud` or `client_id`, and its own token-type marker). A provider with no audience binding or no token-type marker is not used | U4 |
| P2 | MoneyApi gets the confirmed email address and display name from the verified sign-in | The access token holds `email` and `displayName` equal to the confirmed account's values | U4 adds both to the access token with the provider's token-customization hook. With no such hook, the verifier configuration sets `profileAttributeSource` to `user-profile-endpoint`, and MoneyApi reads both once at wallet setup with the caller's own access token and checks that the profile's subject equals `sub` | U4 for the hook and the configuration; U2 for the own-profile call |
| P3 | One account per normalized email address (FR1.6) | Sign up `a@x.com`, then `A@x.com` with a trailing space: the second gets `EMAIL_IN_USE` | MobileApp already trims and lowercases before every account call. U4 adds a check in the platform, before sign-up completes, that refuses an address differing only in capitals | U3 for the client rule; U4 for the check |
| P4 | The password rule of A4, at sign-up and at reset | A4's five sample passwords give A4's results | U4 brings the difference to the person as a change to A4 before U3 builds the sign-up screen | U4 |
| P5 | Only the email address and display name are stored about a user (AC1.1.4) | List a `dev` account's attributes | U4 requests and fills no other attribute. Identifiers, timestamps and status that the provider creates by itself are not data collected from the user | U4 |
| P6 | Wrong password, unknown email and unconfirmed account give one refusal (AC1.3.2, AC1.3.3) | Try the three cases and compare what the app receives | U4 turns on the provider's setting that hides whether an account exists, where it has one. U3's sign-in adapter maps every provider refusal except a rate limit to `SIGN_IN_FAILED` and one message. U4 reports any difference still visible on the network to the person before `stg` | U3 for the adapter; U4 for the setting and the report |
| P7 | A resent code replaces every earlier code, and the answer is the same for any address (AC1.2.6) | Ask for two codes: the first is refused and the second works. Ask for a resend for an unknown and for a confirmed address | U3's adapter shows the one acknowledgement for every outcome except a rate limit. If an earlier code stays valid, U4 adds its own confirmation step in the platform that cancels earlier codes, or returns AC1.2.6 to the person before U3 builds the confirmation screen. The app never works around it | U4; U3 for the message |
| P8 | A password-reset request gives one acknowledgement for any address | Ask for a reset for a known and for an unknown address | U3's adapter shows the one acknowledgement for every outcome except a rate limit | U3 |
| P9 | An access token lasts 60 minutes, and renewal is refused after 30 days without use (A5) | Read both settings, and run A5's test-clock check where the provider allows one | If the provider has only a fixed renewal lifetime counted from sign-in, U4 sets it to at least 30 days (the value is chosen in Infrastructure Design). MobileApp keeps the time of last use in secure storage and, after more than 30 days without use, signs out and shows sign-in. An active user then signs in again only when the fixed lifetime ends | U3 for the idle rule; U4 for the lifetime |
| P10 | Per-caller limits on account operations (AC1.3.5, NFR12) | Send a burst of sign-in attempts from one caller: further attempts are refused and a second caller is unaffected | U4 attaches the platform firewall's per-caller rate rule to the sign-in service's endpoint where the provider allows it. If neither can separate callers, U4 returns AC1.3.5 to the person before `stg` | U4 |
| P11 | Every code under `expected_failures` is a stable client code | Produce each code once and list the provider error behind it | U3's adapter owns the mapping and turns any unlisted provider error into its generic failure, never into provider text | U3 |
| P12 | Confirming an account can publish the C2 event with the email address and display name | Confirm a `dev` account and observe one C2 event | None is needed: with no hook after confirmation, no event is published and `PUT /wallet` opens every wallet, as C2 permits | U4 |
| P13 | Signing keys are published over HTTPS and tokens are signed with RS256 | `jwksUri` answers, and the token header names RS256 | None: a provider without public key discovery, or with shared-secret signing only, is not used | U4 |

---

## C4 — Mobile environment configuration v1

### Purpose and boundary

Each mobile build is tied to exactly one environment and may call only that environment's API and sign-in service (AC6.2.2). U4 owns this non-secret schema. Infrastructure outputs supply the values. U3 consumes an immutable file at build time; missing, extra or cross-environment values fail the build rather than falling back.

### Shared schema

```yaml
shared-schema: raad-mobile-environment-config
version: '1.0'
owner: u4-platform
consumer: u3-mobile-app
secrets_allowed: false
schema:
  type: object
  additionalProperties: false
  required:
    - configVersion
    - environment
    - apiBaseUrl
    - moneyBasePath
    - authIssuer
    - authAudience
    - authClientId
  properties:
    configVersion:
      type: string
      const: '1.0'
    environment:
      type: string
      enum: [dev, stg, prd]
    apiBaseUrl:
      type: string
      format: uri
      pattern: '^https://'
    moneyBasePath:
      type: string
      const: /money/v1
    authIssuer:
      type: string
      format: uri
      description: Must identify the same environment as environment and apiBaseUrl.
    authAudience:
      type: string
      minLength: 1
    authClientId:
      type: string
      minLength: 1
      description: Public application identifier, not a secret.
validation:
  - apiBaseUrl, authIssuer, authAudience and authClientId must all belong to environment
  - no key name may contain secret, password, token, privateKey or clientSecret
  - production builds accept only environment prd
  - development and staging builds show the matching DEV or STG chip; prd shows no chip
```

The environment values are deployment outputs, not committed secrets. Each pipeline supplies them to the build. U3 tests schema validation and refuses to build when a required value is missing or when environments disagree.

---

## C5 — Public API edge and token-verifier contract v1

### Purpose and boundary

U4 owns the public API edge, the `/money/v1` mapping, firewall and edge rate limits. U2 owns MoneyApi behind that edge. C5 defines exactly what the edge forwards, how both sides verify access tokens, and how an edge-generated error remains indistinguishable in shape from a MoneyApi error. It leaves the concrete gateway and key-discovery services to Infrastructure Design.

### Edge and verifier specification

```yaml
contract: raad-money-edge
version: '1.0'
owner: u4-platform
consumer: u2-money-service
public_route:
  path_prefix: /money/v1
  upstream_contract: C1
  tls_minimum: '1.2'
forwarding:
  preserve: [httpMethod, pathAfterPrefix, query, body]
  request_headers:
    forward: [Authorization, Idempotency-Key, Content-Type, Accept, X-Correlation-Id]
    strip:
      - X-User-Id
      - X-Wallet-Id
      - X-Authenticated-User
      - X-Forwarded-User
    authorization_token_type: access-token
    never_forward_token_types: [id-token, refresh-token]
  correlation_id:
    header: X-Correlation-Id
    accepted_pattern: '^[A-Za-z0-9._~-]{1,128}$'
    behavior: >
      Preserve a valid caller value; otherwise create one. Forward it to MoneyApi
      and return the same value in every response, including edge errors.
  response:
    preserve_status_and_body: true
    add_headers: [X-Correlation-Id]
token_verification:
  layers: [public-edge, MoneyApi]
  required_checks: [signature, issuer, audience-binding, expiry, not-before-if-present, token-type]
  required_token_type: access-token
  caller_id_claim: sub
  accepted_algorithms: [RS256]
  configuration:
    name: raad-token-verifier-config
    version: '1.0'
    delivery: immutable non-secret deployment configuration, one per environment
    secrets_allowed: false
    schema:
      type: object
      additionalProperties: false
      required:
        - configVersion
        - environment
        - issuer
        - audience
        - audienceClaim
        - tokenTypeMarker
        - jwksUri
        - acceptedAlgorithms
        - profileAttributeSource
      properties:
        configVersion:
          type: string
          const: '1.0'
        environment:
          type: string
          enum: [dev, stg, prd]
        issuer:
          type: string
          format: uri
          pattern: '^https://'
        audience:
          type: string
          minLength: 1
          description: >
            The value the access token's audience-binding claim must carry in
            this environment; equals C4 authAudience.
        audienceClaim:
          type: string
          enum: [aud, client_id]
          description: The access-token claim that must equal audience for this provider.
        tokenTypeMarker:
          type: object
          additionalProperties: false
          required: [location, name, expectedValue]
          properties:
            location:
              type: string
              enum: [claim, header]
            name:
              type: string
              minLength: 1
            expectedValue:
              type: string
              minLength: 1
        jwksUri:
          type: string
          format: uri
          pattern: '^https://'
        acceptedAlgorithms:
          type: array
          minItems: 1
          maxItems: 1
          items:
            type: string
            const: RS256
        profileAttributeSource:
          type: string
          enum: [access-token-claims, user-profile-endpoint]
          description: Where MoneyApi reads email and displayName at wallet setup (C3 check P2).
        userProfileUri:
          type: string
          format: uri
          pattern: '^https://'
          description: Present exactly when profileAttributeSource is user-profile-endpoint.
    validation:
      - issuer, audience, jwksUri and userProfileUri must all belong to environment
      - userProfileUri is present exactly when profileAttributeSource is user-profile-endpoint
      - every value is public information about the sign-in service; none is a secret
  key_discovery:
    transport: HTTPS
    source: jwksUri
    cache_maximum_minutes: 360
    unknown_kid_behavior: refresh-once-then-refuse
    unknown_kid_refresh_minimum_interval_seconds: 60
    rotation: >
      A verifier refreshes its key set once when a token names a key it does not
      hold, and at most once a minute, so a new key works without a restart.
      Where U4 controls rotation, the new and the retiring key overlap for at
      least the greater of the access-token lifetime and the verifier cache
      maximum. Where the provider rotates by itself, a token signed by a
      withdrawn key is refused with 401 and the app renews its session.
    discovery_failure: >
      Continue with an unexpired cached key set. With no usable cached key, return
      503 TOKEN_VERIFIER_UNAVAILABLE; never turn verifier unavailability into 401.
edge_errors:
  schema: C1 Error
  mappings:
    missing_invalid_or_expired_access_token:
      httpStatus: 401
      code: AUTHENTICATION_REQUIRED
    firewall_refusal:
      httpStatus: 403
      code: FORBIDDEN
    rate_limit:
      httpStatus: 429
      code: RATE_LIMITED
      requiredHeader: Retry-After
    token_key_discovery_unavailable:
      httpStatus: 503
      code: TOKEN_VERIFIER_UNAVAILABLE
  privacy: no token, email, wallet id, stack trace or internal route name in body or logs
failure_behavior:
  no_matching_route: return 404 outside C1; never forward
  upstream_unreachable: return C1 Error with 503 SERVICE_UNAVAILABLE and Retry-After
  upstream_timeout: return C1 Error with 503 SERVICE_UNAVAILABLE and Retry-After
```

U4 publishes one `raad-token-verifier-config` per environment, from the same deployment outputs that describe the sign-in service C3 profiles. The edge and U2 each load it. U2 refuses to start if a value is missing, if the configuration fails the schema, or if the issuer or audience belongs to a different environment. The edge forwards the original access token to MoneyApi; it never converts token claims into trusted identity headers. MoneyApi independently verifies the token and takes the caller only from `sub`.

### Edge tests

- U4 proves path and query forwarding, request-body preservation, allowed-header forwarding, spoofed identity-header stripping, correlation-ID creation/preservation, edge error shape, 401/403/429/503 mappings and `Retry-After`. It validates each environment's verifier configuration against the schema.
- U2 proves the issuer, audience-binding, algorithm, expiry, token-type and signature checks with the claim names the configuration gives; unknown-key refresh and its one-minute limit; overlapping-key rotation; cached-key behavior during discovery failure; refusal to start with a missing, invalid or cross-environment configuration; the configured profile-attribute source; and that no request field or forwarded identity header can replace `sub`.
- The joint test sends the same C1 request through the edge and directly to a test MoneyApi adapter and compares the C1 status/body, apart from headers that C5 owns. A token from each wrong environment is refused at both layers.

---

## Contract Files, Releases and Pinning

Each contract is one file in the repo of the unit that owns it. That file at a released tag is the contract; this document is its design record.

| Contract | Owning repo | Canonical file | Contract ID | Repos that pin it |
|---|---|---|---|---|
| C1 | `RaadMoneyService` | `openapi/raad-money-v1.yaml` | `c1-money-api` | `RaadMobile`; `Raad`, for the `Error` shape of edge responses |
| C2 | `Raad` | `contracts/c2-identity-events-v1.asyncapi.yaml` | `c2-identity-events` | `RaadMoneyService` |
| C3 | `Raad` | `contracts/c3-sign-in-client-profile-v1.yaml` | `c3-sign-in-profile` | `RaadMobile` |
| C4 | `Raad` | `contracts/c4-mobile-environment-config-v1.schema.yaml` | `c4-mobile-config` | `RaadMobile` |
| C5 | `Raad` | `contracts/c5-money-edge-v1.yaml` | `c5-money-edge` | `RaadMoneyService` |

The last column is the register of consumers. The owning repo's README repeats its rows, and a new consumer is added there by pull request.

### Release identity

- A release is an annotated git tag on a commit of the owning repo's `main`, named `contract/<contract ID>/v<MAJOR>.<MINOR>.<PATCH>`, for example `contract/c1-money-api/v1.0.0`.
- A pull request that changes a contract file raises the version inside the file: `info.version` for C1 and C2, `version` for C3 to C5. The markers that travel with data (`specVersion`, `configVersion`) carry `MAJOR.MINOR`. PATCH is for wording that changes no schema and no behavior, MINOR for a compatible addition, and MAJOR for a breaking change, which also gets a new file ending in `-v2` and a new path or address.
- After the merge, the owning repo's pipeline creates the tag for a version that has no tag yet and writes the SHA-256 of the file's bytes in the tag message. CI fails a change that alters a contract file but keeps a version that is already tagged.
- A tag is never moved or deleted. A tag rule enforces this where the GitHub plan allows one. Each consumer also records the commit the tag pointed to, so a moved tag shows at the next pin check.
- Until a contract's provider tests pass for the whole file, its releases carry a pre-release suffix such as `v1.0.0-rc.1`. U1 tags the first ones for the walking skeleton. `v1.0.0` of C1 is tagged when U2's provider tests pass, and `v1.0.0` of C2 to C5 when U4's do. A pre-release is pinned in the same way as a full release.

### Pinning in a consumer repo

- A consumer keeps `contracts/pins.yaml` with one entry per contract it uses: the contract ID, the owning repo, the tag, the commit the tag points to, and the file's SHA-256. It keeps a byte-for-byte copy of each pinned file under `contracts/pinned/`.
- Code generation, schema validation and contract tests read only the pinned copy, never a branch of the owning repo. On every run, CI recomputes each copy's SHA-256 and fails if it differs from `pins.yaml`. A build therefore needs no access to another repo.
- A pin changes only through a pull request in the consumer repo. A script in that repo takes a contract ID and a tag, fetches the file at that tag from the owning repo, checks its SHA-256 against the tag message, and rewrites the copy and the `pins.yaml` entry. The engineer runs it with their own GitHub access. The same pull request carries the regenerated client or the updated tests, and the other engineer reviews it.

### Compatibility baseline in the owning repo

- For a changed contract file, CI takes as the previous release the highest full-release tag with the same contract ID and the same major version, reads the file at that tag and compares the change with it. The pipeline fetches tags for this. Before the first full release there is no baseline, and the check passes.
- A difference that the rules below class as breaking fails the check unless the change is a new major version in a new file.

### Old major versions

- Each major version has its own file and its own series of tags, so the `-v1` file stays on `main` beside the `-v2` file.
- The provider keeps serving the old major version until no consumer's `pins.yaml` names it and both engineers approve its removal in a pull request to the owning repo. Removing the file from `main` leaves its tags in place.

## Contract Ownership and Change Rules

- **C1:** U2 owns `openapi/raad-money-v1.yaml`. U1 commits its first pre-release, and U2 owns every later change. U3 pins a released revision and generates its client from the pinned copy in CI.
- **C2:** U4 owns the `UserConfirmed` event name and payload. U2 owns its consumer behavior but cannot change the payload contract alone.
- **C3, C4 and C5:** U4 owns the sign-in behavior profile, both configuration schemas and the edge contract. U3 owns its client implementation and tests it against C3 and C4. U2 owns its token verifier and tests it against C5.
- An additive response field is safe only when optional and consumers ignore unknown fields. Removing or renaming a field, making an optional field required, changing its meaning or type, narrowing a numeric range, or adding an enum value without an unknown-value fallback is breaking.
- A breaking C1 change uses `/money/v2` and a new OpenAPI major version. A breaking C2 change uses a new event address such as `raad.identity.user-confirmed.v2`. A breaking C3, C4 or C5 change uses version `2.0` and coexists with v1 until its consumer migrates.
- A provider keeps the old major version until every registered consumer has migrated and both engineers approve its removal. A provider change and its compatibility report are reviewed in that provider repo's pull request.
- CI in the owning repo checks every changed contract file against its previous release, found as Contract Files, Releases and Pinning describes. Additive changes still require the owner's review; breaking changes require coordinated changes in provider and consumer repos.
- Consumers never rely on undocumented fields, transport metadata, ordering between unrelated events, or provider-specific error text.

## Contract Test Responsibilities

| Contract | Provider check | Consumer check | Integrated check |
|---|---|---|---|
| C1 | U2 validates every request and response against OpenAPI, refuses undeclared output fields, and tests every status and code that MoneyApi itself produces, every row of the transfer idempotency matrix, the refusal order and the email normalization cases; Ledger replay/concurrency tests remain behind it. The statuses the edge produces are U4's under C5 | U3 generates the Dart client from the pinned copy, runs client tests against an OpenAPI-based fake server, proves that an unknown response field and an unknown `Error.code` do not break it, and has no handwritten models | U1 proves balance/send/history on `dev`; U3 runs all later mobile integration tests against the real U2 service (Q2 B in Units Generation) |
| C2 | U4 validates emitted events against AsyncAPI, refuses undeclared fields, and tests that a publish failure before the bus accepts the event never fails confirmation | U2 validates events and tests duplicate, simultaneous, wrong-environment, malformed, unknown-field, later-minor-version and dead-letter cases | U3 confirms an account and observes exactly one wallet with 1,000.00 SAR; the safety-net test covers a lost event |
| C3 | U1 runs capability checks P1, P2 and P13 and U4 runs the rest on `dev`; each result and chosen fallback is recorded in that unit's Infrastructure Design | U3 tests each screen and its adapter's code mapping against a provider test environment, and the idle-session rule when check P9 assigns it | U3's account integration suite on `dev` |
| C4 | U4 validates each environment's generated configuration against the schema | U3 fails builds on missing, secret-looking or cross-environment values | Each environment's smoke test checks that the app calls only its matching API and issuer |
| C5 | U4 proves forwarding, identity-header stripping, correlation IDs, the edge error shape and the 401/403/429/503 mappings, and validates each environment's verifier configuration against the schema | U2 proves every verifier check, key refresh and rotation, discovery failure, refusal to start on a bad configuration, and the configured profile-attribute source | One C1 request sent through the edge and directly to a test MoneyApi gives the same status and body; a token from each wrong environment is refused at both layers |

## Timeouts, Availability and Data Handling

- C1 client timeout: 15 seconds. Reads get one retry; transfers require a person to choose retry and reuse the key. NFR6 remains 95% within 2 seconds at the demo load.
- C2 delivery: at least once, retried for 24 hours, then dead letter plus an alarm. The safety net makes wallet setup recoverable even after permanent event failure.
- C3 uses provider-native timeouts and capped SDK retries for safe reads only; account-changing operations are not blindly repeated by the app.
- C1, C3 and C5 use TLS 1.2 or later. C2 is encrypted in transit and at rest. C4 and the C5 verifier configuration contain no secret.
- Emails appear only in encrypted request/event bodies and responses to authorized callers, never in C1 URLs, logs, metric dimensions or alert text. Correlation and event IDs support investigation without personal data.

## Accepted Design Risks Carried Forward

The person approved Domain Design and Units Generation without requesting fixes to their review findings. This contract resolves some but does not silently change the approved unit graph or kinds:

- **Units R-01:** C2 and C5 pin the two U4-to-U2 boundaries, the signal and the edge, even though U2 does not depend on U4 in the approved graph. U2 and U4 each owe contract tests; U3 depends on both for the integrated test. Deployment order remains a Delivery Planning and Infrastructure Design concern.
- **Units R-02:** U4 remains `packaging`, so it receives no Functional Design. C2, C3, C4 and C5, with the provider capability checks in C3, are therefore the authoritative functional contracts for its sign-in, signal and edge behavior, and its Infrastructure Design must implement and trace them.
- **Units R-03/R-04:** U1 still needs a positive-amount check and must initialize both test users before the skeleton sends. These are construction requirements, not cross-boundary contracts.
- **Domain R-01:** Store-level uniqueness for one request per sender/key, one wallet per owner and one holder per normalized email remains for Functional and Infrastructure Design. C1 and C2 require the observable behavior.

## Open Questions

| Contract | Question | Blocks |
|---|---|---|
| C1 | What are the real API host names for `dev`, `stg` and `prd`? | C4 values and environment provisioning; not the API shape |
| C1 | What exact transfer-reference format will Ledger issue? The contract permits 1 to 64 characters. | Functional Design; not client generation |
| C2 | Which AWS event-bus resources implement the address, 24-hour retry and dead-letter behavior? | U2/U4 Infrastructure Design |
| C2 | Which monitoring email receives the dead-letter alarm? | Infrastructure Design / NFR Design |
| C3 | Which AWS sign-in service and SDK implement the behavior profile, and which fallbacks do its capability checks (P1 to P13) select? | U1 and U4 Infrastructure Design; U3 implementation |
| C4, C5 | What are each environment's issuer, audience and client ID, and how do U4's deployment outputs reach the U2 and U3 pipelines? | Infrastructure Design and environment provisioning |
| C5 | Which AWS resources implement the public edge, its firewall and its rate limits? | U1 and U4 Infrastructure Design |
| C1–C5 | Should a scheduled job with a read-only credential also re-check every consumer's pins against the owning repos' tags? Pinning works without it. | CI Pipeline |

## Sources

- `unit-of-work.md` and `unit-of-work-dependency.md` in `inception/units-generation/`: U1 to U5, their dependencies and integration points.
- `components.md` and `decisions.md` in `inception/domain-design/`: MobileApp, MoneyApi, Ledger, WalletDirectory, their entities and ADR-001 to ADR-007.
- `requirements.md` in `inception/requirements-analysis/`: FR1 to FR8, NFR1 to NFR15 and assumptions A4, A5 and A13.
- `stories.md` in `inception/user-stories/`: the acceptance criteria cited by ID.
- `contract-design-questions.md` in this directory: Q1 to Q7, all answered A.
- `team-practices.md` in `inception/practices-discovery/`: OpenAPI ownership, generated Dart client, environments, deployment order and security practices.
