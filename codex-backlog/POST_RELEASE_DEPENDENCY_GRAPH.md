# Dependency graph — post-release trigger-gated pool

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
```

Прежние import tasks `81-program-import-xlsx-csv` и `95-program-import-txt-docx` объединены в
единую task `93`: формат файла выбирает extractor, а анализ, matching, preview и confirmed write
принадлежат одному pipeline. Task идёт после AI-кластера, поскольку использует принятые там
provider/privacy/safety contracts.

Положение food-photo после AI закреплено и номерами, и графом. Все стрелки дополнительно требуют
evidence Trigger и owner decision. Umbrella-файлы не являются implementation tasks и не разрешают
смешивать дочерние tasks в одном commit.
