"""Run pytest while keeping its generated files under .artifacts."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(
    root: Path,
    *,
    pytest_cache: Path,
    pytest_tmp: Path,
    process_tmp: Path,
) -> int:
    pytest_cache.parent.mkdir(parents=True, exist_ok=True)
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


def main() -> int:
    root = Path(__file__).resolve().parent.parent

    # On Windows, use a per-run temporary tree. This avoids stale/corrupted ACLs
    # or file-vs-directory collisions inside a shared .artifacts pytest cache.
    # Linux/CI keeps generated test files under .artifacts as before.
    if os.name == "nt":
        with tempfile.TemporaryDirectory(prefix="fitminiapp-pytest-") as temp_dir:
            temp_root = Path(temp_dir)
            return _run(
                root,
                pytest_cache=temp_root / "cache",
                pytest_tmp=temp_root / "basetemp",
                process_tmp=temp_root / "python",
            )

    artifacts = root / ".artifacts"
    return _run(
        root,
        pytest_cache=artifacts / "cache" / "pytest-runner",
        pytest_tmp=artifacts / "tests" / "pytest-runner-tmp",
        process_tmp=artifacts / "tmp" / "python",
    )


if __name__ == "__main__":
    raise SystemExit(main())
