# Discovered Rules: RAAD

These are the hard rules the person chose at the practices interview (Q9: A, B,
C, D and E). On approval they are added to `project.md`.

## Mandated

ALWAYS store and calculate money as whole halalas (1 SAR = 100 halalas), never as decimals or floating-point numbers.

## Forbidden

NEVER commit secrets, passwords or AWS keys to the repository.
NEVER connect to real payment systems or accept real card or bank details; funds are simulated and SAR is the only currency.
NEVER write passwords, tokens or personal details into logs.
NEVER deploy to prd a version that has not passed its checks and smoke test on dev first.
