# Contracts owned by Raad

Each file below is the canonical contract that the U4 platform provides. A release is an annotated
tag `contract/<contract ID>/v<MAJOR>.<MINOR>.<PATCH>` on `main`, whose message carries the
SHA-256 of the file's bytes. Tags are never moved or deleted. Until U4's provider tests pass for a
whole file and the change lands on `main`, its version carries a pre-release suffix (`-rc.N`).

A consumer keeps `contracts/pins.yaml` and a byte-for-byte copy under `contracts/pinned/`, and
changes a pin only through a pull request in its own repo. Add a consumer to this register by pull
request.

| Contract | Canonical file | Contract ID | File version | Consumers that pin it |
|---|---|---|---|---|
| C2 UserConfirmed event | `contracts/c2-identity-events-v1.asyncapi.yaml` | `c2-identity-events` | `1.0.0-rc.1` | `RaadMoneyService` |
| C3 Sign-in client profile | `contracts/c3-sign-in-client-profile-v1.yaml` | `c3-sign-in-profile` | `1.0.0-rc.1` | `RaadMobile` |
| C4 Mobile environment configuration | `contracts/c4-mobile-environment-config-v1.schema.yaml` | `c4-mobile-config` | `1.0.0-rc.1` | `RaadMobile` |
| C5 Public API edge and token verifier | `contracts/c5-money-edge-v1.yaml` | `c5-money-edge` | `1.0.0-rc.1` | `RaadMoneyService` |

The C2 file is unchanged byte for byte from the copy `RaadMoneyService` pins today, so that pin
stays valid. Raising C2 to `1.0.0` and tagging it is a separate release step after U4's provider
tests land on `main`; U2 then moves its pin by pull request.

## Platform outputs other units read

Every value is non-secret and specific to one environment (`<env>` is `dev`, `stg` or `prd`).

| SSM parameter | Written by | Read by | Holds |
|---|---|---|---|
| `/raad/<env>/event-bus/arn` | `RaadIdentity-<env>` | U2 deploy (`RAAD_EVENT_BUS_ARN`) | The C2 event bus |
| `/raad/<env>/alarm-topic/arn` | `RaadMonitoring-<env>` | U2 deploy (`RAAD_ALARM_TOPIC_ARN`) | The `raad-<env>-alerts` topic |
| `/raad/<env>/platform-edge-role-arn` | `RaadPublicEdge-<env>` | U2 deploy (`RAAD_EDGE_ROLE_ARN`) | The only role allowed to call MoneyApi |
| `/raad/<env>/correlation-hmac/arn` | `RaadPublicEdge-<env>` | U2 deploy (`RAAD_CORRELATION_SECRET_ARN`) | Secret reference only, never its value |
| `/raad/<env>/verifier` | `RaadPublicEdge-<env>` | U2 MoneyApi at start | C5 `raad-token-verifier-config` JSON |
| `/raad/<env>/public-api-url` | `RaadPublicEdge-<env>` | Smoke tests, C4 writer | The public HTTPS origin |

U2 writes `/raad/<env>/money-api/function-url`, which the platform edge reads at request time.
C4 files for U3 come from `scripts/write_platform_config.py` (see `infrastructure/README.md`).
