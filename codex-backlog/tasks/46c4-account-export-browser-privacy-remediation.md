# TASK 46C.4. Account export and browser privacy remediation

- Фаза: **Retrospective remediation gate**
- Приоритет: **46C.4/93 — после 46C.3**
- Зависит от: `46C.3`
- Canonical findings: `F46B-03`, `F46B-04`
- Рекомендуемый reasoning: **High**
- Рекомендуемая модель: **GPT-5.6 Sol High**
- Рекомендуемые skills: `$privacy-engineer`, `$security-engineer`, `$data-engineer`, `$backend-engineer`, `$frontend-engineer`, `$python-engineer`, `$qa-engineer`, `$code-reviewer`

## Цель

Сделать account export полным относительно current user data inventory и обеспечить единый
lifecycle sensitive user-scoped browser storage.

## Owner-approved contract

- Sensitive user-scoped storage очищается на logout, user switch и successful account deletion.
- Non-sensitive theme preference сохраняется.
- Storage changes backward-compatible.

## Scope

1. Ввести versioned export schema и включить все owner-scoped profile/nutrition domains, в том
   числе food diary snapshots, private foods/favorites, recipes/ingredients и resting heart rate.
2. Экспортировать только данные текущего account; не включать password hashes, tokens, provider
   secrets, чужие managed-client data или несвязанные operational records.
3. Сохранить необходимую snapshot/provenance информацию без расширения purpose.
4. Добавить inventory-to-export completeness contract, чтобы новые persistent user domains нельзя
   было незаметно пропустить.
5. Создать centralized registry user-scoped persistent browser keys и минимизировать содержимое
   drafts до реально нужных полей.
6. На logout, auth user switch и successful account deletion удалять food/measurement/other
   sensitive drafts вместе с workout storage. При failed account deletion не имитировать успех.
7. Не очищать theme preference и другие явно non-sensitive global preferences.

## Compatibility и данные

- DB migration не ожидается: меняется serialization/lifecycle, а не stored schema.
- Добавить явную export schema version. Существующие top-level sections не ломать без необходимости.
- Browser cleanup должен распознавать legacy keys и быть idempotent.
- Export response может вырасти; сохранить streaming/memory safety в пределах текущего data scale и
  не создавать persistent server temp artifacts.

## Targeted regression

- Fixture по каждому current user data class присутствует в export.
- Export не содержит hashes/tokens/secrets/чужие client objects.
- Snapshot/provenance сохраняются только там, где являются частью пользовательских данных.
- Preseed legacy/current sensitive keys -> logout/user switch/successful delete -> keys absent.
- Failed delete не очищает state как будто account удалён.
- Theme preference остаётся.
- Existing active-workout cleanup не регрессирует.

Запустить targeted backend export/privacy tests, frontend storage/auth lifecycle tests, typecheck/lint
и generated API drift, если меняется contract. Полный suite без необходимости не запускать.

## Documentation

Обновить durable account export/lifecycle documentation и versioned export contract. Не переносить
raw privacy findings в public docs.

## STOP CONDITION

После закрытия `F46B-03`, `F46B-04`, targeted review, `git diff` и отдельного commit остановиться.
Не начинать `46C.5`.

## Рекомендуемый commit

`fix(account): complete export and browser data cleanup`

## Процесс и отчёт

Следовать `AGENTS.md` и `codex-backlog/GLOBAL_RULES.md`. Указать export compatibility, browser
lifecycle checks, migrations/config и commit hash.
