"""Run pytest while keeping its generated files under .artifacts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    artifacts = root / ".artifacts"
    pytest_cache = artifacts / "cache" / "pytest-runner"
    pytest_tmp = artifacts / "tests" / "pytest-runner-tmp"
    process_tmp = artifacts / "tmp" / "python"
    pytest_tmp.parent.mkdir(parents=True, exist_ok=True)
    process_tmp.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "TMP": str(process_tmp),
        "TEMP": str(process_tmp),
        "TMPDIR": str(process_tmp),
    }
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *sys.argv[1:],
        "-o",
        f"cache_dir={pytest_cache}",
        f"--basetemp={pytest_tmp}",
    ]
    return subprocess.call(cmd, cwd=root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
