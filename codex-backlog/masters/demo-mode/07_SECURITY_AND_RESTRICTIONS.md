# Stage 6 - Security and side-effect restrictions

## Goal

Make demo mode safe for anonymous public access.

## Threat model

Assume demo entry is available to arbitrary unauthenticated internet users.

Do not trust client-side UI hiding as the only security control for sensitive/server-side capabilities.

## Required restrictions

Audit and block demo access to identity-bound or external-side-effect operations, including as applicable:

- AI Coach;
- trainer/client invitations;
- account linking;
- Telegram notifications;
- push/email notifications;
- persistent uploads;
- data export containing server/user data;
- payment operations;
- admin/moderation operations;
- changes to another user's data;
- persistent user/profile/program/workout writes not explicitly converted into demo-local operations.

## Backend enforcement

Where an endpoint can be called directly and must not support demo/anonymous execution, enforce the restriction server-side as well.

Return an appropriate authorization/capability error.

Do not rely only on disabled buttons.

## Data isolation

Verify that:

- demo never receives arbitrary real-user data;
- demo fixtures are not sourced from a production user's records;
- identifiers used in fixtures cannot accidentally target real rows;
- demo temporary state cannot be referenced by authenticated APIs as trusted ownership;
- cached demo state is scoped correctly.

## Abuse resistance

Use existing rate limiting/security middleware if demo creates new anonymous server endpoints.

Do not introduce a large new anti-abuse platform solely for this feature.

Anonymous calculations that are already public should retain current limits/validation.

## Secrets

Demo client bundles must not gain:

- AI provider keys;
- Telegram bot secrets;
- privileged backend tokens;
- database credentials;
- admin identifiers that grant access.

## Direct-route testing

Test not only UI behavior but attempts to invoke restricted routes/actions directly.

Especially verify AI Coach cannot be called from demo through:

- direct route navigation;
- raw frontend API client calls;
- backend endpoint requests without a valid authenticated user.

## Security regression tests

Add focused tests for the capability boundary.

## Commit

Suggested commit intent:

```text
security/demo: enforce anonymous demo boundaries
```
