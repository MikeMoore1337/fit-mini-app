# TASK 08. Единая тема YFC и синхронизация Web/TMA

- Фаза: **Design System / Platform UX**
- Приоритет: **08/93**
- Зависит от: `05`, `06`, `07`
- Выполнить после: **05 Design System** и **07 Brand logo/favicon**
- `05-06` уже могут быть выполнены - этот task не требует их отката или повторного выполнения.
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$frontend-engineer`, `$product-designer`, `$qa-engineer`

## Цель

Перейти к одному визуальному контракту Your Fitness Coach для обычного Web, Mobile Web и Telegram Mini App.

Нужны только две фирменные темы продукта:

```text
YFC Light
YFC Dark
```

Обе поверхности используют одинаковые semantic tokens, цвета, типографику, компоненты и визуальные состояния.
Telegram Mini App отличается платформенной интеграцией, а не отдельной палитрой или отдельным дизайном.

Не переделывать Design System с нуля. Переиспользовать primitives/tokens из task `05`, canonical logo/favicon из task `07` и нормализовать только theme/runtime contract.

## Главный контракт

```text
                         YFC Design System
                               |
                    +----------+----------+
                    |                     |
                 YFC Light             YFC Dark
                    |                     |
                    +----------+----------+
                               |
                    shared semantic tokens
                               |
                    shared components/layout
                               |
                  +------------+------------+
                  |                         |
                 Web                       TMA
          browser behavior          Telegram adapter
```

### Web

```text
ThemePreference = system | light | dark
```

`system` использует `prefers-color-scheme`.

### Telegram Mini App

Telegram сообщает текущий `colorScheme` (`light`/`dark`). Он выбирает соответствующую **фирменную YFC Light/YFC Dark**, а не перекрашивает приложение в Telegram palette.

```text
Telegram light -> YFC Light
Telegram dark  -> YFC Dark
```

`themeParams` не являются источником цветов feature-компонентов и не должны создавать отдельную Telegram design theme.

## 1. Перед началом

Проверить фактическую реализацию после tasks `05-07`:

- semantic color/surface tokens;
- root theme attributes/classes;
- `ThemeProvider`/hook/analog;
- `prefers-color-scheme`;
- local/session storage для UI preferences;
- Landing/public shell;
- `/login`;
- authenticated AppShell;
- Telegram WebApp/Mini Apps adapter;
- текущее использование `colorScheme`, `themeParams`, `themeChanged` или аналогов;
- tests around theme behavior;
- legacy platform-specific color variables/classes.

Если theme system уже существует, расширять её. Не создавать параллельный provider/theme store.

## 2. Shared YFC palette contract

Для каждого semantic token должен существовать один canonical value в `light` и один в `dark`, используемый и Web, и TMA.

Пример принципа, точные имена адаптировать к проекту:

```text
--color-bg
--color-surface
--color-surface-raised
--color-text
--color-text-muted
--color-border
--color-accent
--color-danger
--color-success
--color-focus
```

Запрещено создавать пары вида:

```text
--web-accent
--telegram-accent
--web-surface
--telegram-surface
```

только ради разных платформ.

Platform-specific token допустим только если он описывает реальную платформенную оболочку/геометрию, например safe area или Telegram shell color, а не внешний вид продуктового компонента.

## 3. Web preference

Для Web поддержать:

```text
system
light
dark
```

Default для нового пользователя:

```text
themePreference = system
```

В `system` effective theme следует browser/OS preference и обновляется runtime без reload.

При explicit `light`/`dark` системная смена не переопределяет выбор пользователя.

При возврате в `system` приложение снова следует `prefers-color-scheme`.

## 4. Web persistence

Web preference сохраняется между reload/browser sessions через существующий безопасный client preference layer или минимально через `localStorage`.

Не создавать backend table/column только ради темы.

Preference не зависит от auth и должна работать:

- на Landing;
- на `/login`;
- до входа;
- после входа;
- внутри authenticated App.

Cross-device theme sync не входит в этот task.

## 5. Initial theme и flash prevention

Не должно быть заметного flash:

```text
light -> dark
```

или обратного при cold load/direct navigation.

Определять effective theme настолько рано, насколько позволяет текущая frontend architecture, без смены framework/SSR только ради этой задачи.

Проверить минимум Landing, `/login`, `/app`.

## 6. Web theme selector

В обычном Web предоставить один понятный control:

- Системная;
- Светлая;
- Тёмная.

Использовать существующую Design System. Control должен быть keyboard accessible, иметь accessible name/selected state и не полагаться только на icon.

В TMA этот Web-selector по умолчанию не показывать: там effective theme приходит из Telegram `colorScheme`.

## 7. Telegram runtime contract

В корректно инициализированном TMA:

```text
Telegram colorScheme
        |
        v
light | dark
        |
        v
