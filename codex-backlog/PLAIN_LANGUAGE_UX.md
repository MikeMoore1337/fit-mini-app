# Plain-language UX — release contract

This is a release-wide language contract, not a separate feature.

## Principle

The default UI is beginner-friendly. Advanced terminology remains available for experienced users.

## Terminology

| Technical term | Default Russian UI |
|---|---|
| RIR | Повторы в запасе |
| working set | Рабочий подход |
| warm-up set | Разминочный подход |
| drop set | Дроп-сет |
| superset | Суперсет — два упражнения подряд |
| failure set | Подход до отказа |
| adherence | Соблюдение плана |
| progression | Увеличение нагрузки / прогрессия нагрузки |
| deload | Облегчённая неделя |
| training block | Тренировочный блок |
| primary muscle | Основная мышечная группа |
| secondary muscle | Дополнительная мышечная группа |
| data confidence | Достаточность данных |

## RIR control

```text
Повторы в запасе

Сколько повторов вы ещё могли бы сделать
с хорошей техникой?

0   Больше не смог бы
1   Ещё примерно 1 повтор
2   Ещё примерно 2 повтора
3   Ещё примерно 3 повтора
4+  Осталось много сил
```

`RIR` may be secondary: `Повторы в запасе (RIR)`.

## Beginner workout

Default:
```text
Вес
Повторы
Готово
```

Advanced:
```text
Дополнительно
  Повторы в запасе
  Тип подхода
  Суперсет
```

## Analytics

Bad:
```text
Training adherence: 83%
RIR coverage insufficient
Primary muscle exposure
```

Good:
```text
Выполнено 10 из 12 тренировок — 83%

Пока мало данных об интенсивности.
Повторы в запасе отмечены только в нескольких подходах.

Рабочие подходы по мышечным группам
```

## AI Coach

Use ordinary Russian by default. Mirror professional terminology only when the user's own language shows familiarity.

## Release test

A novice should be able to register, finish onboarding, choose a program, complete a workout,
understand a progression hint, log food, add measurements, read Progress and ask Coach a basic question
without external terminology lookup.
