# Порядок выполнения release backlog v29

## Completed

`00-73`, включая `69B` и предшествующие буквенные подзадачи. Task-файлы находятся в `tasks/done/`.

## Current

```text
73A Landing premium marketing art-direction, alternatives и production rollout
```

После завершения `73A`:

```text
74 Cross-product responsive/accessibility/states hardening
 -> 74A product-wide motion system и data visualization
 -> 75 performance/motion hardening
 -> 76 skill-aware retrospective audit -> 76A adversarial gate
 -> 77 real-user results checkpoint
 -> 78 production readiness
 -> 79 final go/no-go
```

`69B` завершена как owner-approved системное расширение иконографики и data visualization внутри
`DESIGN_V2_1`. Tasks `70-71` были завершены вне очереди отдельными task-only commits. Tasks `72-73`
завершены и архивированы после owner approval. По прямому решению владельца перед `74` добавлена
task `73A`: она сначала показывает три high-fidelity направления и ждёт owner selection, затем
реализует только выбранное и снова ждёт screenshot approval до commit. Task `74` остаётся
следующей и не реализуется в рамках `73A`. После `74` отдельная task `74A` проектирует и
распространяет уместный motion по приложению, canonical charts и Demo; `75` измеряет и устраняет
performance risks уже после rollout. Никакая task не запускает следующую автоматически.
