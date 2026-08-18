# TASK 13. Premium страница авторизации и единый account access UX

- Фаза: **Public/Auth UX**
- Приоритет: **13/93**
- Зависит от: `03`, `05`, `07`, `10`, `11`, `12`
- Рекомендуемый reasoning: **Medium/High**
- Рекомендуемые skills: `$product-designer`, `$frontend-engineer`, `$qa-engineer`

## Цель

Создать canonical Web-страницу `/login` вместо provider chooser, появляющегося только внутри protected-route `AuthGate`.

Auth page должна быть частью того же premium public experience, что и новый Landing, и использовать canonical full logo из task `07` для соответствующей поверхности. Не создавать отдельный auth-logo или альтернативный wordmark.

## In scope

### Dedicated browser route

Добавить:

```text
/login
```

Flow:

```text
Landing
-> /login
-> provider
-> callback
-> safe next/default /app
```

Для browser protected routes `AuthGate` становится redirect/guard layer, а не старой полноэкранной auth-card.

### Telegram Mini App

Valid Telegram launch:

```text
signed initData
-> automatic auth
-> requested route
```

Не показывать browser provider chooser перед TMA auth.

При TMA auth error дать Telegram-specific recovery.

### Provider choices

На Web обязательный product set:

- Telegram;
- Google;
- Яндекс;
- VK ID.

Активной показывать кнопку только если provider configured backend-ом.

Если Telegram browser OAuth unavailable, допустим fallback `Открыть в Telegram`.

Apple - optional, если configured.

Email form скрыт при `ENABLE_EMAIL_AUTH=false`.

### UX hierarchy

Copy по смыслу:

```text
Войти в Your Fitness Coach
Выберите удобный способ
```

Provider controls доступны с keyboard/touch/screen reader и соответствуют актуальным branding requirements.

### Same style as new Landing

Создать reusable public/auth shell, а не копировать landing CSS.

Общие:

- brand;
- typography;
- colors;
- surfaces;
- radii;
- shadows/borders;
- light/dark;
- focus;
- motion principles;
- responsive rules.

Login спокойнее hero, без distracting animation вокруг security-critical actions.

Task `73` обязан после final premium Landing refresh обновить/QA этот же auth shell, чтобы Landing и Login не разошлись визуально.

### Routing

Safe `next` из task `11`:

```text
/login?next=/app
/login?next=/coach
/login?next=/admin
/login?next=/join/<token>
```

После login отсутствие нужной capability = permission UX, а не auth-loop.

### Landing CTA

Browser `Войти` ведёт в canonical `/login`.

Already-authenticated `/login` redirects в safe next или `/app`.

### Error/success

Состояния:

- loading/redirecting;
- unavailable;
- cancelled/denied;
- provider/network error;
- invalid/expired state;
- blocked;
- link conflict;
- retry.

Никаких raw OAuth errors/tokens/codes.

### Linking UI

Сохранить existing `Способы входа` и привести к design system:

- Telegram;
- configured Google;
- configured Яндекс;
- configured VK;
- optional Apple.

Linked / available / in-progress / conflict / failure.

Не делать automatic merge. Unlink не добавлять без отдельного безопасного backend contract.

### Auxiliary auth pages

Verify/reset не удалять. Если Email auth включён, они используют тот же public/auth shell.

### SEO

`/login`, reset/verify и technical callback/error surfaces - `noindex`, не в sitemap.

### Tests

Покрыть:

- Landing -> Login;
- each configured provider start;
- unavailable;
- safe next;
- already authenticated;
- protected route -> login -> return;
- TMA auto-auth bypasses browser login;
- OAuth error -> controlled UI;
- linking success/conflict.

Viewports: 1440/1280/768/390/360, keyboard/focus/reduced-motion.

## Out of scope

Не переписывать provider protocols/session system; не включать Email auth; не делать final Landing content redesign; не делать account merge wizard; не заставлять valid TMA проходить `/login`; не индексировать auth pages.

## Проверки

Web `/login`, required provider buttons, configured-only behavior, Apple optional, Email hidden by default, safe-next, protected routes, Landing CTA, TMA bypass, linking feedback, typecheck/lint/tests/build/Playwright, noindex/sitemap exclusion.

## Done when

Есть canonical `/login`; Web выбирает Telegram/Google/Яндекс/VK из configured providers; TMA входит автоматически; Landing/Login используют один public visual language; continuation/linking безопасны; task `73` закрепляет final visual parity.

## Рекомендуемый commit

`feat(auth): add premium multi-provider login experience`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`.

Работать только в текущей feature-ветке. Не создавать/переключать ветки, не merge/rebase и не deploy в production. Не переходить к следующему task.

После изменений: только профильные проверки по `AGENTS.md`, `git diff`, один логический commit при tracked changes.

В финальном отчёте: изменения, ключевые файлы, migrations/config, реально запущенные проверки, manual provider setup, ограничения и commit hash.

## Final release integration: onboarding

После успешной browser auth:
- existing user -> safe intended destination;
- new/incomplete user -> task `14` onboarding;
- не использовать email совпадение для silent account merge;
- internal `next` не должен обходить required onboarding state, если оно действительно обязательное.
