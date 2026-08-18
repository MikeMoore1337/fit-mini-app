# Prompt to start Codex

Use this after unpacking the task folder into the repository, adjusting the path if needed.

```text
Implement the Demo Mode task from the attached task package.

Start by reading:
1. <task-folder>/00_START_HERE.md
2. <task-folder>/01_SHARED_REQUIREMENTS.md
3. <task-folder>/02_AUDIT_AND_DESIGN.md

Also follow the repository AGENTS.md and applicable project skills.

Important:
- work in the current dedicated feature branch and keep all demo subtasks in this same branch;
- do not merge or deploy;
- complete only Stage 1 first;
- inspect the current repository and docs rather than assuming architecture;
- after Stage 1, run only relevant tests/checks and create a separate commit;
- then report what you found, the design decision, changed files, tests, and commit hash before proceeding to Stage 2.

AI Coach must not be available or callable in demo mode. It belongs to the authenticated full product.
```

## Prompt for the next stage

After reviewing the previous stage result, use:

```text
Continue the Demo Mode task in the same Git branch.

Read:
- <task-folder>/00_START_HERE.md
- <task-folder>/01_SHARED_REQUIREMENTS.md
- <task-folder>/<NEXT_STAGE_FILE>.md

Use the implementation decisions and repository state produced by the previous stages.
Implement only this stage, run stage-relevant tests, update docs if needed, and make one separate Git commit.
Do not merge or deploy.
Report changed files, tests/results, commit hash, and any blockers or deliberate follow-ups.
```
