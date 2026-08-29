# Post-release UX Reset - priority order

## Owner-driven последовательность

```text
113 branch normalization
  -> 114 nutrition/barcode P0 regression
  -> 115A UX audit + IA + compactness/disclosure prototype/spec
  -> OWNER APPROVAL
  -> 116 core nav + Today
  -> 117 first-run without mandatory onboarding
  -> 118 simple Training Program
  -> 119 type-aware strength/cardio logging
  -> 120A exercise coverage audit
      -> 120B upper-body machine expansion
      -> 120C lower-body machine expansion
      -> 120D remaining coverage + search hardening
  -> 121 Knowledge/Public Web handoff
  -> 122 Profile/settings simplification
  -> 123 semantic compact/expandable card system + visual wow
  -> 81 Hydration [existing owner-local task, amended]
  -> 82 Sleep + Mood [existing owner-local task, amended]
  -> 84 Reminders [existing owner-local task, amended]
  -> 124A pre-release integrated UX/QA gate
  -> OWNER RELEASE APPROVAL
  -> dev -> master + production deployment
  -> 124B production real-user usability validation
  -> 124C remediation ONLY IF 124B has BLOCKER/HIGH
```

В обычном режиме пользователя выполнять именно линейно и не переходить к следующей task автоматически.

## Почему human validation после release

Текущая инфраструктура не предоставляет отдельный dev/staging environment, который можно реалистично отдать внешним пользователям для Web/TMA validation. Поэтому Task 115A является owner design gate, а реальные люди тестируют уже фактически deployed production build в Task 124B.

Это не означает отказ от pre-release QA: Task 124A должна максимально снизить риск production release перед human sessions.

## Existing Tasks 85/110/111

Они не удаляются, но не являются обязательными для данного critical path:

- 85 - после 121, Public Web-first;
- 110 - после 122;
- 111 - после 123 и с учётом фактически реализованной Task 82.

Если владелец сознательно включает любую из них в тот же release candidate до 124A, affected scope должен быть протестирован 124A. Иначе они выполняются отдельным последующим циклом.

## Приоритеты

- **P0:** 113, 114, 115A, 124A, 124B; 124C только при BLOCKER/HIGH.
- **P1:** 116, 117, 118, 119, 120A-D, 81, 82, 84.
- **P2:** 121, 122, 123.

P2 здесь означает sequencing priority, а не низкую важность для итогового UX.
