# Design V2 - integration contract после task 46

Этот документ описывает переход от уже выполненных tasks `00-46` к новому Design V2 без повторного выполнения всего backlog.

## Порядок выполнения

```text
46A  Read-only production quality audit
46B  Read-only security/privacy/data-integrity audit
46B1 Consolidated triage + owner decision
46C  Umbrella for owner-approved remediation
46C.1 Root/Admin/Trainer authorization boundaries
46C.2 Measurement chronology/concurrency/dependent state
46C.3 Cross-context auth/workout recovery
46C.4 Account export/browser privacy lifecycle
46C.5 HTTP limits/safe logging boundary
46C.6 Telegram auth proxy-tunnel preservation
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

Каждая implementation task выполняется в отдельной Codex-сессии. `46C.1-46C.6` идут строго
последовательно с отдельными commits; `46D` запрещено начинать, пока не завершены все шесть.
Между checkpoint tasks требуется явное решение владельца.

На момент завершения task `46J` цепочка `46A-46J`, включая owner checkpoints и task `46C.6`,
завершена. Следующая допустимая задача — `47-profile-account-experience.md`.

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

## Conflict analysis task 46J

Functional scope перечисленных tasks не изменён: правки ограничены источниками визуальной истины,
переиспользованием shared Design V2 и профильными browser/quality gates.

| Future task | Найденный конфликт и риск | Минимальная синхронизация | Functional scope |
| --- | --- | --- | --- |
| `47` | Profile мог создать локальную settings/card system, а dependency line не фиксировала gate `46J`. | Добавлены зависимость `46J`, контракт shared forms/actions/states и browser-проверка. | Не изменён. |
| `48` | Coach workspace мог стать отдельным generic admin/SaaS dashboard. | Зафиксированы shared shell, data regions, desktop/mobile и light/dark parity. | Не изменён. |
| `49` | Комментарии могли получить messenger/chat visual language. | Закреплён встроенный feedback region на общих primitives. | Не изменён. |
| `50` | Public и in-app knowledge могли разойтись по palette и components. | Закреплены единая content grammar и shared typography/navigation. | Не изменён. |
| `52` | Check-in мог ввести локальный wizard/card language. | Указаны shared form, action и confidence patterns. | Не изменён. |
| `53` | Calibration states могли переопределить semantic colors. | Указаны shared data/form/action и insufficient/error states. | Не изменён. |
| `55` | Workout adaptation могла создать отдельный workout skin. | Закреплены существующие workout, sheet/dialog и diff patterns. | Не изменён. |
| `56` | История могла ввести локальную timeline/card system. | Указаны shared timeline/data/status primitives. | Не изменён. |
| `57` | Anthropometry могла создать отдельную analytics palette. | Закреплены semantic tokens, accessible charts и state coverage. | Не изменён. |
| `58` | Confidence мог распасться на локальные badges и цвета. | Закреплён один reusable state pattern с text/icon redundancy. | Не изменён. |
| `60` | Progression guidance могла стать отдельной gamified card system. | Указаны shared evidence/status/disclosure patterns. | Не изменён. |
| `61` | Notifications и Telegram fallback могли разойтись визуально. | Закреплены shared lists/forms/states across Web/Mobile/TMA. | Не изменён. |
| former `59A` | Bot-specific controls могли протечь в Web/TMA visual language. | Полностью перенесено в отдельный Telegram backlog; main UI сохраняет только integration boundaries. | Не изменён. |
| `62` | Export/destructive flows могли получить локальную palette и cards. | Закреплены shared account/feedback primitives и recovery states. | Не изменён. |
| `63` | Cardio gap мог породить отдельную activity-tracker систему. | Указана интеграция в Today/workout/history/Progress patterns. | Не изменён. |
| `65` | Demo design мог стать отдельной marketing/demo theme. | Зафиксировано использование реального Design V2 shell/components. | Не изменён. |
| `66` | Demo mode мог создать собственную palette/navigation. | Indicator и locked state привязаны к shared product states. | Не изменён. |
| `67` | Fixtures могли проверять mock UI и demo-only variants. | Закреплены реальные components и representative V2 states. | Не изменён. |
| `68` | Conversion flow мог вернуть generic SaaS takeover patterns. | CTA, prompts и auth transition привязаны к shared V2 primitives. | Не изменён. |
| `69` | Demo handoff мог создать отдельный login/provider skin. | Закреплены shared Demo/Auth surfaces и browser states. | Не изменён. |
| `71` | Финальная Demo-проверка не защищала Design V2 parity. | Добавлен browser gate для light/dark и отсутствия demo-only language. | Не изменён. |
| `76` | Admin Workspace мог стать отдельным admin template. | Закреплена плотная, но общая Design V2 system и browser QA. | Не изменён. |
| `77` | Profile/Admin/Coach application flow мог разойтись визуально. | Зафиксированы общие form/status/navigation primitives и state pass. | Не изменён. |
| `78` | TMA мог трактоваться как отдельный редизайн, а bot-specific work было смешано с main backlog в dependency line. | Зафиксирована формула shared UI + responsive composition + adapter, только platform differences и отдельная bot-workstream boundary без зависимости main backlog. | Не изменён. |
| `79` | Legacy Landing PNG считались composition source of truth. | Источник заменён на Approved Design V2 renders/shared implementation; PNG оставлены historical. | Не изменён. |
| `80` | Responsive/a11y audit мог проверять legacy UI и Landing PNG. | Gate переведён на фактический Design V2, parity, states и browser coverage. | Не изменён. |
| `81` | Performance task могла измерять абстрактный redesign и legacy assets. | Уточнены реальные V2 assets, fonts/images, CLS, main-thread, motion и reduced motion. | Не изменён. |
| `96` | AI UI мог создать отдельный generic chat/AI style. | Закреплены shared shell/components/states и запрет provider-inspired styling. | Не изменён. |
| `98` | Readiness не перечисляла актуальные production skills и V2 recovery states. | Добавлены профильные skills и production-build state evidence без повторения закрытых audits. | Не изменён. |
| `99` | Final gate не проверял весь Design V2 и решения findings `46A-46C`; bot-specific work ранее было смешано с main dependency list. | Добавлены human-made flows, legacy-fragment gate, связь с task `77` evidence и separate bot-workstream boundary. | Не изменён. |

## Design alternatives после завершённых tasks 00-49

Новый блок `49A-49G` не отменяет результаты `46D-46J` и не делает Design V2 устаревшим автоматически.

До явного owner decision в `49F` и closure/rollout task `49G`:

- Design V2 остаётся production source of truth;
- новые directions являются только exploration artifacts;
- pending tasks читают `ACTIVE_DESIGN_SOURCE.md`;
- production UI нельзя менять по неутверждённым renders;
- completed task files `00-49` не редактируются.

Если владелец утверждает V2.1 или V3, task `49G` создаёт новый canonical integration contract и сохраняет этот документ как исторический источник Design V2.
