# Backlog v11 changelog

Дата: 22.08.2026.

## Причина

После выполнения tasks `00-49B` владелец зафиксировал риск накопленной UI inconsistency: предыдущие части продукта создавались при разных версиях rules/roles/skills, поэтому отдельные screens/components могли быть функционально корректны, но расходиться по reuse, размерам, tokens, visual rhythm и mobile composition.

## Изменения

- Добавлена task `49B1` перед `49C`: один rendered UI + component-system audit текущего Design V2, frozen finding set и ограниченная remediation.
- `49B1` намеренно не выбирает новое visual direction и не импортирует A/B/C из task `49B`.
- Для всех будущих client-facing tasks добавлен короткий `UI consistency contract` в `GLOBAL_RULES.md`: shared semantic primitives/tokens, единые variants/sizes/states и mobile-first composition.
- Future feature tasks не повторяют product-wide audit - они проверяют только изменённую поверхность и непосредственные usages shared component.
- Lifecycle уточнён для dedicated `audit + remediation`: finding set замораживается до fixes, review/QA не начинают второй полный audit.
- `49C` теперь сравнивает alternatives с актуальной normalized V2 baseline после `49B1`.
- Control/status/priority/dependency/owner/skill routing docs синхронизированы с user-confirmed completed range `00-49B`.

## Resource budget

`49B1` использует один primary `implementer`, только три core skills (`frontend`, `mobile`, implemented-UI audit), один independent review и один QA pass. Отдельный `$product-designer` не загружается: active Design V2 уже утверждён, а спорные design decisions откладываются до `49C/49D`. Conditional specialists подключаются только по доказанному trigger. Visual coverage строится по distinct UI families и representative viewport/state matrix вместо полного декартова произведения экранов/тем/состояний.
