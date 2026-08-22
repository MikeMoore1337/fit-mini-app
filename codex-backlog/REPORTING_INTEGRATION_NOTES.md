# Reporting integration notes v8

## One information architecture

```text
Прогресс
├── Обзор
├── Тренировки
├── Питание
├── Тело
└── Скачать отчёт
```

- task `57` owns nutrition period analytics;
- task `67` owns readable cross-domain report and print/PDF;
- task `65` owns account portability export and is not the same as a readable report;
- task `61` owns confidence wording;
- historical nutrition days compare against the effective target from task `55`.

## First-release PDF decision

Prefer a dedicated print-friendly report page and browser “Save as PDF”. A server PDF queue, public share links and Telegram file delivery are post-release unless a real release blocker proves otherwise.

## Mobile/TMA

- report preview is a mobile-readable screen, not a scaled A4 page;
- TMA uses a safe browser/print handoff and returns to the selected report context;
- unsupported client download behavior is explained explicitly;
- no public permanent URL, Telegram file delivery or hidden share token in the first release.
