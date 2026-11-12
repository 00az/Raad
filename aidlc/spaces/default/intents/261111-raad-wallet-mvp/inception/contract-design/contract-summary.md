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

The API description is owned in `RaadMoneyService` at `openapi/raad-money-v1.yaml`. U1 introduces the v1 description for the walking-skeleton operations. U2 completes it. `RaadMobile` pins an exact released revision and generates its Dart client from it in CI (Q3 A). Handwritten request and response models in `RaadMobile` are not allowed.

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
        '404':
          description: >
            No recipient has the normalized email address. This is a persisted
            first business outcome for this caller and idempotency key.
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
          description: Page size; defaults to 20 and cannot exceed 100.
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
        false on the first response and on a non-persisted error; true when this
        response comes from the persisted first outcome for an earlier request
        with this caller and key.
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
          description: Opaque cursor for the next page; null at the end. Valid for 24 hours.
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

The app sends `Authorization: Bearer <access token>` (Q7 A). C5 governs the U4 edge and U2 verification layers: both verify signature, issuer, audience, expiry, token type and the pinned asymmetric algorithm against the environment's key-discovery configuration, including rotation and discovery failure. The edge forwards the access token unchanged and strips caller-supplied identity headers. MoneyApi takes the user ID only from the independently verified token's `sub`. No request contains a caller user ID or a source wallet ID. MoneyApi uses that `sub` for wallet setup, wallet reads, transfers, history and the idempotency-key scope. A token, issuer, audience or key configuration from `dev` cannot authorize `stg` or `prd`. Every edge- or service-generated response carries the same `X-Correlation-Id`; every error body follows the C1 `Error` schema.

### Error and retry behavior

- Every error body follows `Error`. The Dart app branches on `code` and displays its own Arabic or English text; `message` is only a safe fallback.
- The app's request timeout is 15 seconds. The service target remains NFR6: 95% of transfers answer within 2 seconds at 10 concurrent users.
- The app may retry `PUT /wallet`, `GET /wallet`, `POST /recipients/resolve` and `GET /transfers` once after a timeout, 500 or 503. It respects `Retry-After` on 429 and 503.
- It never automatically retries validation, authentication, authorization, recipient, self-transfer, amount, low-balance, idempotency-conflict or cursor errors.
- A transfer is retried only after the user chooses **Try again**, with the same locked recipient, amount and `Idempotency-Key` (Q6 A). A key with different normalized recipient or amount returns 409 / `IDEMPOTENCY_KEY_REUSED` and never changes the first outcome.
- Requests are strict: an unknown request field is refused. Provider emission is checked against the documented response fields, but consumers tolerate and ignore unknown response fields as described under Compatibility behavior.

### Transfer idempotency matrix

MoneyApi processes `POST /transfers` in this order: verify C5 identity and rate limits; parse the header and body; normalize the recipient email; build a fingerprint from contract major version `1`, the normalized recipient email and `amountHalalas`; then conditionally create the first `TransferRequest` for the unique pair `(verified sub, Idempotency-Key)`. The client-supplied key is opaque and never used without the verified `sub`.

The first business outcome and its fingerprint remain for the lifetime of the environment in this MVP. A key is never made available for another transfer. If a later retention policy erases the owning account and its transfer data, it may erase the key with that data; no active app session may retain it afterward.

