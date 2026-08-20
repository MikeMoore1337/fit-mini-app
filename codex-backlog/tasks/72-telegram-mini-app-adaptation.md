# TASK 72. Telegram Mini App - platform integration и hardening

- Фаза: **Platform integration / polish**
- Приоритет: **72/93**
- Зависит от: `08`, `12`, `13`, `14`, `36`, `38`, `39`, `40`, `41`, `42`, `43`, `44`, `46`, `47`, `48`, `49`, `50`, `51`, `52`, `53`, `54`, `55`, `58`, `59`, `59A`, `60`, `61`, `68`, `71A`
- Рекомендуемый reasoning: **High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

После появления основных экранов провести один финальный Telegram Mini App pass как **платформенную интеграцию общего Your Fitness Coach UI**, а не отдельный редизайн.

Перед UI-работой прочитать `codex-backlog/DESIGN_V2_INTEGRATION_NOTES.md`, релевантные `docs/design/*v2*` и проверить фактическую shared Design V2 реализацию в Mobile Web. Утверждённый visual language не менять без отдельного owner checkpoint.

Главный принцип:

```text
Approved Design V2 shared UI
+ responsive mobile layout
+ Telegram platform adapter
= Telegram Mini App
```

Mobile Web и TMA должны выглядеть как один продукт. Отличаются только те детали, которые реально продиктованы Telegram runtime/API.

## In scope

Проверить и при необходимости исправить:

- signed `initData` auth continuity;
- Telegram `colorScheme` -> shared YFC Light/Dark contract из task `08`;
- runtime theme change без потери screen state;
- Telegram shell background/header/bottom-bar integration с цветами активной YFC theme, если это поддержано актуальным официальным API;
- safe areas/content safe areas;
- viewport resize;
- mobile keyboard и forms;
- shared bottom navigation;
- Telegram BackButton и nested navigation;
- MainButton/SecondaryButton только там, где они реально улучшают UX и не дублируют понятный shared control;
- умеренные haptics для подтверждённых product events;
- dialogs/modals/sheets;
- deep links и возврат из вложенных flows;
- workout/offline recovery;
- nutrition/search/barcode forms;
- Progress/Programs/Exercise Guide;
- trainer application submit/status/withdraw/resubmit flow из task `71A`;
- trainer/contextual comments/knowledge;
- check-in/adaptive calories/workout adaptation/program history/anthropometry;
- notifications/deep links;
- account export/delete UX where permitted;
- manual cardio;
- Demo -> Telegram continuation/auth boundary;
- существующий AI entry/locked state, если он уже присутствует; полный AI Coach UI из task `90` обязан наследовать этот platform contract;
- compact performance на реальном mobile-size viewport.

Если TMA показывает logo/brand mark, использовать canonical assets task `07`.

## Единый визуальный контракт

Запрещено создавать для TMA отдельные:

- color palette;
- typography scale;
- button/card/input styling;
- radii/shadows;
- feature-component copies;
- product navigation language.

При одинаковом viewport representative Mobile Web и TMA должны иметь одинаковые YFC colors/components/spacing/hierarchy.

Равенство включает semantic colors, typography, geometry, icon family, controls, forms, data/exercise regions и active-navigation language. Platform API не является основанием для локальных visual variants.

Допустимые Telegram-specific различия:

- safe-area padding;
- viewport/keyboard accommodation;
- Telegram BackButton;
- platform shell colors;
- haptics;
- platform buttons, только если они уместны;
- auth/initData lifecycle;
- Telegram deep-link/close behavior.

Desktop Web responsive composition не обязана совпадать с mobile/TMA.

## Theme contract

Не возвращать старую схему `Telegram themeParams -> product palette`.

Canonical rule из task `08`:

```text
Telegram light -> YFC Light
Telegram dark  -> YFC Dark
```

`themeParams` допустимы только как platform/fallback compatibility detail, если это подтверждено актуальным official Telegram API. Feature components получают цвета из YFC semantic tokens.

Web theme selector внутри TMA не показывать, если он создаёт конфликт с Telegram `colorScheme`.

## Auth continuity

Valid Telegram launch:

```text
signed initData -> automatic auth -> app
```

Не добавлять второй browser login screen.

Telegram browser OAuth/linking и TMA identity должны сходиться в один internal account согласно auth tasks.

## Navigation

BackButton не должен конфликтовать с browser/history routing.

Shared bottom nav из task `38` остаётся основой mobile IA. Не заменять её Telegram controls без доказанной UX-причины.

Fixed/sticky UI учитывает safe area и keyboard.

## Haptics

Использовать умеренно и только для понятной обратной связи, например:

- set complete;
- успешное подтверждение;
- warning/error where appropriate.

Не добавлять haptics на каждое обычное нажатие.

## Проверки

Использовать реальный Telegram client, если это доступно и воспроизводимо. Если нет - проверять platform adapter через mock `initData`, `colorScheme`, safe-area/viewport events и не заявлять реальную client-проверку.

Минимум:

- TMA light -> YFC Light;
- TMA dark -> YFC Dark;
- runtime theme change;
- 390/360 visual parity с Mobile Web;
- safe areas;
- bottom nav;
- nested BackButton;
- keyboard/forms;
- active workout/offline recovery;
- nutrition;
- Progress/Programs;
- trainer application flow и approved Coach entry;
- trainer flows;
- Demo auth continuation;
- существующий AI entry/locked state без отдельной TMA styling;
- notification/cardio/account flows;
- browser mode regression.

Representative states проверять в реальном браузере в обеих темах; реальную проверку Telegram client заявлять только если она фактически выполнена.

Запустить связанные unit/component/e2e adapter tests, typecheck/lint/build согласно `AGENTS.md`.

## Out of scope

Не делать:

- Telegram-only frontend tree;
- отдельный TMA redesign;
- отдельную Telegram product palette;
- массовые Telegram-specific component forks;
- Telegram-blue branding;
- bot logic changes без необходимости;
- использование Telegram API там, где shared UI проще и лучше.

## Done when

- TMA использует тот же YFC Light/Dark visual system, что Mobile Web;
- Telegram-specific различия ограничены platform behavior/integration;
- auth/initData, BackButton, safe areas, keyboard, viewport и deep links работают согласованно;
- theme switching выбирает YFC Light/Dark, а не перекрашивает продукт в Telegram colors;
- representative Mobile Web/TMA screens визуально согласованы;
- нет второго frontend или конфликтующих component variants;
- основные product flows usable в TMA.

## Рекомендуемый commit

`feat(telegram): harden shared ui platform integration`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Работать в текущей feature-ветке, не merge/deploy. Не переходить к следующему task. После изменений запустить только профильные проверки, проверить diff и создать один логический commit. В финальном отчёте перечислить изменения, ключевые файлы, реально запущенные проверки, ограничения и commit hash.

## Plain-language parity

TMA использует те же beginner-friendly labels и объяснения, что Web. Не заменять понятные названия английскими сокращениями только ради экономии места.
