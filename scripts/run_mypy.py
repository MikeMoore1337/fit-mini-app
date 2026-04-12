"""Запуск mypy для пакета app из каталога backend (корректный PYTHONPATH)."""

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
        "app",
        "--config-file",
        str(cfg),
    ]
    return subprocess.call(cmd, cwd=backend, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
