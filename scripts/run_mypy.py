"""Запуск mypy для пакета fitminiapp_api из каталога backend."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    backend = root / "backend"
    cfg = root / "pyproject.toml"
    env = {**os.environ, "PYTHONPATH": str(backend)}
    cmd = [
        sys.executable,
        "-m",
        "mypy",
        "fitminiapp_api",
        "--config-file",
        str(cfg),
    ]
    return subprocess.call(cmd, cwd=backend, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
