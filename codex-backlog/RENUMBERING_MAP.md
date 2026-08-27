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

## 2026-08-27 — post-release pool после task `79`

Pending post-release tasks перенумерованы так, чтобы сам ID отражал предпочтительную
последовательность реализации. Отдельный product rank удалён. Актуальные ID являются source of
truth; старые используются только для чтения истории Git.

| Прежний ID | Актуальный ID | Направление |
|---:|---:|---|
| `97` | `80` | Repository hygiene/security/README |
| `81` | `81` | XLSX/CSV import |
| `98` | `82` | Hydration tracking |
| `99` | `83` | Sleep/mood check-in |
| `100` | `84` | Trainer report handoff |
| `101` | `85` | Reminder templates |
| `102` | `86` | Knowledge package |
| `82` | `87` | PWA |
| `84-86` | `88-90` | AI decision, grounded core, personal tools |
| `87A-87B` | `91A-91B` | AI UI/evals и rollout |
| `104` | `92` | AI period report insights |
| `87C1-87C2` | `93A-93B` | Advanced AI memory/provider routing |
| `103A-103B` | `94A-94B` | Food-photo feasibility и assisted entry |
| `95` | `95` | TXT/DOCX import |
| `92A-92B` | `96A-96B` | Server PDF и private delivery |
| `93` | `97` | Wearables discovery |
| `94` | `98` | Delegated admins |
| `96` | `99` | Native feasibility |
| `83A-83C` | `100A-100C` | Billing/монетизация |
| `91A-91B` | `101A-101B` | Английская локализация |
| `80` | `102` | Private progress photos без AI/body analysis |
| completed `88-90` | completed `103-105` | Telegram news/digest history |

AI Coach занимает непрерывный кластер `88-93`; food-photo следует сразу после него как
`94/94A/94B`. Анализ фото тела не входит в task `102` и не имеет отдельной downstream task.
