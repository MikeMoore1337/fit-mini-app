# Task 115A — решения и варианты прототипа

Clickable prototype: `prototype/index.html`. Он изолирован от production React/CSS/API и использует
product-shaped static data. Переключатели позволяют сравнить direction, screen, theme и
Mobile/TMA/Desktop frame. `prototype/compare.html` показывает один state сразу в трёх колонках
`Command Stack / Day Rail / Signal Grid` для прямого owner comparison.

## Визуальная выдержка и источник иконок

- Все три направления используют одну сдержанную брендированную основу: lime как единственный
  активный акцент, black/white для контраста и близкие green/neutral оттенки для семантических
  групп. Цвет не является единственным носителем смысла.
- Иконки не рисовались специально для прототипа. `prototype/approved-icons.js` содержит необходимый
  subset утверждённого production-пака из `frontend/src/shared/ui/Icon.tsx` и выборочные официальные
  Lucide glyphs для отсутствующей или двусмысленной семантики. Все они нормализованы к общей сетке
  `24 px`, `currentColor` и stroke `1.8`; источники зафиксированы в
  `prototype/THIRD_PARTY_NOTICES.md`.
- Emoji, Unicode-псевдоиконки и внешние непроверенные ассеты в screenshot-пакете не используются.

### Контракт бренд-связанности

При будущем owner-approved переносе направление должно применяться ко всему клиентскому продукту
как система, а не как набор локальных акцентов. Primary actions и реальные selected/active states
используют общие lime/black/white tokens; neutral surfaces не получают случайный accent, а
error/warning/success могут отступать от ядра только по понятной семантической причине. Light и
dark theme меняют поверхности и основной текст, но не смысл цветового состояния. Локальные
инверсии вроде чёрного selected-day в light и белого в dark не допускаются, если они не выражают
отдельную семантику.

### Аудит иконок после owner feedback

Принято выборочное обновление вместо тотальной смены pack:

| Поверхность                                   | Решение                      | Обоснование                                                                          |
| --------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------ |
| `Сегодня`                                     | оставить YFC `nav-today`     | календарь однозначен и читается на 20–24 px                                          |
| `Программа`                                   | Lucide `ClipboardList`       | отделяет программу от календаря `Сегодня`; передаёт структурированный план           |
| `Питание`                                     | оставить YFC `nav-nutrition` | упрощённая миска/лист читается лучше более детального `Salad` в taskbar              |
| `Прогресс`                                    | оставить YFC `nav-progress`  | bars + trend точно передают динамику; альтернативный Lucide не проще                 |
| Profile/avatar                                | оставить YFC `nav-profile`   | стандартная, нейтральная и хорошо центрированная семантика пользователя              |
| `Цели и параметры`                            | Lucide `SlidersHorizontal`   | параметры вместо ошибочного повторного использования иконки программы                |
| `Тренер и приглашения`                        | Lucide `UserRoundPlus`       | понятнее сложного person + chat glyph на малом размере                               |
| `Уведомления`                                 | Lucide `Bell`                | исправляет семантическую ошибку календаря                                            |
| `Доступ и безопасность`                       | Lucide `ShieldCheck`         | безопасность аккаунта без ложного состояния «доступ запрещён»                        |
| Barcode                                       | Lucide `Barcode`             | прямое соответствие действию сканирования                                            |
| Вес, пульс, силовая, timer и generic controls | оставить YFC subset          | точная domain-семантика либо общеизвестные controls без обнаруженной неоднозначности |

Для lime action surfaces введён invariant `--on-lime: #0c100d`: текст и иконки остаются почти
чёрными и в light, и в dark theme. Это касается `.primary`, выбора результата поиска,
завершения подхода и других lime controls; цвет больше не зависит от browser `ButtonText`.

В списке `Аккаунт и настройки` все пять пунктов имеют одинаковую нейтральную подачу: иконки без
accent background, светлые в dark theme и тёмные в light theme. Лайм не используется для одного
пункта без реального selected/active состояния; это сохраняет единство и не создаёт ложную
приоритетность `Цели и параметры`.

Taskbar намеренно содержит только четыре locked target-IA пункта: `Сегодня`, `Программа`,
`Питание`, `Прогресс`. Пункт `Ещё` не пропущен: account identity и secondary settings открываются
через постоянный avatar entry point в AppShell, а contextual/detail capabilities — из своих
родительских разделов. Возвращать catch-all `Ещё` без новой owner IA decision не требуется.
Кликабельный avatar entry point имеет постоянный lime-контур `2px`: это спокойный affordance
перехода в профиль без ложного notification badge, glow или дополнительного пятого пункта taskbar.
Lime-заливка по-прежнему зарезервирована для primary actions и реальных selected/active состояний.

