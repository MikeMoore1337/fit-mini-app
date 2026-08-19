# Продуктовая аналитика без чувствительных данных

## Назначение и границы

Frontend использует единый provider-neutral контракт `yfc:product-event`. Контракт позволяет
последовательно измерять продуктовые воронки, но не включает внешний analytics SDK, cookies,
session replay, BI-хранилище или сетевой транспорт. Реальная инструментация основных сценариев
отложена до task 57; сейчас onboarding — единственный подключённый продуктовый flow.

Source of truth находится в
`frontend/src/shared/analytics/productEvents.ts`. Provider подключается через
`subscribeProductAnalyticsProvider()` и не участвует в бизнес-логике приложения.

## Контракт события

Каждое прошедшее runtime-валидацию событие получает envelope:

```json
{
  "name": "workout_completed",
  "surface": "web",
  "schema_version": 1,
  "environment": "production",
  "occurred_at": "2026-08-19T10:00:00.000Z"
}
```

Поддерживаемые группы событий:

- landing: `landing_viewed`, `landing_demo_selected`, `landing_login_selected`;
- demo: `demo_started`, `demo_login_selected`;
- auth: `login_started`, `login_completed`;
- onboarding: `onboarding_started`, `onboarding_minimum_saved`,
  `onboarding_next_action_selected`;
- program: `program_recommendation_started`, `program_recommendation_completed`,
  `program_activated`;
- workout: `workout_started`, `workout_completed`;
- журнал: `food_logged`, `measurement_logged`, `check_in_logged`.

Только `onboarding_next_action_selected` имеет дополнительное поле `next_action` с закрытым
списком значений. Любое неизвестное имя, поле или значение отклоняется до публикации события и
повторно проверяется на provider boundary. Изменение смысла или структуры существующего события
требует новой `schema_version`; добавление нового allowlisted имени без изменения envelope может
оставаться в текущей версии.

## Privacy-инварианты

В payload запрещены:

- названия, состав и текстовые описания еды;
- точный вес, окружности и другие измерения;
- калории и точные БЖУ;
- комментарии тренера и другой свободный пользовательский текст;
- тексты AI-диалогов;
- access/refresh tokens, Telegram `initData`, secrets;
- user/client/session ID, URL, query string и другие raw identifiers.

Контракт принимает только заранее перечисленные события и короткие enum-значения. Foundation не
создаёт cookie, fingerprint, anonymous ID или запись в `localStorage`/`sessionStorage`. Dedupe с
режимом `session` хранит в памяти только ключ из версии, среды, surface и имени события; он не
содержит идентификатор пользователя. События действий, которые допустимо повторять, по умолчанию
не дедуплицируются.

`environment` определяется Vite mode и принимает только `production`, `staging`, `development`
или `test`; неизвестный mode безопасно становится `development`. Provider подписывается только на
свою среду, поэтому test/dev события не отправляются в production sink. Ошибка provider не ломает
пользовательский сценарий и публикуется локально как `yfc:product-analytics-status` без исходной
ошибки или event payload.

## Gate перед подключением provider

Этот раздел фиксирует инженерный decision gate, а не юридическое заключение. На 19 августа 2026
года проверены актуальные официальные источники:

- [Федеральный закон № 152-ФЗ «О персональных данных»](https://ips.pravo.gov.ru/api/ips/legislation/document?baseid=None&hash=98490812b3409e2a8d78a11ca9010f434ea3d9250a11dbbdb78690cd5551bdd6)
  требует определить цель и основание обработки, соблюдать минимизацию и конфиденциальность;
  если основанием является согласие, оператор должен доказать его получение, а согласие должно
  быть конкретным, информированным, однозначным и оформленным отдельно; статья 22 этого же закона
  требует до начала обработки проверить обязанность уведомить Роскомнадзор;
- для пользователей, на которых распространяются нормы ЕС,
  [GDPR](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) закрепляет
  purpose limitation, data minimisation и необходимость документированного lawful basis;
- [ePrivacy Directive, Article 5(3)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32002L0058)
  требует ясной информации и права отказаться от необязательного хранения или доступа к данным
  на устройстве; конкретная реализация зависит от применимого национального права.

До production-подключения provider владелец вместе с профильным юристом должен:

1. определить применимые юрисдикции, цели и lawful basis отдельно для public и authenticated
   surfaces;
2. проверить статус оператора, уведомления, локализацию баз и возможную трансграничную передачу;
3. проверить provider как обработчика: данные, серверные регионы, sub-processors, retention,
   удаление, договорные условия и запрет рекламного переиспользования;
4. обновить privacy/cookie notice и настроить доказуемый consent/withdrawal flow, если он нужен;
5. не загружать provider и не отправлять события до выполнения этого gate.

Наличие безопасного технического payload само по себе не отменяет требования к правовому
основанию, прозрачности, срокам хранения и правам пользователя.
