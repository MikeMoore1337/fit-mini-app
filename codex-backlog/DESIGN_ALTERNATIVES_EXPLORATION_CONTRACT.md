# Контракт исследования альтернатив дизайна после выполненных tasks 00-49

## Статус

Утверждённый Design V2 остаётся единственным production source of truth до явного решения владельца в task `49F` и закрытия task `49G`.

Tasks `49A-49G` не отменяют и не переигрывают выполненные tasks `00-49`. Они создают новый независимый цикл визуального исследования с учётом:

- актуального фактического продукта после task `49`;
- `.agents v4` и новых профильных skills;
- smartphone-first приоритета Mobile Web и Telegram Mini App;
- необходимости одинаково сильного Landing на desktop и mobile;
- отдельного качества `/login`, authenticated Web и TMA.

До owner approval запрещено менять production UI, общие tokens, маршруты и публичный Landing ради нового направления.

## Цель исследования

Подготовить и честно сравнить три новые цельные визуальные системы с текущим Design V2 как четвёртым baseline.

Новые направления должны отличаться не только цветом, radius или font weight, а всей системой:

- арт-дирекцией;
- типографикой;
- сеткой и композицией;
- плотностью;
- surface model;
- навигацией;
- представлением данных;
- product storytelling;
- mobile interaction model;
- motion principles.

## Обязательные поверхности

Каждое направление обязано показать одну согласованную систему для:

1. Public Landing.
2. `/login` и основные auth states.
3. Authenticated desktop Web.
4. Mobile Web.
5. Telegram Mini App как ту же mobile-композицию с Telegram adapter.

TMA не получает отдельную палитру, типографику, кнопки, карточки или feature components. Допустимы только реальные platform differences: safe area, content safe area, viewport, keyboard, BackButton, haptics, shell colors, initData и deep links.

## Обязательная матрица визуальных материалов

Для каждого из трёх направлений подготовить минимум шесть сравнительных boards:

1. `landing-desktop-light-dark` - 1440 px, обе темы, hero и ритм ключевых секций.
2. `landing-mobile-light-dark` - 390 px, обе темы, не сжатый desktop.
3. `login-desktop-mobile-light-dark` - 1440 и 390 px, provider, loading, error и continuation states.
4. `app-desktop-light-dark` - representative Today и data-rich surface, 1440 px.
5. `mobile-web-core-light-dark` - Today, active workout и fast nutrition на 390 px.
6. `tma-core-light-dark` - Today и active workout с safe area, BackButton и keyboard state на 390 px.

Дополнительно допустимы Progress, Coach workspace и другие экраны, если они помогают доказать устойчивость направления.

## Требования к Landing

### Desktop

Landing должен быть самостоятельно сильной desktop-композицией, а не растянутым mobile layout:

- убедительный hero без гигантской пустоты;
- один ясный primary CTA;
- реальный product proof;
- качественный ритм секций;
- понятная история для самостоятельного пользователя и тренера;
- хорошая композиция на `1440`, `1280`, `1024` и `768`;
- отсутствие шаблонного SaaS card-grid языка;
- factual SEO-friendly content и crawlable structure.

### Mobile

Mobile Landing должен быть самостоятельно спроектирован для `360`, `390` и `430`:

- в первом viewport понятны продукт, primary CTA и первое доказательство продукта;
- hero не занимает бессмысленно несколько экранов;
- product visuals читаемы, а не уменьшены до миниатюры;
- touch/no-hover navigation;
- отсутствие horizontal overflow;
- быстрый initial render, зарезервированные размеры изображений и отсутствие CLS;
- light/dark parity;
- понятный переход в Web, `/login`, Demo и TMA.

## Требования к `/login`

- public visual language согласован с Landing, но login не копирует его секционную структуру;
- provider actions понятны и удобны пальцем;
- mobile keyboard не перекрывает active field, error и primary action;
- loading, cancellation, provider unavailable, conflict, invalid state и return continuation показаны честно;
- valid TMA launch не показывает второй browser login;
- desktop не содержит лишней пустоты, mobile не превращается в тесную карточку внутри карточки.

## Требования к приложению и TMA

- client daily flows smartphone-first;
- главный и следующий шаг видны сразу;
- active workout удобен одной рукой между подходами;
- быстрый цифровой ввод и понятная синхронизация;
- bottom navigation, dialogs/sheets и sticky actions учитывают keyboard/safe areas;
- desktop Web использует пространство для подробной настройки и аналитики;
- Coach/Admin могут быть плотнее на desktop, но остаются визуально частью продукта;
- Mobile Web и TMA при одинаковом viewport визуально совпадают, кроме platform behavior.

## Factual и brand constraints

Обязательно:

- canonical logo и mark из task `07`;
- реальные названия функций и фактические product states;
- правдивые данные или явно помеченные fixtures;
- обе фирменные темы;
- отсутствие fake ratings, testimonials, usage numbers, prices, outcomes и несуществующих функций;
- отсутствие копирования идентичности Apple, Linear, Whoop, Oura, Fitness Online и других продуктов.

Разрешено переосмысливать нейтрали, геометрию, типографику, плотность, composition и характер использования lime. Смена canonical logo или brand promise не входит в scope.

## Accessibility и performance

Каждое направление оценивается до выбора по:

- contrast и color-independent meaning;
- touch targets;
- keyboard/focus;
- readable type scale;
- long content;
- reduced motion;
- image/font/animation cost;
- layout stability;
- feasibility в текущем React + TypeScript + Vite + CSS stack;
- отсутствию тяжёлой зависимости только ради визуального эффекта.

## Три направления

Task `49B` должен сформировать три действительно разные системы. Допустимые концептуальные опоры:

1. `Precision Performance` - точный, data-led, спортивно-технологичный и сдержанный.
2. `Editorial Coaching` - более человеческий, тёплый, типографичный и narrative-led.
3. `Kinetic Mobile Utility` - смелая иерархия, высокая ясность действий и mobile-first динамика без визуального шума.

Названия могут быть уточнены после `49A`, но различия должны оставаться системными.

## Owner decision branches

После task `49C` владелец выбирает ровно один путь:

- `KEEP_V2_UNCHANGED` - Design V2 остаётся без визуальных изменений; tasks `49D-49F` пропускаются, выполняется `49G` для закрытия gate.
- `APPROVE_V2_1_REFINEMENT` - выбираются только явно перечисленные изменения; обязательны `49D-49F`.
- `APPROVE_DIRECTION_A`, `B` или `C` - направление становится кандидатом; обязательны `49D-49F`.
- `APPROVE_EXPLICIT_HYBRID` - разрешён только конкретный список совместимых решений, а не произвольное смешивание; обязательны `49D-49F`.

Codex не выбирает направление за владельца и не трактует положительный комментарий как approval.

## Артефакты

До финального approval материалы хранятся в:

```text
.artifacts/design-alternatives/
```

После task `49F` утверждённая спецификация переносится в `docs/design/` только в том случае, если владелец явно одобрил V2.1 или новое направление.

## Out of scope

- повторная реализация features `00-49`;
- backend redesign;
- новая auth architecture;
- второй frontend;
- native mobile app;
- смена logo;
- rollout до owner approval;
- автоматическое принятие нового направления только потому, что появились новые skills.
