# Infrastructure Design Questions — U1 Walking Skeleton

Conversation language: English.

## Q1. [Platform] Shared sign-in provider

Which provider should U1 target for the shared user pool and access-token behavior?

- A. Amazon Cognito User Pools (Recommended) — use the shared pool and verify its required capabilities against C3 before implementation.
- B. Other provider — name the provider and its existing or planned AWS integration.
- X. Other (please specify)

[Answer]: A. Amazon Cognito User Pools (Recommended)
**Answered:** 2026-11-13 12:46:37 UTC
**Mode:** chat

## Q2. [Platform] Public API edge

Which AWS public API edge should U1 target to meet C5 routing, token verification, correlation ID, firewall, and C1 error requirements?

- A. API Gateway HTTP API behind CloudFront and AWS WAF (Recommended) — CloudFront provides firewall and edge controls; API Gateway handles C5 routes.
- B. API Gateway REST API with AWS WAF — use its broader API features and accept additional cost and configuration.
- C. Other AWS edge — name the resource and how it will meet C5.
- X. Other (please specify)

[Answer]: A. API Gateway HTTP API behind CloudFront and AWS WAF (Recommended)
**Answered:** 2026-11-13 12:46:37 UTC
**Mode:** chat

## Q3. [Operations] Dead-letter alert destination

What destination should receive the required dead-letter notification?

- A. Team monitored email address (Recommended) — provide the address when configuring the environment; keep it out of source control.
- B. Team incident notification topic — provide the topic ARN.
- C. Defer notification wiring — keep the alarm defined, but treat notification setup as blocked until a destination is provisioned.
- X. Other (please specify)

[Answer]: A. Team monitored email address (Recommended); provide the address during environment setup.
**Answered:** 2026-11-13 12:46:37 UTC
**Mode:** chat

## Consolidated Summary Confirmation

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
