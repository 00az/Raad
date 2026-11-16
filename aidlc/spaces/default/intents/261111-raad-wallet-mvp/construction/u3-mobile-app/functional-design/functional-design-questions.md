# Functional Design Questions — U3 Mobile App

Conversation language: English.

## Q1. Number formatting in Arabic

User Stories explicitly leaves assumption A8 unconfirmed before implementation (AC5.1.4). Should amounts and dates use Western digits (0–9) in both languages, with SAR in English and ر.س in Arabic?

- A. Use Western digits in both languages, with the translated currency label (recommended for consistency with the current stories).
- B. Use Arabic-Indic digits in Arabic and Western digits in English.
- X. Other (please specify)

[Answer]: The person requires all frontend screens in Arabic and English (message 77a32fc9). Western digits in both languages remain the proposed A8 default for review, not an explicitly confirmed digit preference.
