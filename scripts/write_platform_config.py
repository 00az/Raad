"""Write one environment's C4 mobile configuration and C5 verifier file from deployment outputs.

Input is the JSON that `cdk deploy --outputs-file` wrote for the platform stacks of exactly one
environment. The tool never calls AWS and never reads credentials. It refuses missing, extra,
cross-environment or secret-looking values and never overwrites an unrelated file. Output:

    <output-dir>/config/<env>.json     C4, delivered to RaadMobile's pinned build input
    <output-dir>/verifier/<env>.json   C5 raad-token-verifier-config (also in /raad/<env>/verifier)

Run from infrastructure/:
    uv run python ../scripts/write_platform_config.py --environment dev --account <account-id> \
        --outputs outputs.json --output-dir <directory>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "infrastructure"))

from raad_platform.configuration import (
    ENVIRONMENTS,
    ConfigurationError,
    build_configuration,
    write_configuration,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--environment", required=True, choices=ENVIRONMENTS)
    parser.add_argument("--account", required=True, help="expected 12-digit account ID")
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.outputs.read_text(encoding="utf-8"))
        configuration = build_configuration(
            document, environment=args.environment, account=args.account
        )
        written = write_configuration(configuration, args.output_dir)
    except ConfigurationError as error:
        print(f"Configuration refused: {error}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError, json.JSONDecodeError):
        print("Configuration refused: outputs file is unreadable or not JSON", file=sys.stderr)
        return 1
    for path in written:
        print(f"Wrote {path.parent.name}/{path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
