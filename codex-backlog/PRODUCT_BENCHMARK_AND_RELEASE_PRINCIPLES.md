# Product benchmark и принципы первого релиза

## Цель

Взять лучшие ежедневные механики зрелых приложений, но не переносить их социальные, коммерческие и инфраструктурные подсистемы без доказанной необходимости.

## Что берём

### Из Hevy / Strong

- быстрый workout logger, который не мешает тренировке;
- предыдущие фактические значения рядом с текущим подходом;
- одно очевидное завершение подхода;
- автоматический таймер отдыха;
- custom exercises;
- warm-up/drop/failure semantics и supersets как раскрываемые продвинутые функции;
- история упражнения, рекорды и понятный итог тренировки.

Официальные источники:
- https://www.hevyapp.com/
- https://www.hevyapp.com/features/workout-rest-timer/
- https://www.strong.app/

### Из MacroFactor

- быстрый ввод еды через recent/favorites/quick add;
- различение полного, частично заполненного и отсутствующего дня;
- компактная неделя для перехода между днями;
- единая недельная проверка, где выводы и изменение цели появляются только при достаточных данных и требуют подтверждения пользователя.

Официальные источники:
- https://help.macrofactorapp.com/en/articles/215-how-to-log-food-in-macrofactor
- https://help.macrofactorapp.com/en/articles/248-coaching-module-partial-logging
- https://help.macrofactorapp.com/en/articles/247-introduction-to-check-ins-and-coaching-modules

### Из FatSecret

- отчёты питания за период;
- средние значения и динамика;
- понятное разделение дневника и аналитики.

### Из Trainerize

- trainer/client context;
- персональные программы;
- обзор активности клиента;
- contextual feedback;
- weekly progress summary.

Не берём в первый релиз встроенные платежи, видеозвонки, групповые сообщества, challenge/leaderboard, полноценный messenger и team management.

Официальный источник:
- https://www.trainerize.com/features/

## Primary device strategy

- Personal/client daily flows are smartphone-first: Mobile Web and TMA.
- Desktop Web remains first-class for detailed analytics, program editing, Coach and Admin work.
- Shared frontend and Design V2 are mandatory; TMA is a platform adapter, not a separate product.
- A feature is not complete when desktop works but the equivalent 360/390 touch flow is broken.

## Неподвижные UX-принципы

1. Один экран - одно главное действие.
2. Новичок видит вес, повторы и завершение подхода; продвинутые поля раскрываются по необходимости.
3. Today отвечает «что делать сейчас», а не становится лентой уведомлений.
4. Progress, nutrition reports и downloadable report - одна информационная архитектура, а не три конкурирующих раздела.
5. Weekly check-in и adaptive calorie decision - один пользовательский процесс.
6. Missing data никогда не превращаются в ноль.
7. Trainer context всегда явно показывает имя клиента.
8. Mobile Web и TMA являются основными клиентскими поверхностями; TMA оптимизирован для быстрого возврата, тренировки, питания и итогов, а длинное чтение остаётся Public Web.
9. Ни один AI, news, translation или import workstream не является скрытой зависимостью релиза.
10. Функция включается в release scope только если усиливает ежедневный цикл и имеет проверяемый сценарий использования.

## Метрики успеха

Главные воронки:

- onboarding -> программа выбрана;
- Today -> тренировка начата;
- тренировка начата -> завершена;
- Nutrition -> запись добавлена менее чем за приемлемое число действий;
- Progress -> пользователь понимает изменение за период;
- Trainer -> клиент приглашён/связан -> программа назначена -> результат просмотрен;
- D7/D30 return;
- support/feedback доступен без блокировки core flow.
