# YFC Codex skills v5 - resource-aware

Этот набор skills используется как профильные рабочие контракты Your Fitness Coach. Начиная с task `49`, task-файлы разделяют их на core и conditional, чтобы не тратить контекст на области, которые фактически не затронуты.

## Правила

1. `Рекомендуемые skills` - открыть в начале для primary role.
2. `Условные skills` - открыть только после подтверждения trigger из task.
3. Code/diff reviewer и QA используют применимые base skills из role contract; non-code decision reviewer не загружает `$code-reviewer` автоматически. Их не нужно дублировать в каждой feature-task.
4. Skill не расширяет scope и не является причиной для нового refactor/migration/API/platform workstream.
5. Для обычной task предпочитается 2-5 core skills; для review/QA - base skill + максимум 1-2 профильных.
6. `$telegram-engineer` нужен для Telegram-specific contract, а не просто потому, что shared UI виден в TMA.
7. Dedicated `$ui-audit`, `$accessibility-engineer`, `$performance-engineer`, `$solution-architect` подключаются по реальной задаче/риску, а не автоматически.

См. `references/SKILL_ROUTING_GUIDE.md` и `references/MOBILE_TMA_ACCEPTANCE_MATRIX.md`.

Всего skills: **31**.
