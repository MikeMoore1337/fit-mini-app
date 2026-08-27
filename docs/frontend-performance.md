# Производительность frontend

## Контракт

Проверка относится к production build общего Web/Mobile Web/TMA frontend. Она не заменяет field
monitoring и не доказывает производительность реального Telegram-клиента или физического low-end
устройства.

Актуальные ориентиры Core Web Vitals для статуса `good`:

- LCP — не более `2.5 s`;
- INP — не более `200 ms`;
- CLS — не более `0.1`.

Их оценивают на 75-м перцентиле отдельно для mobile и desktop field data. Локальный production
build, Chromium trace и Lighthouse являются только lab-диагностикой. Источники: [web.dev Web
Vitals](https://web.dev/articles/vitals) и [Google Search Central](https://developers.google.com/search/docs/appearance/core-web-vitals).

## Baseline task 75

Измерение выполнено `2026-08-27` на production build Vite до и после оптимизации task 75.

| Метрика                |          До |       После |               Изменение |
| ---------------------- | ----------: | ----------: | ----------------------: |
| initial JS, raw        | `366 783 B` | `288 746 B` |  `-78 037 B` (`-21.3%`) |
| initial JS, gzip       | `108 617 B` |  `91 077 B` |  `-17 540 B` (`-16.1%`) |
| initial CSS, raw       | `341 764 B` | `330 904 B` |   `-10 860 B` (`-3.2%`) |
| initial CSS, gzip      |  `53 516 B` |  `51 599 B` |    `-1 917 B` (`-3.6%`) |
| `frontend/public`, raw | `920 597 B` | `810 901 B` | `-109 696 B` (`-11.9%`) |

Главная подтверждённая причина initial JS — статическое включение `publicContent.json` в bootstrap
через router/SEO metadata. Теперь content manifest остаётся в lazy public-content boundary; app,
auth, Admin и TMA не загружают его до открытия публичного content route. Landing запрашивает
metadata после первого render, не включая весь manifest в синхронный entry graph. CSS графиков
загружается вместе с `DataViz`, а не на маршрутах без графиков.

Два неиспользуемых legacy proof-файла удалены из production assets. Canonical Landing proofs,
responsive athlete WebP, logo и favicon сохранены. Exercise guide media уже использует lazy
loading, async decode и зарезервированные `width`/`height`; eager video/WebM в frontend нет.

## Автоматический budget

После `npm run build` выполнить из `frontend/`:

```powershell
npm run perf:check
```

Проверка ограничивает initial JS/CSS и public assets, не допускает возврат public content manifest
в entry, eager `DataViz` CSS, удалённых orphan proofs и SVG с embedded raster/external dependency.
Budget — regression boundary, а не обещание field CWV. Рост выше него требует нового измерения и
осознанного обновления контракта.

## Ограничения измерения

- Field/RUM и Search Console data в task 75 недоступны.
- Real Telegram Android/iOS, физический low-end телефон и реальная OS keyboard не проверялись.
- Backend/runtime bottleneck measurements не выявили trigger для server-side изменений: task не
  меняет API, schema, scheduler, export или cardio queries.
