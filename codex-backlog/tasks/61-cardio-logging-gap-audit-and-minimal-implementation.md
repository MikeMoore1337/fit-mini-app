# TASK 61. Cardio logging: gap audit и минимальная реализация при необходимости

- Фаза: **Training / Cardio**
- Приоритет: **61/93**
- Зависит от: `26`, `39`, `42`
- Рекомендуемая модель: **GPT-5.6 Sol High**

## Цель

Проверить, есть ли уже полноценный ручной cardio logging.
Если он существует — не дублировать.
Если есть реальный gap — закрыть минимальный сценарий до релиза без превращения YFC в Strava.

## In scope

1. Сначала провести narrow audit только cardio-related code:
   - exercise/cardio taxonomy;
   - planned workouts;
   - workout history;
   - adherence;
   - heart-rate zones;
   - Today/Progress;
   - current API/model/UI.

2. Если current implementation уже позволяет пользователю:
   - выбрать cardio type;
   - записать duration;
   - сохранить completed session;
   - увидеть историю;
   - учитывать её в adherence,
то ограничиться missing validation/UX/tests и не создавать новую subsystem.

3. Если gap подтверждён, минимальный manual cardio record:
   - type/activity;
   - duration;
   - distance optional;
   - average HR optional;
   - HR zone optional;
   - note optional;
   - planned/completed timestamp/status;
   - source = manual/current app.

4. Units:
   - duration;
   - km/miles according to existing unit conventions;
   - HR bpm validation.

5. Не требовать smartwatch/wearables.
Не считать machine/watch calories source of truth.

6. Не показывать MET пользователю.
Не вводить generic MET calorie-burn engine в КБЖУ.

7. Analytics:
   - cardio frequency/duration;
   - adherence;
   - optional HR zone time только если данные реально введены и модель это поддерживает.
Не смешивать strength volume и cardio metrics.

8. Web/TMA/mobile.

## Out of scope

Не делать GPS tracks.
Не делать route maps.
Не делать Strava clone.
Не добавлять Apple Health / Google Health / smartwatch integrations.
Не оценивать калории по псевдоточному generic MET calculation.
Не строить AI feature.

## Проверки

Audit proves existing path or identifies gap; create/edit/complete cardio;
duration validation; optional distance/HR; no wearables;
Today/history/adherence; Web/TMA; units; duplicate completion; privacy.

## Done when

До релиза есть понятный ручной cardio scenario либо документально подтверждено,
что существующая реализация уже его закрывает и новой subsystem не потребовалось.

## Рекомендуемый commit

`feat(cardio): close manual logging gaps`

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

## Plain-language cardio UX

Do not expose MET or implementation terminology.

Use:
- вид активности;
- длительность;
- дистанция;
- средний пульс;
- зона пульса.

Heart-rate zones need a concise explanation instead of assuming knowledge of zone numbers.