| First attempt or repeat | Key reserved or outcome persisted? | HTTP and code | Repeat with identical fingerprint | `Idempotency-Replayed` |
|---|---|---|---|---|
| Malformed JSON, missing/unknown field, invalid key syntax, non-integer amount or email invalid after normalization | No | 400 `VALIDATION_ERROR` | Evaluated as a new attempt after the request is corrected | Header omitted |
| Missing, invalid, expired, wrong-environment or wrong-type token; authorization refusal | No | 401 `AUTHENTICATION_REQUIRED` or 403 `FORBIDDEN` | Evaluated again | Header omitted |
| Rate limit reached | No | 429 `RATE_LIMITED` | Evaluated again after `Retry-After` | Header omitted |
| No recipient has the normalized email | Yes, as a final refused outcome | 404 `RECIPIENT_NOT_FOUND` | Same status, code and business result; a fresh request correlation ID | `true` on repeat, `false` first |
| Recipient is the caller | Yes, as a final refused outcome | 409 `SELF_TRANSFER` | Same status, code and business result; a fresh request correlation ID | `true` on repeat, `false` first |
| Amount is below 100 or above 50,000 halalas | Yes, as a final refused outcome | 422 `AMOUNT_OUT_OF_RANGE` | Same status, code and business result; a fresh request correlation ID | `true` on repeat, `false` first |
| Balance is too low | Yes, as a final refused outcome | 422 `INSUFFICIENT_FUNDS` | Same status, code and business result even if money arrives later; a fresh request correlation ID | `true` on repeat, `false` first |
| Transfer completed | Yes, in the same all-or-nothing change as both balances and the Transfer | 201 with `TransferResult` | Same transfer ID, reference, amount, recipient, completion time and resulting balance; a fresh request correlation ID | `true` on repeat, `false` first |
| Same `(sub, key)` already exists with a different fingerprint | No new outcome; original remains unchanged | 409 `IDEMPOTENCY_KEY_REUSED` | Not applicable | `false` |
| Store or service fails before the all-or-nothing outcome commits | No | 500 `INTERNAL_ERROR`, 503 `SERVICE_UNAVAILABLE`, or no response | May execute when the person retries; no money moved on the failed attempt | Header omitted |
| Outcome commits but the response is lost | Already final | The first caller may receive no response | Retry returns the persisted business outcome as above | `true` on retry |

For two simultaneous requests with the same `(sub, key)` and fingerprint, one conditional operation creates the outcome. The other waits for that atomic operation to resolve, then reads and returns that same final business outcome. No externally visible `pending` outcome exists. If the store fails before either commits, neither reserves the key or changes a balance and both may receive a transient failure. Two simultaneous requests with one key and different fingerprints result in one first outcome and one 409 `IDEMPOTENCY_KEY_REUSED`; which fingerprint wins is not promised, so the app must never do this.

`AMOUNT_OUT_OF_RANGE` is a Ledger business refusal, not schema validation: the OpenAPI request accepts any int64 and the Ledger applies the 100–50,000 range. This removes the former 400/422 ambiguity. `WALLET_NOT_FOUND`, if the safety-net `PUT /wallet` has not completed, is not persisted against the transfer key; the app ensures the wallet and may then retry with the same key.

### Compatibility behavior

- Request schemas are closed (`additionalProperties: false`) and provider request validation runs after the normalization described below.
- Response schemas and the C2 event payload are open to unknown fields for consumers. U2 and U4 provider-emission tests separately refuse undeclared output fields unless the field has first been added to the current owned contract.
- Generated C1 clients must deserialize a response containing an unknown optional field and continue using all known fields. The C2 consumer must do the same for an event. These are compatibility tests in U3 and U2 respectively.
- Removing, renaming or changing a field, making an optional field required, or adding an enum value when a consumer lacks an unknown-value fallback remains breaking and requires a new major version.

### Email normalization

