# Task 115A — план post-release usability validation для Task 124B

## Решение, на которое влияет исследование

Подтвердить или отклонить UX reset как production default: fixed IA, direct first run, simple
Program creation, active workout hierarchy, food picker и Progress summary. Результат определяет
release acceptance либо bounded remediation Task 124C.

Сессии ещё не проводились. Ниже план, а не пользовательские findings.

## Аудитории

| Сегмент               | Минимальный контекст                              | Primary surface                     |
| --------------------- | ------------------------------------------------- | ----------------------------------- |
| Beginner self-user    | тренируется < 1 года, нет сложного logger habit   | smartphone Mobile Web/TMA           |
| Experienced self-user | регулярно логирует силовые                        | smartphone, gym context             |
| Nutrition logger      | считает питание хотя бы несколько дней в неделю   | smartphone                          |
| TMA-first             | обычно возвращается через Telegram                | отдельно Android/iOS                |
| Trainer/client        | только если release scope затронул client context | desktop trainer + client smartphone |

Не смешивать platform results. Реальные участники, sample size и вознаграждение определяются
владельцем до recruitment; проценты заранее не назначаются.

## Production-safe test data

- отдельные test accounts/fixtures, никаких чужих production данных;
- synthetic program, foods, measurements и trainer relationship;
- не просить реальные health notes, фото тела, точные медицинские сведения;
- запись экрана/голоса только по consent, срок хранения и доступ объявляются заранее;
- Telegram initData/token/logs не попадают в материалы;
- созданные записи маркируются тестовыми и удаляются по согласованной процедуре без воздействия на
  реальные аккаунты.

## Goal-based scenarios

1. **First value:** `Вы только вошли и хотите начать пользоваться приложением. Покажите, что бы вы
сделали первым.` Success: без обучения выбирает релевантный intent и понимает, что профиль можно
   заполнить позже.
2. **Own program:** `Составьте простую программу на три тренировки и добавьте жим лёжа в первый
день.` Success: находит Program, создаёт program и сохраняет без обращения к advanced settings.
3. **Start/log workout:** `Сегодня тренировка. Начните её и отметьте первый подход.` Success: видит
   current set, вводит weight/reps, завершает один раз; ошибочный double tap не дублирует.
4. **Interruption:** background/return + краткий offline во время второго set. Success: draft
   сохраняется, recovery понятен, нет повторного save.
5. **Cardio:** `Добавьте сегодняшнюю прогулку/кардио.` Success: planned/completed/factual semantics
   понятны, strength fields не появляются.
6. **Food by name:** `Добавьте продукт, которого нет среди недавних.` Success: search -> result ->
   amount -> meal; provider state понятен.
7. **Barcode:** `Добавьте продукт по штрихкоду; если камера недоступна, восстановитесь вручную.`
   Success: barcode entry находится первым, manual fallback доступен над keyboard.
8. **Progress:** `Расскажите, что изменилось за период и чего не хватает для вывода.` Success:
   участник не трактует missing как zero и находит detail.
9. **Settings:** `Измените время уведомления и вернитесь к Сегодня.` Success: Profile/Notifications
   находится предсказуемо, Save semantics понятны.

## Наблюдаемые показатели

- outcome: success / partial / fail;
- critical error, unintended destructive action, duplicate submit;
- запрос помощи и момент подсказки;
- фактический path и лишние переходы;
- observed hesitation с evidence timestamp;
- time on task только описательно при одинаковых условиях;
- confidence после задачи;
- восстановление после keyboard, BackButton, background, network interruption.

## Moderator guide

1. Нейтральное вступление: тестируем продукт, не участника.
2. Consent на запись, перечень данных и право остановиться.
3. Короткий warm-up о реальном способе тренироваться/вести питание.
4. Читать scenario без названий кнопок; не обучать во время выполнения.
5. Нейтральные probes: `Что вы ожидаете?`, `Что сейчас произошло?`, `Куда бы вы пошли дальше?`.
6. После каждой задачи: уверенность и самое непонятное место.
7. Debrief: сравнение ожиданий до/после, не вопрос `нравится ли` как единственный signal.

## Observation template

```text
Session ID / segment / platform / device
Scenario ID
Outcome: success | partial | fail
Observed path:
Critical error/help:
Keyboard/safe-area/BackButton/network behavior:
Evidence timestamp:
Exact quote (only from recording):
Observation:
Interpretation:
Risk:
Confidence:
```

## Decision rubric

- `GO`: обязательные journeys выполняются без критической подсказки; нет data-loss/cross-user/
  duplicate-action риска; platform-specific blocking findings отсутствуют.
- `BOUNDED_FIX`: hierarchy понятна, но один локальный interaction создаёт повторяемую проблему;
  scope помещается в Task 124C без новой IA/API/schema.
- `NO-GO`: first value, Program creation, workout logging, food add или honest Progress не
  выполняется; либо keyboard/TMA lifecycle создаёт потерю/неверное действие.

Findings связываются с evidence IDs. Малую выборку описывать как `N из M`, не как долю рынка.
