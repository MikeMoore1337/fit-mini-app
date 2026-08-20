# Landing - legacy visual references

Эти два файла использовались как historical input до утверждения Design V2:

- `references/landing/landing-reference-dark.png` - тёмная тема;
- `references/landing/landing-reference-light.png` - светлая тема.

Они больше не являются source of truth или acceptance reference по hero, cards, testimonials,
imagery, typography, section rhythm, geometry и composition. Канонический контракт задают
`DESIGN_V2_INTEGRATION_NOTES.md`, релевантные `docs/design/*v2*`, approved renders в
`docs/design/references/design-v2/` и фактическая shared Design V2 implementation.

Оставшиеся разделы этого документа описывают только исторический контекст. Их нельзя использовать
для возврата legacy UI или переопределения Approved Design V2.

Главная implementation task: `tasks/73-landing-premium-refresh.md`.

## Историческое визуальное направление

### 1. Общий характер

- современный premium sport-tech;
- чистая, уверенная композиция без декоративного шума;
- лаймовый акцент на нейтральной светлой/тёмной базе;
- большие зоны воздуха, чёткая типографическая иерархия;
- аккуратные тонкие borders/surfaces вместо тяжёлых теней;
- одинаковая структура бренда в light/dark, но не механическая инверсия цветов;
- визуально дорогой, но не «крипто/neon/gaming» стиль.

### 2. Header

Ориентир из референсов:

- canonical mark + `Your Fitness Coach` слева;
- компактная навигация по ключевым public sections;
- справа вторичная кнопка входа и один яркий primary CTA;
- на mobile - компактный доступный menu pattern без попытки сохранить desktop navigation в одну строку.

Конкретные пункты навигации определяются фактической public IA после tasks `03`, `06`, `09`, а не копируются с PNG буквально.

### 3. Hero

Композиционный ориентир:

- слева сильный двухстрочный headline;
- одна ключевая часть headline может быть выделена lime;
- короткий supporting paragraph;
- primary CTA + secondary Demo CTA;
- небольшая строка trust/value facts только из реально существующих условий продукта;
- справа - крупный real-product composition из desktop + mobile UI, а не абстрактная stock illustration.

Hero должен прежде всего объяснять ценность продукта: тренировки + питание + прогресс + работа с тренером в одной системе. AI Coach можно выводить в hero как доступную возможность только после фактического завершения AI block и проверки task `90/91`.

### 4. Быстрые capabilities под hero

Референс задаёт горизонтальный ряд компактных карточек/пунктов с line icons и коротким описанием.

Требования:

- 5-6 высокосигнальных возможностей максимум;
- использовать реальные возможности продукта;
- на narrow screens перестраивать в компактную responsive grid/scroll-safe layout;
- не превращать блок в десяток одинаковых карточек.

Возможные фактические категории после соответствующих tasks: питание/КБЖУ, тренировки, прогресс/замеры, пульсовые зоны/кардио если реально доступны, работа с тренером, уведомления.

### 5. Product showcase «Что умеет»

Ориентир - 4 крупных вертикальных product cards с реальными mobile screens:

- nutrition;
- workout/program flow;
- progress/measurements;
- trainer/client flow.

Использовать реальные screenshots/controlled product renders из текущего UI. Не генерировать фиктивные экраны, которые нельзя получить в продукте.

### 6. Для клиентов / Для тренеров

Референс задаёт заметный split-section с двумя value propositions.

Требования:

- самостоятельный пользователь и тренер - две полноценные аудитории;
- у каждой 3-5 конкретных выгод;
- trainer section не сводить к одной строке «можно работать с тренером»;
- фотографии людей допустимы только при наличии легального production source/licence; если такого источника нет, заменить на real-product visuals/нейтральную композицию, не тянуть случайные изображения из интернета;
- claims должны соответствовать реально завершённым trainer capabilities.

### 7. Demo CTA

Отдельная заметная горизонтальная секция, визуально близкая к референсу:

- Demo Mode как secondary conversion path;
- ясно сообщить, что регистрация для демо не нужна, только если это действительно так после tasks `62-68`;
- AI Coach в demo не вызывать и не имитировать как рабочий чат;
- один понятный CTA.

### 8. Platform section

Три смысловых блока как в референсе:

- Web;
- Telegram Mini App;
- adaptive/responsive experience.

Показывать один продукт на разных поверхностях, а не три независимых приложения.

### 9. Social proof

В референсах есть отзывы/рейтинги, но **они не являются разрешением придумывать пользователей, цитаты, оценки или число клиентов**.

До появления проверяемого social proof:

- либо блок полностью скрыть;
- либо заменить на factual proof block: возможности, privacy/security facts, supported platforms, открытое demo и т.п.;
- не использовать вымышленные имена, фотографии, звёзды и цитаты.

### 10. FAQ

- компактный accordion;
- вопросы основаны на реальных возражениях/условиях продукта;
- содержимое crawlable и доступно без сложного JS;
- keyboard/a11y semantics обязательны;
- не писать ответы про тарифы, подписку, AI, хранение данных или integrations, которых ещё нет/не утверждены.

### 11. Footer

Ориентир - аккуратный 3-4-column footer:

- canonical logo/brand;
- product links;
- company/legal links только если страницы существуют;
- support/contact links только реальные;
- social links только реальные;
- год/copyright не должен быть захардкожен ошибочно.

## Что НЕ копировать буквально из референсов

В PNG есть элементы, которые могут быть иллюстративными. Перед реализацией каждый такой элемент сверять с фактическим продуктом:

- `14 дней бесплатно`;
- `без привязки карты`;
- тарифы/цены;
- конкретные email/username;
- отзывы, имена, фото и звёздные рейтинги;
- конкретные цифры калорий/веса/пульса как marketing facts;
- формулировки про AI Coach до завершения AI tasks;
- ссылки/страницы, которых нет;
- любые screenshot details, которых нет в текущем product UI.

Исторические PNG не задают production visual system, rhythm, hierarchy или состав блоков.
Production content исходит из фактического продукта и SEO/public content source of truth, а
визуальное решение — из Approved Design V2.

## Связь с логотипом

Landing не создаёт новый logo. Используется canonical brand source из task `07`:

- light logo на светлой поверхности;
- dark logo на тёмной поверхности;
- favicon остаётся mark-only и не зависит от Landing implementation.

## Responsive contract

Референсы в первую очередь desktop-oriented. Реализация обязана быть самостоятельной на:

- 1440;
- 1280;
- 1024;
- 768;
- 390;
- 360.

Нельзя просто уменьшать desktop screenshot composition. На mobile:

- hero превращается в последовательный flow;
- product mockups не перекрывают CTA/text;
- capability row становится читабельной сеткой;
- client/trainer split становится вертикальным;
- FAQ/footer не требуют горизонтального скролла.

## Priority if sources disagree

Для Landing использовать такой приоритет:

1. фактический product behavior и security/privacy/auth/SEO/accessibility requirements;
2. Approved Design V2 в `docs/design/*v2*` и `docs/design/references/design-v2/`;
3. фактическая shared Design V2 implementation;
4. canonical logo/assets task `07`;
5. task `73` как implementation scope.

Этот документ, два legacy PNG и `masters/premium-redesign-master.md` остаются только historical
context и не переопределяют источники выше.