For `ResolveRecipientRequest.email` and `CreateTransferRequest.recipientEmail`, MoneyApi performs these steps before email-format validation, lookup, self-transfer comparison or idempotency fingerprinting: remove leading and trailing Unicode whitespace; normalize Unicode to NFC; lowercase the complete address for comparison; then validate the normalized complete address. The normalized value must be at most 254 characters. WalletDirectory uses this same value as `emailKey`. MobileApp performs the same trim and lowercase for early feedback, but server correctness never depends on the client doing it. The confirmed display spelling from WalletDirectory is returned in `Recipient.email`.

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
          const: '1.0'
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
  required_claims: [sub, iss, aud, exp, iat, email, displayName]
  claim_rules:
    sub: immutable opaque user identifier within one environment
    iss: unique issuer for one environment
    aud: unique mobile app client for one environment
    email: confirmed address used by the C1 wallet-setup safety net
    displayName: display name used by the C1 wallet-setup safety net
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
- U4 applies provider-native limits to sign-up, confirmation, resend, sign-in and password-reset operations. These direct account calls do not pass through the public API firewall; NFR12 and AC1.3.5 depend on these provider limits.
- MobileApp never sends passwords, codes or tokens to C1. Access and refresh tokens are held only in phone secure storage.

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
  required_checks: [signature, issuer, audience, expiry, not-before-if-present, token-type]
  required_token_type: access-token
  caller_id_claim: sub
  accepted_algorithms: [RS256]
  configuration:
    canonical_contract: C3
    per_environment_fields: [issuer, audience, jwksUri, acceptedAlgorithms]
    delivery: immutable non-secret deployment configuration
  key_discovery:
    transport: HTTPS
    source: jwksUri
    cache_maximum_minutes: 360
    unknown_kid_behavior: refresh-once-then-refuse
    rotation: >
      New and retiring keys overlap for at least the greater of the access-token
      lifetime and the verifier cache maximum. Verifiers accept both during overlap.
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

C3 supplies `issuer`, `audience`, `jwksUri` and `acceptedAlgorithms` to U2 as non-secret environment configuration. U2 refuses to start if any is missing or if the issuer/audience identify a different environment. The edge forwards the original access token to MoneyApi; it never converts token claims into trusted identity headers. MoneyApi independently verifies the token and takes the caller only from `sub`.

### Edge tests

- U4 proves path and query forwarding, request-body preservation, allowed-header forwarding, spoofed identity-header stripping, correlation-ID creation/preservation, edge error shape, 401/403/429/503 mappings and `Retry-After`.
- U2 proves issuer, audience, algorithm, expiry, token type and signature checks; unknown-key refresh; overlapping-key rotation; cached-key behavior during discovery failure; refusal to start with missing or cross-environment configuration; and that no request field or forwarded identity header can replace `sub`.
- The joint test sends the same C1 request through the edge and directly to a test MoneyApi adapter and compares the C1 status/body, apart from headers that C5 owns. A token from each wrong environment is refused at both layers.

---

## Contract Ownership and Change Rules

- **C1:** U2 owns `openapi/raad-money-v1.yaml`. U1 may introduce its initial revision, but U2 owns every later change. U3 pins an exact released revision and generates its client in CI.
- **C2:** U4 owns the `UserConfirmed` event name and payload. U2 owns its consumer behavior but cannot change the payload contract alone.
- **C3 and C4:** U4 owns the behavior and configuration schemas. U3 owns its client implementation and tests against them.
- An additive response field is safe only when optional and consumers ignore unknown fields. Removing or renaming a field, making an optional field required, changing its meaning or type, narrowing a numeric range, or adding an enum value without an unknown-value fallback is breaking.
- A breaking C1 change uses `/money/v2` and a new OpenAPI major version. A breaking C2 change uses a new event address such as `raad.identity.user-confirmed.v2`. Breaking C3 or C4 changes use version `2.0` and coexist with v1 until U3 migrates.
- A provider keeps the old major version until every registered consumer has migrated and both engineers approve its removal. A provider change and its compatibility report are reviewed in that provider repo's pull request.
- CI checks C1 against the last released v1 description and checks C2 to C4 against their last released schemas. Additive changes still require the owner's review; breaking changes require coordinated changes in provider and consumer repos.
- Consumers never rely on undocumented fields, transport metadata, ordering between unrelated events, or provider-specific error text.

## Contract Test Responsibilities

