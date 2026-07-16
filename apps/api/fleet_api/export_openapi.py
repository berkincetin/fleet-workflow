"""Dump the FastAPI OpenAPI schema to a file for TS client generation."""

from __future__ import annotations

import json
import sys

from fleet_api.app import create_app


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else "packages/shared/openapi.json"
    schema = create_app().openapi()
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
