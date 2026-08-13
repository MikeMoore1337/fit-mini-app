# Workspace hygiene

- Put every tool cache, temporary directory, test artifact, log, and generated
  report under `.artifacts/`; never create `.tmp*`, `pytest-cache-files-*`, or
  other scratch paths in the repository root.
- Prefer the paths already configured in `pyproject.toml` and the wrappers in
  `scripts/`. If an isolated cache is needed, create it below
  `.artifacts/cache/` or `.artifacts/tmp/`.

# Workflow

- Work on the task in stages. After each completed stage, run only the tests
  related to that stage so that the changes are checked in isolation, then
  create a separate Git commit for that stage.
- Do not leave the project in a knowingly non-working state. If a full test
  suite or broader verification is needed, report that separately and wait for
  the user's decision before running it.
