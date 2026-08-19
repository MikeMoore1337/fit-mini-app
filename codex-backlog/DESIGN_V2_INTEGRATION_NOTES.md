# Design V2 - integration contract после task 46

Этот документ описывает переход от уже выполненных tasks `00-46` к новому Design V2 без повторного выполнения всего backlog.

## Порядок выполнения

```text
46A  Read-only production quality audit
46B  Read-only security/privacy/data-integrity audit
46C  Owner-approved critical remediation
46D  Read-only product UX/UI/Landing baseline audit
46E  Three visual directions + renders
     OWNER CHOICE
46F  Approved direction + final renders + design docs
     OWNER APPROVAL
46G  Production pilot
     OWNER MANUAL TEST
46H  Pilot refinement + final checkpoint
     OWNER APPROVAL
46I  Rollout on completed UI 00-46
46J  Align remaining backlog 47-93
47   Resume original backlog
```

Каждая task выполняется в отдельной Codex-сессии. Между checkpoint tasks требуется явное решение владельца.

## Source of truth после Design V2

После `46F-46I` приоритет визуальных источников:

1. фактический product behavior и ограничения security/privacy/SEO/accessibility;
2. утверждённые `docs/design/*v2*` и reference renders;
3. проверенная реализация shared Design V2 tokens/components;
4. canonical logo/brand assets task `07`;
5. старые design documents и Landing PNG только как historical context.

## Legacy Landing references

Файлы `landing-reference-dark.png` и `landing-reference-light.png` больше не являются целевым source of truth по композиции.

Разрешено сохранить или развить только обоснованные элементы:

- lime brand accent;
- graphite/dark neutral base;
- clean light theme;
- product UI как основной маркетинговый материал;
- единый бренд Web/Mobile/TMA;
- две аудитории: самостоятельный пользователь и тренер.

Нельзя автоматически наследовать hero layout, card grids, testimonials, imagery, typography, section sequence и visual rhythm.

## Scope safety

Новый блок не разрешает:

- повторно выполнять tasks `00-46`;
- переписывать backend без finding;
- менять business logic ради дизайна;
- добавлять новые features;
- создавать отдельный TMA frontend;
- начинать rollout до owner approval;
- продолжать task `47`, пока не завершена `46J`.
