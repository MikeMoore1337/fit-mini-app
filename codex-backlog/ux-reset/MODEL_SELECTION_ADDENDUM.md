# Model selection addendum - UX-reset cycle

Модели являются рекомендацией и не переключаются Codex автоматически. Приоритет существующего `codex-backlog/MODEL_SELECTION.md` и owner selection сохраняется.

| Task | Recommended model |
|---|---|
| 113 | GPT-5.6 Sol High |
| 114 | GPT-5.6 Sol High |
| 115A | GPT-5.6 Sol High; Terra High допустима для focused prototype work |
| 116 | GPT-5.6 Terra High |
| 117 | GPT-5.6 Sol High |
| 118 | GPT-5.6 Terra High; Sol High если затронут backend/domain contract |
| 119 | GPT-5.6 Sol High |
| 120A-D | GPT-5.6 Sol High |
| 121 | GPT-5.6 Terra High; Sol High при TMA/routing architecture change |
| 122 | GPT-5.6 Terra High |
| 123 | GPT-5.6 Terra High |
| 124A | GPT-5.6 Sol High |
| 124B | GPT-5.6 Sol High |
| 124C | GPT-5.6 Sol High |

Existing Tasks 81/82/84 сохраняют canonical model recommendation своих task files, если owner не изменит её. При cross-surface/domain-sensitive изменениях не понижать модель только ради экономии.

Не понижать модель для auth, data migration, domain integrity, platform/release gate, human evidence synthesis и cross-surface audit.
