# Dependency graph — post-release trigger-gated pool

```text
release 79
  -> 80 Private progress photos
  -> 81 XLSX/CSV import -> 95 TXT/DOCX adapters
  -> 82 PWA
  -> 83 umbrella
       -> 83A Commercial/provider decision
       -> 83B Billing/entitlement backend
       -> 83C Checkout/account rollout readiness
  -> 84 AI decision -> 85 Grounded core -> 86 Read-only tools
       -> 87 umbrella -> 87A UI/internal evals -> 87B Real-user beta decision
            -> 87C umbrella
                 -> 87C1 Long-term memory (independent Trigger)
                 -> 87C2 Multiprovider routing (independent Trigger)
  -> 91 umbrella -> 91A Core product localization -> 91B Public Web/SEO/content
  -> 92 umbrella -> 92A Server PDF/authenticated download -> 92B Share/Telegram delivery
  -> 93 Wearables discovery
  -> 94 Delegated admins
  -> 96 Native feasibility

Telegram Core release task 04
  -> 88 News ingestion -> 89 Moderated publishing -> 90 Weekly opt-in digest
```

Все стрелки дополнительно требуют evidence Trigger и owner decision. Umbrella-файлы не являются
implementation tasks и не разрешают смешивать дочерние tasks в одном commit.
