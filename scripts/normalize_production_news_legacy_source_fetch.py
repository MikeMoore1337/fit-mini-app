from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PRODUCTION_FLAG = "NEWS_LEGACY_SOURCE_FETCH_ENABLED"
PRODUCTION_VALUE = "false"


def normalize_production_news_legacy_source_fetch(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Environment file does not exist: {path}")

    original = path.read_text(encoding="utf-8")
    trailing_newline = original.endswith("\n")
    seen = False
    updated_lines: list[str] = []
    for line in original.splitlines():
        key, separator, _value = line.partition("=")
        if separator and key == PRODUCTION_FLAG:
            if not seen:
                updated_lines.append(f"{PRODUCTION_FLAG}={PRODUCTION_VALUE}")
                seen = True
            continue
        updated_lines.append(line)

    if not seen:
        updated_lines.append(f"{PRODUCTION_FLAG}={PRODUCTION_VALUE}")

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

    return PRODUCTION_VALUE


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: normalize_production_news_legacy_source_fetch.py ENV_FILE")
    value = normalize_production_news_legacy_source_fetch(Path(sys.argv[1]))
    print(f"Production legacy news source fetching: {value}")


if __name__ == "__main__":
    main()