YFC Light | YFC Dark
```

Browser `prefers-color-scheme` не должен переопределять валидный Telegram `colorScheme`.

Пример:

```text
OS = dark
Telegram = light
=> TMA uses YFC Light
```

При изменении темы Telegram во время открытого Mini App приложение переключает YFC Light/Dark без потери состояния текущего экрана.

Перед реализацией проверить актуальный официальный Telegram Mini Apps API и supported event/mechanism.

## 8. Роль Telegram themeParams

Не использовать `themeParams` для отдельной продуктовой палитры.

Допустимо читать их только если это действительно нужно для:

- совместимости с конкретной версией Telegram API;
- безопасного определения light/dark fallback при отсутствии нормального `colorScheme`;
- интеграции с Telegram shell, если официальный API требует соответствующее значение.

Feature components, cards, buttons, forms, charts, badges и navigation получают цвета только из YFC semantic tokens.

Если legacy код сейчас маппит Telegram colors прямо в semantic product tokens - task должен аккуратно убрать это расхождение, не переписывая unrelated UI.

## 9. Telegram shell colors

Если текущий официальный API позволяет задавать background/header/bottom bar colors, синхронизировать оболочку Telegram с активной YFC theme через platform adapter.

Принцип:

```text
YFC effective theme
        |
        v
YFC semantic shell colors
        |
        v
Telegram background/header/bottom bar API
```

Не делать наоборот - Telegram shell palette не перекрашивает YFC components.

Если часть API недоступна в конкретном клиенте, graceful fallback без поломки интерфейса.

## 10. Mobile Web и TMA visual parity

При одинаковом viewport Mobile Web и TMA должны использовать:

- одну типографику;
- те же цвета;
- те же radii;
- те же cards/surfaces;
- те же buttons/fields;
- ту же визуальную иерархию;
- те же spacing rules;
- те же content states.

Допустимые различия TMA:

- safe-area offsets;
- viewport/keyboard accommodation;
- Telegram BackButton/MainButton/SecondaryButton там, где их использование подтверждено UX;
- haptics;
- auth/initData lifecycle;
- Telegram deep links/navigation behavior;
- shell/header/bottom-bar integration.

Desktop Web может иметь другую responsive-композицию (sidebar/rail, более широкие data layouts), но остаётся той же Design System.

## 11. Brand assets

Использовать только canonical light/dark logo variants из task `07`.

Не создавать Web-logo и Telegram-logo как разные бренды.

Favicon не менять, кроме проверки theme-aware поведения, если оно уже предусмотрено task `07`.

## 12. State ownership

Не смешивать:

```text
persisted Web ThemePreference
```

и

```text
runtime Telegram effective theme
```

TMA theme не сохранять как manual Web preference.

Открытие TMA не должно менять сохранённый Web choice пользователя.

## 13. Fallback вне Telegram

Если Telegram adapter запущен вне реального Mini App/в тестовом окружении:

1. использовать явный mock/test contract, если он есть;
2. иначе безопасно определить light/dark через существующий fallback;
3. не записывать fallback как user Web preference;
4. не создавать отдельную Telegram palette.

Normal TMA path и fallback должны быть различимы в коде и тестах.

## 14. Out of scope

Не делать в этом task:

- полный редизайн экранов;
- отдельный Telegram frontend;
- отдельную Telegram palette;
- Telegram-specific copies общих components;
- backend preference storage;
- sync темы между аккаунтами/устройствами;
- изменение auth/business logic;
- большой CSS refactor unrelated legacy styles;
- новую animation/UI framework.

## 15. Проверки

Проверить профильными unit/component/e2e tests, typecheck/lint/build согласно `AGENTS.md`.

Минимальная visual/runtime matrix:

### Web

```text
new user + system light -> YFC Light
new user + system dark  -> YFC Dark
manual light + OS dark  -> YFC Light
manual dark + OS light  -> YFC Dark
system + runtime OS change -> updates without reload
reload -> manual preference preserved
```

### TMA

```text
Telegram light -> YFC Light
Telegram dark  -> YFC Dark
Telegram runtime light<->dark -> YFC theme updates without losing screen state
TMA does not expose conflicting Web manual selector
legacy Telegram palette does not leak into feature components
```

### Parity

На 390/360 px сравнить representative Mobile Web и mocked/realistic TMA render:

- same YFC light palette;
- same YFC dark palette;
- same component geometry/typography;
- differences limited to documented platform behavior/safe areas.

Если реальный Telegram client недоступен, тестировать adapter/mocks и прямо указать это в отчёте.

## Done when

- существует один shared YFC Light/Dark visual system для Web и TMA;
- Web поддерживает `system/light/dark` с persistence и runtime system updates;
- TMA использует Telegram `colorScheme` только для выбора YFC Light/Dark;
- `themeParams` не формируют отдельную продуктовую palette;
- Mobile Web и TMA визуально совпадают в рамках одной Design System;
- Telegram-specific код ограничен platform adapter/behavior;
- canonical logo variants переключаются корректно;
- нет заметного initial theme flash и конфликтующих theme sources.

## Рекомендуемый commit

`refactor(ui): unify web and telegram theme system`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, реально запущенные проверки, ограничения и commit hash.
