# Renumbering map — release/backlog history

## v5 -> v6 product restructuring

| v5 | v6/v7 |
|---|---|
| 50 Knowledge | 50 Knowledge, narrowed for TMA |
| new | 51 Today/week UX |
| new | 52 Fast nutrition/data completeness |
| new | 53 Workout completion summary |
| new | 54 Training preferences |
| 51 | 55 |
| 52 + 53 | 56 |
| 54 | 57 |
| 55 | 58 |
| 56 | 59 |
| 57 | 60 |
| 58 | 61 |
| 59 | 62 |
| 60 | 63 |
| 61 | 64 |
| 62 | 65 |
| 63 | 66 |
| 64 | 67 |
| 65-71 | 68-69 simplified |
| 72-77 | 70-71, applications removed |
| 78 | 72 |
| 79 | 73 |
| 80 | 74 |
| 81 | 75 |
| 82-97 | post-release AI workstream |

## v6 -> v7 quality gates

| v6 | v7 |
|---|---|
| new | 76 skill-aware retrospective audit |
| 76 usability validation | 77 |
| 77 production readiness | 78 |
| 78 final audit | 79 |

Tasks `00-49` remain completed and are not renumbered.

## v7 -> v8 mobile/TMA gate

| v7 | v8 |
|---|---|
| new | `50A` Mobile Web/TMA quality gate foundation |
| `50-79` | unchanged |

Tasks `00-49` remain completed and are not renumbered or replayed.

## v9 insertion

Tasks `49A-49G` inserted after completed task `49` and before `50A`. Existing numeric tasks were not renumbered.

## 2026-08-27 — объединение imports и финальный post-release order

Прежние tasks `81-program-import-xlsx-csv` и `95-program-import-txt-docx` объединены в единую
task `93-ai-assisted-program-import`. Один формат файла не создаёт отдельного product pipeline:
все поддержанные форматы проходят общий AI-assisted analysis, exercise matching, preview и
confirmed write.

| ID до объединения | Актуальный ID | Направление |
|---:|---:|---|
| `80` | `80` | Repository hygiene/security/README |
| `82` | `81` | Hydration tracking |
| `83` | `82` | Sleep/mood check-in |
| `84` | `83` | Trainer report handoff |
| `85` | `84` | Reminder templates |
| `86` | `85` | Knowledge package |
| `87` | `86` | PWA |
| `88-90` | `87-89` | AI decision, grounded core, personal tools |
| `91A-91B` | `90A-90B` | AI UI/evals и rollout |
| `92` | `91` | AI period report insights |
| `93A-93B` | `92A-92B` | Advanced AI memory/provider routing |
| `81` + `95` | `93` | AI-assisted program import XLSX/CSV/TXT/DOCX |
| `94A-94B` | `94A-94B` | Food-photo feasibility и assisted entry |
| `96A-96B` | `95A-95B` | Server PDF и private delivery |
| `97` | `96` | Wearables discovery |
| `98` | `97` | Delegated admins |
| `99` | `98` | Native feasibility |
| `100A-100C` | `99A-99C` | Billing/монетизация |
| `101A-101B` | `100A-100B` | Английская локализация |
| `102` | `101` | Private progress photos без AI/body analysis |

Актуальный pending pool — `80-101`. AI Coach занимает непрерывный кластер `87-92`, единый
AI-assisted import следует за ним как `93`, а food-photo — как `94/94A/94B`. Анализ фото тела не
входит в task `101` и не имеет отдельной downstream task. Старые ID используются только для чтения
истории Git.
