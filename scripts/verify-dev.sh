#!/usr/bin/env bash
set -euo pipefail

uv run --project ../money-service python ../money-service/scripts/verify_dev.py
