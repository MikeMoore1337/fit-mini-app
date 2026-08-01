# Workspace hygiene

- Put every tool cache, temporary directory, test artifact, log, and generated
  report under `.artifacts/`; never create `.tmp*`, `pytest-cache-files-*`, or
  other scratch paths in the repository root.
- Prefer the paths already configured in `pyproject.toml` and the wrappers in
  `scripts/`. If an isolated cache is needed, create it below
  `.artifacts/cache/` or `.artifacts/tmp/`.