В WeekStrip выбранная дата использует сплошной lime-фон и чёрный `--on-lime` текст в обеих темах.
Если пользователь выбрал другой день, текущая календарная дата сохраняет только тонкий
lime-контур: заливка однозначно означает selection, а контур — today reference.

## Direction A — Command Stack (рекомендация)

**Идея:** один выразительный current-action hero, под ним спокойный вертикальный stack compact
summaries. Это наиболее прямое продолжение сильных current contracts и лучший вариант для зала.

- Отличие: action-first composition, минимум scanning перед действием.
- Сильные стороны: ясный primary action; легко применить state-first; хорошо работает 360/TMA;
  semantic wow сосредоточен на hero/summary.
- Стоимость: для data-rich Progress нужен отдельный detail слой; desktop требует column reflow.
- Motion: короткая state transition hero -> active operation; summaries без постоянной анимации.
- Сложность реализации: средняя; можно мигрировать экран за экраном поверх current domain/API.

## Direction B — Day Rail

**Идея:** день как вертикальная временная rail: сейчас, далее, итог. Quick actions привязаны к
моменту дня, а не к категории продукта.

- Отличие: chronological interaction model вместо card/category stack.
- Сильные стороны: хорошо объясняет `что сейчас`; удобно для returning user с расписанием.
- Риски: nutrition/progress могут казаться второстепенными; empty/new user rail становится
  искусственной; сложнее переносить на Program/Profile.
- Motion: позиция `Сейчас` перемещается по rail; reduced-motion сохраняет статичный marker.
- Сложность: выше средней из-за day/time prioritization и большого числа state combinations.

## Direction C — Signal Grid

**Идея:** compact bento/grid собирает важные сигналы и quick actions; primary action закреплён как
крупная action tile.

- Отличие: information-dense scan и data representation вместо линейного flow.
- Сильные стороны: выразительный Progress и сильный desktop; много полезного помещается без длинной
  ленты.
- Риски: новый пользователь может не понять порядок; tiles конкурируют; 360 px требует строгой
  приоритизации и легко превращается в dashboard ради dashboard.
- Motion: controlled metric transitions; никаких декоративных loops.
- Сложность: высокая из-за responsive grid и semantic tile system.

## Спорные flow alternatives

### First run

- A: Today empty hero с `Создать программу` + 2 secondary quick actions — **рекомендация**.
- B: три equal intent cards без hero — лучше нейтральность, хуже одно primary action.

### Program creation

- A: dedicated 3-step flow `Основа -> День -> Проверка` — **рекомендация**.
- B: template-first choice (`Готовая`, `Своя`, `Подбор`) — быстрее для части пользователей, но
  требует раннего решения модели.

### Progress hierarchy

- A: one conclusion + category summaries — **рекомендация** для low-data и mobile.
- C: bento signals — сильнее при достаточных данных; использовать внутри Task 111 после semantic
  system, не как универсальный empty-state.

## Recommendation

Выбрать `Command Stack` как target IA/composition. Взять из `Signal Grid` только desktop Progress
reflow и bento при достаточных данных. `Day Rail` оставить как возможный local pattern для Today
schedule, но не как глобальную архитектуру.

## Owner decision — approved

Owner decision от 30.08.2026: `SELECT_COMMAND_STACK`. Владелец явно одобрил Direction A и разрешил
зафиксировать prototype package одним commit. Вместе с направлением выбраны:

1. First run: direct Today empty hero без обязательного onboarding wizard.
2. Program: базовый 3-step own-program flow `Основа -> День -> Проверка`.
3. Progress: conclusion-first; detail и data-rich bento открываются по intent и достаточности данных.
4. Visual material: restrained sport-paper с общей lime/black/white бренд-системой в light/dark.
5. AppShell: четыре locked nav item; Profile/settings открываются через обозначенный avatar entry point.

`Day Rail` и `Signal Grid` остаются comparative evidence, но не являются выбранной глобальной
архитектурой. Отдельные data-rich bento patterns могут быть рассмотрены Task 111 внутри выбранной
Progress hierarchy.

Этот owner checkpoint завершает Task 115A и разрешает commit design package, но не меняет
production baseline и не разрешает release/production rollout. До отдельной реализации и активации
в будущих tasks действует `DESIGN_V2_1`.
