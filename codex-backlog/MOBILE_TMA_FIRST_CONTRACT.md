# Mobile/TMA-first contract - release backlog v11

## Product priority

Для обычного пользователя и клиента тренера основной контекст использования Your Fitness Coach - смартфон:

```text
Mobile Web и Telegram Mini App - основные клиентские поверхности
Desktop Web - полноценная дополнительная поверхность
Coach/Admin - desktop-first там, где важны таблицы, массовые операции и подробный анализ
```

Это не означает отдельное мобильное приложение или отдельный TMA frontend. Web, Mobile Web и TMA используют общие backend, маршруты, доменные правила, Design V2 tokens и feature components.

Tasks `00-49B` завершены и не выполняются повторно. Current task `49B1` один раз проверяет и нормализует фактическую mobile/shared UI baseline текущего Design V2. После `49C-49G` task `50A` создаёт continuous quality gate для оставшихся задач. Task `76` позднее проводит ретроспективный release audit без повторения уже закрытого product-wide UI consistency pass.

## Обязательный gate для новых клиентских задач

Для каждой pending task, меняющей Today, тренировку, питание, Progress, Profile, Demo, Trainer/client flow или другой пользовательский сценарий на смартфоне:

1. Mobile Web является самостоятельной целевой композицией, а не уменьшенным desktop.
2. TMA переиспользует тот же UI и отличается только реальными platform APIs и runtime constraints.
3. Проверяются минимум `360x800`, `390x844`, `430x932`, touch input и отсутствие зависимости от hover.
4. Основные зоны нажатия практически удобны и не меньше 44x44 px, если меньший размер не обоснован семантикой элемента.
5. Нет необязательного горизонтального scroll.
6. Экранная клавиатура не перекрывает активное поле, primary action, ошибки и способ закрыть/отменить flow.
7. Fixed/sticky UI учитывает browser safe area и Telegram `safeAreaInset`/`contentSafeAreaInset` через общий adapter.
8. Theme, viewport, foreground/background, reload и временная потеря сети не уничтожают recoverable user state.
9. Light/dark, loading, empty, partial, error, offline, long-content и reduced-motion states входят в acceptance.
10. Новая функция добавляет или расширяет сценарий общего mobile/TMA smoke suite из task `50A`.

## TMA platform differences

Разрешены только обоснованные отличия:

- signed `initData` lifecycle;
- Telegram `BackButton`;
- safe area и content safe area;
- viewport/stable viewport и keyboard accommodation;
- shell colors;
- haptics;
- deep links и close/return behavior;
- platform buttons только при доказанной пользе.

Запрещены отдельные TMA palette, typography, component copies, feature logic, navigation language и Telegram-blue branding.

## Gym-context acceptance

Для сценариев тренировки учитывать реальную обстановку:

- управление одной рукой;
- короткие взаимодействия между подходами;
- отвлечение и частое сворачивание приложения;
- нестабильную сеть;
- повторное касание;
- ввод чисел без длинной формы;
- быстрое понимание текущего и следующего действия;
- отсутствие обязательного чтения длинных инструкций.

## Честность проверки

Mock TMA и браузерная эмуляция обязательны для автоматизации, но не заменяют реальный Telegram client. В отчёте всегда разделять:

- automated Mobile Web checks;
- mocked TMA adapter checks;
- real Android Telegram checks;
- real iOS Telegram checks;
- непроверенные среды и ограничения.

Нельзя заявлять real-device проверку, если она фактически не выполнялась.
