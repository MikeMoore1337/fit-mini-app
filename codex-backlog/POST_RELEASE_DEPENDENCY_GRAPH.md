# Dependency graph — post-release trigger-gated pool

## Текущий UX-reset critical path

```text
113 -> 114 -> 115A -> OWNER APPROVAL
 -> 116 -> 117 -> 118 -> 119
 -> 120A -> 120B -> 120C -> 120D
 -> 121 -> 122 -> 123
 -> 81 -> 82 -> 84 -> 124A
 -> OWNER RELEASE APPROVAL
 -> dev -> master -> production deployment
 -> 124B -> 124C only if BLOCKER/HIGH
```

- `81` зависит от `123`; Today использует compact quick action, detail/history — Nutrition.
- `82` зависит от `81` и semantic system `123`; check-in compact, insights/history — Progress.
- `84` зависит от `82` и `122`; settings compact/default-off, Today только actionable state.
- `85 -> 121`, `110 -> 122`, `111 -> 123`; эти tasks вне critical path `124A`, пока владелец не
  включил их в release candidate.
- `115B` отсутствует; real-user validation выполняется Task `124B` после production release.

```text
release 79
  -> 80 Repository hygiene/security/README
  -> 81 Hydration tracking
  -> 82 Daily sleep/mood
  -> 83 Authenticated trainer report handoff
  -> 84 Contextual reminder templates
  -> 85 Knowledge: GI/КБЖУ/BMI/HR zones
  -> 86 PWA
  -> 87 AI decision/privacy/provider
       -> 88 Grounded core
       -> 89 Read-only personal tools
       -> 90 umbrella -> 90A UI/internal evals -> 90B Real-user beta decision
       -> 91 AI period insights
       -> 92 umbrella
            -> 92A Long-term memory (independent Trigger)
            -> 92B Multiprovider routing (independent Trigger)
  -> 93 AI-assisted program import
       -> safe XLSX/CSV/TXT/DOCX extraction
       -> AI neutral draft with source spans
       -> deterministic exercise candidate retrieval
       -> bounded AI reranking/advisory
       -> manual ambiguity resolution -> explicit confirmation -> editable draft
  -> 94 umbrella -> 94A Food-photo feasibility/evals
       -> owner Go/Narrow Go -> 94B Confirmed assisted entry
  -> 95 umbrella -> 95A Server PDF/authenticated download -> 95B Share/Telegram delivery
  -> 96 Wearables discovery
  -> 97 Delegated admins
  -> 98 Native feasibility
  -> 99 umbrella -> 99A Commercial/provider decision
       -> 99B Billing/entitlement backend -> 99C Checkout/account rollout readiness
  -> 100 umbrella -> 100A Core product localization -> 100B Public Web/SEO/content
  -> 101 Private progress photos without AI/body analysis

Report 67 + notifications 64 + active coach relationship
  -> 83 Authenticated trainer report handoff

Report delivery 95A -> 95B External share/Telegram delivery
  (does not replace task 83 in-product handoff)

Telegram Core release task 04
  -> 103 News ingestion -> 104 Moderated publishing -> 104A Exact publication composition
  -> 105 Weekly opt-in digest [COMPLETED]

Current Landing + canonical `@your_fitness_coach_bot` Main Mini App + confirmed `@your_fitness_news`
  -> 106 Landing Telegram app/support/news discoverability [COMPLETED]

Current GitHub Actions CI + Pytest/Vitest/Playwright harness + owner access/retention decisions
  -> 107 Scheduled regression + private Allure reports [OWNER-SELECTED, PENDING; NOT CURRENT]

Current code/data/infrastructure + all backlog families + owner facts + product-lawyer/ru-legal-risk + RF counsel
  -> 108 Russian law compliance audit + continuous future-task gate [OWNER-SELECTED, PENDING; NOT CURRENT]

Current factual Landing + DESIGN_V2_1 + optional approved public security claims baseline from 108
  -> 109 Landing value proposition + conversion story [OWNER-SELECTED, PENDING; NOT CURRENT]

Current AppShell avatar fallback + provider photo + private media/export/delete lifecycle
  -> 110 User custom avatar upload desktop/mobile [OWNER-SELECTED, PENDING; NOT CURRENT]

Current Progress/report services + TimeSeriesChart/DataConfidence + DESIGN_V2_1/Pulse
  -> 111 Progress bento dashboard + 1/7/30/90/365/custom periods [OWNER-SELECTED, PENDING; NOT CURRENT]
```

Прежние import tasks `81-program-import-xlsx-csv` и `95-program-import-txt-docx` объединены в
единую task `93`: формат файла выбирает extractor, а анализ, matching, preview и confirmed write
принадлежат одному pipeline. Task идёт после AI-кластера, поскольку использует принятые там
provider/privacy/safety contracts.

Положение food-photo после AI закреплено и номерами, и графом. Все стрелки дополнительно требуют
evidence Trigger и owner decision. Umbrella-файлы не являются implementation tasks и не разрешают
смешивать дочерние tasks в одном commit.
