# Final execution order

## Completed through Design V2 integration gate
`00-46`, `46A-46J`, включая `46C.1-46C.6`

## Brand foundation
`07`
- canonical light/dark logo SVG
- mark-only readable favicon
- one brand source of truth for downstream surfaces

## Foundation and activation
`08-14`

## Food and training domains
`15-40`

## Completed product UX before retrospective gate
`41-46`

## Retrospective audit and owner-approved remediation
`46A -> 46B -> 46B1 -> 46C umbrella -> 46C.1 -> 46C.2 -> 46C.3 -> 46C.4 -> 46C.5 -> 46C.6`

Каждая `46C.*` выполняется отдельной сессией и отдельным commit.

## Design V2 integration
```text
46D -> 46E
    -> owner choice
    -> 46F
    -> owner approval
    -> 46G
    -> owner manual test
    -> 46H
    -> owner approval
    -> 46I -> 46J -> 47
```

Task `46D` начинается только после завершения всех `46C.1-46C.6`.
Task `46C.6` — уже завершённая owner-approved вставка для сохранения Telegram proxy-tunnel; она не
меняет исходную нумерацию `47-93`.

## Remaining product UX
`47-57`

Следующая задача: `47-profile-account-experience.md`.

## Final core-product gaps
`58 -> 59 -> 59A -> 60 -> 61`
- deterministic progression
- notifications/reminders
- main Telegram bot support/feedback
- account lifecycle/export
- guarded manual cardio

## Release surfaces
`62-75`
- Demo
- Admin and trainer activation: `69 -> 69A -> 70 -> 70A -> 71 -> 71A`
- TMA platform integration over shared YFC UI
- Landing
- Responsive/A11y
- Performance

At task `75`, YFC must already be a complete usable product with AI disabled.

## AI Coach last
`76-91`

## Operational release hardening
`92`

## Final release candidate gate
`93`

After `93`: no feature work before release except blockers.
