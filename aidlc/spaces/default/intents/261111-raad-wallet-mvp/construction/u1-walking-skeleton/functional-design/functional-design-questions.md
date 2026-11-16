# Functional Design Questions — U1 Walking Skeleton

Conversation language: English.

## Q1. Simulated starting balance in prd

User Stories explicitly leaves A10 unconfirmed (AC6.4.2), although the current unit story map assigns this rule to U1. All money remains simulated, including prd.

- A. Give each new wallet exactly 1000.00 simulated SAR once in dev, stg and prd (recommended; matches the current acceptance scenario).
- B. Give the opening credit in dev and stg only; revise prd acceptance before implementation.
- X. Other (please specify)

[Answer]: A. New prd wallets receive 1000.00 simulated SAR once to try the product, as in dev and stg. (Message 77a32fc9.)