| Contract | Provider check | Consumer check | Integrated check |
|---|---|---|---|
| C1 | U2 validates every request/response against OpenAPI and tests all status/code combinations; Ledger replay/concurrency tests remain behind it | U3 generates the Dart client, runs client tests against an OpenAPI-based fake server, and has no handwritten models | U1 proves balance/send/history on `dev`; U3 runs all later mobile integration tests against the real U2 service (Q2 B in Units Generation) |
| C2 | U4 validates emitted events against AsyncAPI and tests publish failure never fails confirmation | U2 validates events and tests duplicate, simultaneous, wrong-environment, malformed and dead-letter cases | U3 confirms an account and observes exactly one wallet with 1,000.00 SAR; the safety-net test covers a lost event |
| C3 | U4 tests every configured sign-in behavior, generic response and rate limit | U3 tests each screen against a provider test environment | U3's account integration suite on `dev` |
| C4 | U4 validates each environment's generated configuration against the schema | U3 fails builds on missing, secret-looking or cross-environment values | Each environment's smoke test checks that the app calls only its matching API and issuer |

## Timeouts, Availability and Data Handling

- C1 client timeout: 15 seconds. Reads get one retry; transfers require a person to choose retry and reuse the key. NFR6 remains 95% within 2 seconds at the demo load.
- C2 delivery: at least once, retried for 24 hours, then dead letter plus an alarm. The safety net makes wallet setup recoverable even after permanent event failure.
- C3 uses provider-native timeouts and capped SDK retries for safe reads only; account-changing operations are not blindly repeated by the app.
- C1 and C3 use TLS 1.2 or later. C2 is encrypted in transit and at rest. C4 contains no secret.
- Emails appear only in encrypted request/event bodies and responses to authorized callers, never in C1 URLs, logs, metric dimensions or alert text. Correlation and event IDs support investigation without personal data.

## Accepted Design Risks Carried Forward

The person approved Domain Design and Units Generation without requesting fixes to their review findings. This contract resolves some but does not silently change the approved unit graph or kinds:

- **Units R-01:** C2 now pins the U4-to-U2 signal even though U2 does not depend on U4 in the approved graph. U2 and U4 each owe contract tests; U3 depends on both for the integrated test. Deployment order remains a Delivery Planning and Infrastructure Design concern.
- **Units R-02:** U4 remains `packaging`, so it receives no Functional Design. C2, C3 and C4 are therefore the authoritative functional contracts for its sign-in and signal behavior, and its Infrastructure Design must implement and trace them.
- **Units R-03/R-04:** U1 still needs a positive-amount check and must initialize both test users before the skeleton sends. These are construction requirements, not cross-boundary contracts.
- **Domain R-01:** Store-level uniqueness for one request per sender/key, one wallet per owner and one holder per normalized email remains for Functional and Infrastructure Design. C1 and C2 require the observable behavior.

## Open Questions

| Contract | Question | Blocks |
|---|---|---|
| C1 | What are the real API host names for `dev`, `stg` and `prd`? | C4 values and environment provisioning; not the API shape |
| C1 | What exact transfer-reference format will Ledger issue? The contract permits 1 to 64 characters. | Functional Design; not client generation |
| C2 | Which AWS event-bus resources implement the address, 24-hour retry and dead-letter behavior? | U2/U4 Infrastructure Design |
| C2 | Which monitoring email receives the dead-letter alarm? | Infrastructure Design / NFR Design |
| C3 | Which AWS sign-in service and SDK implement the behavior profile, and can its native settings satisfy every generic response? | U4 Infrastructure Design and U3 implementation |
| C4 | What are each environment's issuer, audience and client ID? | Environment provisioning |
| C1–C4 | How is a released contract revision tagged so another repo can pin it? | Delivery Planning and CI Pipeline |

## Sources

- `unit-of-work.md` and `unit-of-work-dependency.md` in `inception/units-generation/`: U1 to U5, their dependencies and integration points.
- `components.md` and `decisions.md` in `inception/domain-design/`: MobileApp, MoneyApi, Ledger, WalletDirectory, their entities and ADR-001 to ADR-007.
- `requirements.md` in `inception/requirements-analysis/`: FR1 to FR8 and NFR1 to NFR15.
- `contract-design-questions.md` in this directory: Q1 to Q7, all answered A.
- `team-practices.md` in `inception/practices-discovery/`: OpenAPI ownership, generated Dart client, environments, deployment order and security practices.
