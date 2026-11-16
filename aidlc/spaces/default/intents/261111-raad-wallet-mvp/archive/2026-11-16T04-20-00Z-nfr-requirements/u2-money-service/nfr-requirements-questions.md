# NFR Requirements Questions — U2 Money Service

Conversation language: English.

## Q1. [Operations] Recovery objective for wallet and transfer data

If a service or data-store failure requires recovery, what is the acceptable recovery point objective (RPO: how much recent data could be lost) and recovery time objective (RTO: how long the service could be unavailable)? The existing requirements already set production availability at 99.5% per month.

- A. RPO at most 5 minutes and RTO at most 4 hours (recommended for the MVP).
- B. RPO 0 and RTO at most 1 hour (tighter recovery, with additional operational cost).
- C. Use the selected cloud data store's standard recovery defaults without a separate target.
- D. Other (please specify)

[Answer]: A

## Q2. [Operations] Resolve availability and recovery target overlap

The 99.5% monthly availability target allows about 3 hours 36 minutes of downtime in a 30-day month. A 4-hour recovery objective could exceed that budget. Which target should U2 use?

- A. Keep 99.5% monthly availability and 5-minute RPO; tighten RTO to at most 3 hours (recommended).
- B. Keep 5-minute RPO and 4-hour RTO; lower the monthly availability target to at most 99.4%.
- C. Other (please specify)

[Answer]: A
