# Your Fitness Coach - Premium Redesign

## Цель пакета

Поэтапно переработать UX/UI Your Fitness Coach так, чтобы:

- лендинг выглядел современно и убедительно;
- веб-приложение воспринималось как полноценный коммерческий продукт, а не набор форм и карточек;
- Telegram Mini App был действительно mobile-first;
- ключевые действия пользователя выполнялись быстрее и понятнее;
- интерфейс имел единый узнаваемый визуальный язык;
- дизайн выглядел современно, дорого и профессионально;
- анимации улучшали восприятие и обратную связь, а не мешали работе;
- текущая бизнес-логика, данные и права доступа были сохранены.

Целевое направление:

```text
premium sport-tech
graphite / warm neutral / lime
strong typography
clear hierarchy
fewer borders
fewer nested cards
purposeful motion
mobile-first interactions
```

## Почему задача разбита

Не отдавай Codex весь редизайн одним запросом.

Каждый файл ниже - самостоятельный этап, который можно выполнять в отдельной Codex-сессии.
Это уменьшает расход контекста и снижает риск, что Codex одновременно затронет слишком много экранов.

После каждого этапа изменения должны быть проверены и закоммичены.
Следующий этап начинает работу с уже изменённым репозиторием.

## Взаимодействие с Food + Training Platform и AI Coach

Если эти крупные функции ещё не объединены с основной веткой, рекомендуется:

1. выполнить `01_BASELINE_AUDIT_AND_TARGET_DESIGN.md`;
2. при желании выполнить `02_DESIGN_SYSTEM_FOUNDATION.md`;
3. затем объединить стабильные функциональные этапы Food + Training Platform и AI Coach;
4. продолжить с `03_APP_SHELL_AND_NAVIGATION.md`.

Причина: навигация, "Сегодня", питание и конечный UI должны проектироваться по актуальному набору функций.

Если Food/AI уже реализованы - учитывать их как часть текущего продукта.

## Порядок выполнения

| № | Файл | Результат |
|---|---|---|
| 01 | `01_BASELINE_AUDIT_AND_TARGET_DESIGN.md` | фактический UX/UI baseline и целевая модель |
| 02 | `02_DESIGN_SYSTEM_FOUNDATION.md` | единая дизайн-система и UI primitives |
| 03 | `03_APP_SHELL_AND_NAVIGATION.md` | новая оболочка и навигация |
| 04 | `04_TODAY_DASHBOARD.md` | главный экран "Сегодня" |
| 05 | `05_ACTIVE_WORKOUT_EXPERIENCE.md` | эталонный UX активной тренировки |
| 06 | `06_PROGRESS_EXPERIENCE.md` | прогресс, история и показатели |
| 07 | `07_PROGRAMS_AND_EXERCISES.md` | программы и каталог упражнений |
| 08 | `08_NUTRITION_PROFILE_AND_ACCOUNT.md` | питание, профиль и вторичные настройки |
| 09 | `09_COACH_WORKSPACE.md` | кабинет тренера |
| 10 | `10_TELEGRAM_MINI_APP_ADAPTATION.md` | Telegram-specific UX polish |
| 11 | `11_LANDING_PREMIUM_REFRESH.md` | улучшенный лендинг и motion |
| 12 | `12_RESPONSIVE_ACCESSIBILITY_AND_STATES.md` | responsive/a11y/interaction hardening |
| 13 | `13_PERFORMANCE_AND_MOTION_HARDENING.md` | производительность и motion hardening |
| 14 | `14_FINAL_UI_AUDIT_AND_REGRESSION.md` | независимый аудит и финальная регрессия |

## Как отдавать Codex

Для этапов создания/редизайна:

```text
$product-designer
$frontend-engineer

Выполни задачу из приложенного файла <имя файла>.
Следуй AGENTS.md.
Не переходи к следующим этапам.
После реализации проверь реальные экраны через Playwright и сделай отдельный commit.
```

Для этапа 01:

```text
$ui-audit
$product-designer

Выполни задачу из 01_BASELINE_AUDIT_AND_TARGET_DESIGN.md.
Код продукта не меняй.
```

Для этапа 14:

```text
$ui-audit
$qa-engineer
$code-reviewer

Выполни задачу из 14_FINAL_UI_AUDIT_AND_REGRESSION.md.
Исправь подтверждённые проблемы P0-P2 и повторно проверь результат.
```

## Правило контекста

В новую Codex-сессию достаточно передавать:

- один текущий task-файл;
- репозиторий;
- существующий `AGENTS.md`.

Не нужно каждый раз передавать все предыдущие task-файлы.
Источником истины по уже выполненным этапам являются текущий код и Git history.
