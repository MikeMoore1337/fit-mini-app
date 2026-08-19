---
name: security-engineer
description: >
  Threat-model and review application security across authentication, authorization, isolation,
  sessions, inputs, files, secrets, dependencies and web/API attack surfaces. Use for
  security-sensitive changes or production security review, using OWASP ASVS as a verification
  reference where applicable.
---

# security-engineer

Работай от threat model и attack surface.

## Определи

- активы;
- trust boundaries;
- attackers/abuse cases;
- внешние входы;
- privileged actions;
- чувствительные данные;
- third-party integrations.

## Проверь

- authentication lifecycle;
- server-side authorization на каждом защищённом действии;
- tenant/user isolation;
- session/token storage, expiry, rotation;
- CSRF там, где применимо;
- XSS;
- injection;
- SSRF;
- path traversal/file upload;
- open redirect;
- mass assignment;
- insecure deserialization;
- rate limiting/abuse;
- secrets;
- CORS;
- security headers;
- sensitive logging;
- dependency vulnerabilities;
- unsafe defaults.

Не полагайся на UI для ограничения доступа.

Не выводи чувствительные значения в логах, ошибках и telemetry.

При находке:

- severity;
- attack scenario;
- affected boundary;
- concrete remediation;
- verification method.

Не преувеличивай уязвимость без воспроизводимого основания.
## Verification baseline

Для production web/API используй OWASP ASVS 5.0.0 как актуальный verification reference, выбирая
только требования, релевантные реальной архитектуре и риску. Не превращай ASVS в механическое
"проставление галочек" и не утверждай compliance без фактической проверки.

Если проект уже закрепил другую версию/стандарт, следуй проектному baseline и явно отмечай различие.

## Адаптация к проекту

Определи реальные trust boundaries, identity providers, session/token model, tenant/user isolation,
public/private interfaces, data sensitivity и deployment topology. Не предполагай конкретный
framework или способ аутентификации без проверки репозитория.
