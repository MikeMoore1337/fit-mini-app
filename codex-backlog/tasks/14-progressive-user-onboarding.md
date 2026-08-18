# TASK 14. Progressive onboarding обычного пользователя

- Фаза: **Activation / Core UX**
- Приоритет: **14/93**
- Зависит от: `10`, `11`, `12`, `13`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Сделать первый запуск понятным и коротким: после авторизации пользователь должен быстро
получить персональный базовый контекст и попасть в полезный продукт, а не в длинную анкету.

## In scope

1. Сначала проверить фактический current first-run flow, profile completeness rules и auth redirect.

2. Ввести явное onboarding state/contract без дублирования Profile domain.

3. Первый обязательный слой — только поля, реально необходимые для базового персонального опыта:
   - цель из canonical product goals;
   - пол, возраст, рост, вес — только если они действительно нужны текущему deterministic КБЖУ;
   - обязательные legal/consent шаги только если уже требуются продуктом/юрисдикцией.

4. Не спрашивать заранее то, что нужно только конкретной функции.
Progressive disclosure:
   - training frequency/level/equipment — когда пользователь идёт в подбор программы;
   - body-part priorities — когда открывает расширенные training/progress preferences;
   - AI-specific memory/preferences — только в AI block;
   - trainer-specific setup — только при включении Trainer capability.

5. После минимального шага пользователь должен попасть в понятный next action:
   - настроить питание / посмотреть рассчитанную цель;
   - подобрать программу;
   - открыть Today.
   Не заставлять выполнять все три сценария.

6. Поддержать:
   - Web;
   - mobile Web;
   - TMA;
   - refresh/resume;
   - safe back/forward;
   - уже заполненный профиль;
   - существующий пользователь, которому onboarding не нужен.

7. Не создавать отдельный user profile shadow model.
Все persisted values должны использовать существующие authoritative domain fields.

8. Ошибки/частичное сохранение:
   - не терять уже валидно сохранённые данные;
   - не зацикливать auth redirect;
   - не делать onboarding blocker из optional fields.

9. Analytics event contract подготовить/переиспользовать так, чтобы task product analytics мог измерять activation,
но не отправлять exact body values в ordinary telemetry.

10. Accessibility и mobile-first.

## Out of scope

Не делать 20-экранный quiz.
Не спрашивать все будущие preferences заранее.
Не добавлять AI.
Не делать Trainer onboarding частью обычного user flow.
Не добавлять wearables.
Не хранить дубли профиля ради onboarding.

## Проверки

New account; returning account; partially completed onboarding; already complete profile;
Web/TMA; refresh; auth callback next; invalid values; timezone; mobile keyboard; accessibility;
no redirect loop; no duplicate user/profile entities.

## Done when

Новый пользователь за короткий flow задаёт только необходимый минимум,
понимает следующий шаг и может начать пользоваться продуктом без лишнего friction.

## Рекомендуемый commit

`feat(onboarding): add progressive first-run flow`

## Процесс

Следовать корневому `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Все предыдущие tasks считаются выполненными.
Текущий код, Git history и актуальный `docs/` — source of truth по их результатам.

Не проводить повторный полный аудит репозитория.
Не перечитывать все предыдущие task-файлы.
Не читать весь `codex-backlog/masters/` без необходимости.

Если текущий task явно относится к одному master-документу,
прочитать только этот master.

Если предыдущий audit уже исследовал нужную область и результат доступен,
переиспользовать его; точечно перепроверять только факты, которые могли измениться.

Сначала прочитать текущий task, затем исследовать только релевантный набор файлов
и подсистем, необходимый для корректного выполнения задачи.

Если требуемая функциональность уже существует:
- не реализовывать её заново;
- переиспользовать текущую архитектуру;
- закрыть только реальные gaps.

Не расширять scope самостоятельно.

Если для выполнения нужен крупный architectural change вне scope:
- не начинать его автоматически;
- зафиксировать follow-up;
- выполнить безопасную часть текущего task, если возможно.

Работать только в текущей feature-ветке.

Не:
- создавать или переключать ветки;
- merge/rebase;
- deploy в production;
- переходить к следующему task.

После реализации:
1. только профильные проверки согласно `AGENTS.md`;
2. не запускать полный test suite без необходимости;
3. проверить `git diff`;
4. создать один логический commit при tracked changes;
5. краткий финальный отчёт: reused / changed / files / migrations-config / checks / follow-ups / commit hash.

## Plain-language onboarding requirement

Onboarding must not assume prior fitness knowledge.
Do not ask about unexplained `RIR`, deload, periodization, split jargon or advanced set types.
Training levels should be explained behaviorally. Equipment uses common Russian names.
A beginner must complete onboarding without external terminology lookup.
