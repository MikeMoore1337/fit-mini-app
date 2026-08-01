"""Export the FastAPI OpenAPI document used to generate frontend types."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    os.chdir(root)
    sys.path.insert(0, str(root / "backend"))

    from fitminiapp_api.main import app

    output.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
