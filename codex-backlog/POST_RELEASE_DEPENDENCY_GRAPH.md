# Dependency graph — post-release trigger-gated pool

```text
release 79
  -> 80 Repository hygiene/security/README
  -> 81 XLSX/CSV import
  -> 82 Hydration tracking
  -> 83 Daily sleep/mood
  -> 84 Authenticated trainer report handoff
  -> 85 Contextual reminder templates
  -> 86 Knowledge: GI/КБЖУ/BMI/HR zones
  -> 87 PWA
  -> 88 AI decision/privacy/provider
       -> 89 Grounded core
       -> 90 Read-only personal tools
       -> 91 umbrella -> 91A UI/internal evals -> 91B Real-user beta decision
       -> 92 AI period insights
       -> 93 umbrella
            -> 93A Long-term memory (independent Trigger)
            -> 93B Multiprovider routing (independent Trigger)
  -> 94 umbrella -> 94A Food-photo feasibility/evals
       -> owner Go/Narrow Go -> 94B Confirmed assisted entry
  -> 95 TXT/DOCX adapters (after stable 81 import pipeline)
  -> 96 umbrella -> 96A Server PDF/authenticated download -> 96B Share/Telegram delivery
  -> 97 Wearables discovery
  -> 98 Delegated admins
  -> 99 Native feasibility
  -> 100 umbrella -> 100A Commercial/provider decision
       -> 100B Billing/entitlement backend -> 100C Checkout/account rollout readiness
  -> 101 umbrella -> 101A Core product localization -> 101B Public Web/SEO/content
  -> 102 Private progress photos without AI/body analysis

Report 67 + notifications 64 + active coach relationship
  -> 84 Authenticated trainer report handoff

Report delivery 96A -> 96B External share/Telegram delivery
  (does not replace task 84 in-product handoff)

Telegram Core release task 04
  -> 103 News ingestion -> 104 Moderated publishing -> 104A Exact publication composition
  -> 105 Weekly opt-in digest [COMPLETED]
```

Положение food-photo после AI закреплено и номерами, и графом. Все стрелки дополнительно требуют
evidence Trigger и owner decision. Umbrella-файлы не являются implementation tasks и не разрешают
смешивать дочерние tasks в одном commit.
