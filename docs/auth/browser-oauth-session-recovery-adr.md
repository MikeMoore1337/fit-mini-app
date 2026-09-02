# ADR: server-side browser OAuth transactions

Статус: accepted for Task 136

## Контекст

Authlib и Starlette `SessionMiddleware` раньше хранили state, redirect URI,
PKCE verifier, OIDC nonce и общий login/link-контекст в подписанной cookie
`fit_oauth_session`. Повреждённая или устаревшая cookie могла остаться в
браузере после `invalid_state`, а кнопка «Повторить» только перезагружала
страницу с тем же артефактом.

## Решение

Вводится таблица `oauth_transactions` с bounded TTL по умолчанию 600 секунд.
Запись содержит:

- opaque transaction id, hash browser marker, provider, purpose (`login` или
  `link`), state, redirect URI, safe `next`, timestamps и one-time status;
- server-side PKCE verifier и OIDC nonce при наличии;
- для link flow — hash action token, target user и исходную refresh session
  family.

`fit_oauth_session` остаётся подписанной HttpOnly-cookie с тем же именем,
`Path=/`, production `Secure; SameSite=None` и тем же bounded TTL. В её payload
остаётся только opaque browser marker. State, verifier, nonce, raw action token
и link metadata в cookie не записываются.

На start создаётся новая независимая transaction. Второй tab не supersede-ит
первую запись: каждый callback должен предъявить exact state, provider и marker.
На callback transaction сначала переводится из `pending` в `processing`; только
после этого Authlib или VK выполняет code exchange, PKCE и проверки OIDC/VK.
Повторный, неизвестный, просроченный или mismatching state не запускает обмен и
не выполняет identity write.

Успешный login помечает transaction `completed` и выдаёт refresh-cookie только
после identity flow. Link использует текущую refresh session family, action
token остаётся one-time, а новая refresh-cookie не выдаётся.

## Recovery и failure modes

- `invalid_state`, denial, provider failure и expired state завершают только
  свою transaction; terminal rows удаляются при последующих bounded cleanup.
- Если SessionMiddleware не может прочитать signed cookie (bad signature,
  старый secret или timestamp), callback отправляет явное удаление cookie с
  тем же именем, `Path`, `Secure`, `HttpOnly` и `SameSite`. Refresh-cookie не
  затрагивается.
- Legacy `_state_*`, `oauth_next` и link-keys scrub-ятся из валидной cookie.
  Marker сохраняется, пока существует другой pending flow, поэтому callback
  одной вкладки не стирает независимый flow другой.
- Frontend показывает безопасный reason class и ведёт retry-ссылкой на новый
  provider start. Она сохраняет только allowlisted `next`, не рендерит raw
  query и не запускается автоматически в цикле.
- Backend restart не теряет pending rows до истечения TTL. После ротации
  `SECRET_KEY` старый marker становится unreadable и удаляется; старый state
  всё равно не принимается.

## Отклонённые альтернативы

1. Оставить полный transaction payload в signed cookie — rejected: malformed
   cookie не даёт надёжного cleanup, а shared namespace создаёт stale state и
   race между вкладками.
2. Отдельная cookie на provider/attempt — rejected: secrets и link context
   остаются на клиенте, усложняя rotation и deletion.
3. Redis/external TTL store — rejected: SQLAlchemy database уже является общей
   частью deployment topology, новый operational dependency не нужен.

## Security invariant

Recovery только удаляет OAuth artifact. Он не ослабляет state/CSRF, PKCE,
OIDC nonce, redirect URI, VK payload или identity-conflict checks и не удаляет,
не ротирует и не инвалидирует `fit_refresh_token`.
