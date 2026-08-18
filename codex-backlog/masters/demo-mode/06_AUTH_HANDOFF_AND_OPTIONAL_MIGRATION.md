# Stage 5 - Authentication handoff and demo-data migration decision

## Goal

Ensure a visitor can leave demo mode and enter the real product cleanly.

## Required handoff

At minimum:

1. User chooses to continue/sign in.
2. Existing authentication flow is used.
3. Demo mode is exited.
4. Real authenticated state replaces demo state.
5. Demo fixtures must never overwrite existing account data automatically.
6. No stale demo capability flags remain after authentication/logout transitions.

## Demo data migration

First determine whether safe migration of temporary demo data into a newly authenticated account is low-risk within the current architecture.

### If safe and reasonably scoped

Implement an explicit post-auth choice such as:

- keep/import selected demo data;
- discard demo data.

Requirements:

- never silently overwrite existing real data;
- show exactly what categories are imported;
- validate using normal domain rules;
- make the import idempotent where feasible;
- prevent duplicate creation on retries/navigation;
- do not import prepared fake history/progress as if it belonged to the user unless product requirements explicitly justify it.

A sensible import subset may include user-entered values such as:

- profile parameters entered by the visitor;
- current calculation inputs/results;
- a program created/edited by the visitor.

Prepared fixture history should normally remain demo-only.

### If migration is not safe or would materially increase scope

Do not force it into this task.

Document it as a follow-up enhancement and implement a clean handoff that discards demo state.

## Telegram transition

If the current product supports entering the Telegram Mini App via a public bot/deep-link flow:

- use the existing canonical mechanism;
- avoid inventing a duplicate account-linking scheme;
- ensure demo state is not trusted as Telegram identity.

## Tests

Cover:

- demo -> web auth;
- demo -> authenticated state cleanup;
- logout/auth state transitions;
- existing-user login does not receive fake demo records;
- migration behavior if implemented;
- Telegram handoff URL/flow if testable.

## Commit

Suggested commit intent:

```text
feat/demo: add authenticated handoff for demo users
```
