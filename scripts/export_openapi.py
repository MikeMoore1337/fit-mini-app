"""Export the FastAPI OpenAPI document used to generate frontend types."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCHEMA_ENV_DEFAULTS = {
    "APP_ENV": "test",
    "APP_NAME": "FitMiniApp OpenAPI",
    "APP_HOST": "127.0.0.1",
    "APP_PORT": "8000",
    "APP_DEBUG": "false",
    "SECRET_KEY": "schema-generation-secret-at-least-32-characters",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "REFRESH_TOKEN_EXPIRE_DAYS": "30",
    "DATABASE_URL": "sqlite+pysqlite:///:memory:",
    "ENABLE_DEV_AUTH": "false",
    "TELEGRAM_BOT_TOKEN": "schema-generation-token",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    output = args.output if args.output.is_absolute() else Path.cwd() / args.output
    for name, value in SCHEMA_ENV_DEFAULTS.items():
        os.environ.setdefault(name, value)
    os.chdir(root)
    sys.path.insert(0, str(root / "backend"))

    from fitminiapp_api.main import app

    output.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
