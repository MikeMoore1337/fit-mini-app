from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROVIDER_KEY = "NEWS_IMAGE_PROVIDER"
SUPPORTED_PROVIDERS = {"disabled", "cloudflare_workers_ai"}


def normalize_production_news_image_provider(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Environment file does not exist: {path}")

    original = path.read_text(encoding="utf-8")
    trailing_newline = original.endswith("\n")
    lines = original.splitlines()
    configured_values = [
        value.strip()
        for line in lines
        for key, separator, value in [line.partition("=")]
        if separator and key == PROVIDER_KEY
    ]
    configured = configured_values[-1] if configured_values else ""
    normalized = configured if configured in SUPPORTED_PROVIDERS else "disabled"

    seen = False
    updated_lines: list[str] = []
    for line in lines:
        key, separator, _value = line.partition("=")
        if separator and key == PROVIDER_KEY:
            if not seen:
                updated_lines.append(f"{PROVIDER_KEY}={normalized}")
                seen = True
            continue
        updated_lines.append(line)

    if not seen:
        updated_lines.append(f"{PROVIDER_KEY}={normalized}")

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

    return normalized


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: normalize_production_news_image_provider.py ENV_FILE")
    provider = normalize_production_news_image_provider(Path(sys.argv[1]))
    print(f"Production news image provider: {provider}")


if __name__ == "__main__":
    main()
