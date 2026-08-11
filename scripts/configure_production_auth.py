from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PRODUCTION_AUTH_FLAGS = {
    "ENABLE_WEB_AUTH": "true",
    "ENABLE_EMAIL_AUTH": "false",
}


def configure_production_auth(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Environment file does not exist: {path}")

    original = path.read_text(encoding="utf-8")
    trailing_newline = original.endswith("\n")
    seen: set[str] = set()
    updated_lines: list[str] = []

    for line in original.splitlines():
        key, separator, _value = line.partition("=")
        if separator and key in PRODUCTION_AUTH_FLAGS:
            if key not in seen:
                updated_lines.append(f"{key}={PRODUCTION_AUTH_FLAGS[key]}")
                seen.add(key)
            continue
        updated_lines.append(line)

    for key, value in PRODUCTION_AUTH_FLAGS.items():
        if key not in seen:
            updated_lines.append(f"{key}={value}")

    content = "\n".join(updated_lines) + ("\n" if trailing_newline else "")
    mode = path.stat().st_mode
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(content)
            temporary_name = temporary.name
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: configure_production_auth.py ENV_FILE")
    configure_production_auth(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
