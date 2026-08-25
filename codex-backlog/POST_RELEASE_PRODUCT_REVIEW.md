# Product review post-release направлений `80-96`

Дата ревизии: 2026-08-25.

## Итог

Все 18 исходных направлений имеют потенциальную продуктовую ценность, поэтому ни одно не удалено.
При этом ни одно направление не признано обязательным «просто потому, что оно есть в backlog».
Tasks `80-96` и их буквенные подзадачи — trigger-gated pool после release gate `79`: реализация начинается только после
наблюдаемой проблемы/спроса, проверки более дешёвого решения и owner decision.

## Критерии ревизии

- конкретный пользователь и Job-to-be-Done;
- overlap с уже реализованным продуктом;
- минимальный путь к ценности и более дешёвый fallback;
- external/provider/operations dependency;
- privacy/security/domain risk;
- возможность завершить task одним логическим результатом;
- честный success signal без выдуманных KPI.

## Решения по направлениям

| Tasks | Решение | Обоснование и обязательный Trigger |
|---|---|---|
| `80` | Сохранить conditional | Полезно для visual progress, но body images — чувствительные данные и новый storage cost. Нужны повторяющийся спрос, safe media storage и готовый lifecycle task `65`. AI/body analysis исключён. |
| `81` | Сохранить; вероятный ранний candidate | Может заметно экономить время тренера, но ценность доказывается corpus реальных файлов и временем ручного переноса. Canonical template и preview предпочтительнее обещания arbitrary import. |
| `82` | Сохранить conditional | Имеет смысл только если launch/return действительно ограничивает Web retention после performance fixes. Task `36` остаётся canonical offline workout mechanism; PWA не обещает полный offline. |
| `83A-83C` | Сохранить и декомпозировать | Commercial/provider decision, billing state и customer rollout имеют разные owner checkpoints и trust boundaries. Реализация без payer/value contract запрещена. |
| `84-86` | Сохранить строгой цепочкой | AI допустим только для конкретных jobs, которые обычный UX/deterministic logic не решают дешевле. Сначала provider/privacy/safety/eval decision, затем grounded core, затем отдельно consented read-only tools. |
| `87A-87B` | Декомпозировать | UI/internal evals — implementation task; реальные participants/observations и rollout decision — внешний evidence gate. Синтетические «user results» запрещены. |
| `88-90` | Сохранить отдельной веткой | Это editorial operations product, а не core fitness feature. Нужны stable Telegram Core, реальная owner moderation capacity и отдельный добровольный спрос на digest. Auto-post и auto-opt-in исключены. |
| `91A-91B` | Декомпозировать | Locale foundation/core product и Public Web/SEO/editorial wave различаются объёмом и QA. Полный перевод без target segment и language reviewer создаст дорогой stale content. |
| `92A-92B` | Декомпозировать и запускать только после gap task `67` | Server renderer может понадобиться для стабильного delivery, но browser print-to-PDF уже является fallback. Bearer share/Telegram добавляют отдельный риск и не следуют автоматически из PDF generation. |
| `93` | Оставить research-only | Нельзя планировать «все часы». Нужен один конкретный datum/platform/job; watch calories, eating-back calories и readiness score не становятся product truth. |
| `94` | Сохранить conditional | Делегирование оправдано только реальной командой и responsibility matrix. Task `71` уже закрывает минимальный Root Admin; speculative hierarchy и admin TMA не нужны. |
| `95` | Сохранить после `81` | TXT/DOCX имеют смысл только после доказанной ценности общего import pipeline. Deterministic grammar и честные unresolved states обязательны; LLM — необязательный bounded helper. |
| `96` | Оставить research-only | Native rewrite не нужен ради App Store presence. Feasibility запускается только при измеримом Web/TMA/PWA limitation и проверяет один главный риск prototype/spike. |
| `87C1`, `87C2` | Разделить и оценивать независимо | Memory решает continuity, routing — provider resilience/cost. Одна проблема не доказывает вторую; допустим `Go` только для одной capability. |

## Что добавлено к acceptance contracts

- Trigger matrix стала обязательной до запуска направления.
- Product rank отделён от execution order.
- Umbrella `83`, `87`, `87C`, `91`, `92` запрещено выполнять одним change set.
- External research, real-user validation, production provider/price/channel actions и rollout требуют
  фактического evidence/owner checkpoint; sequencing assumption их не заменяет.
- Skills разделены на core и conditional по фактическому trigger; review/QA roles указаны явно.
- Все UI tasks `80+` наследуют active `DESIGN_V2_1`, Mobile Web/TMA contracts и owner screenshot
  checkpoint.
- Existing canonical domains (`36`, `65`, `67`, `71`, Telegram Core) переиспользуются, а не
  дублируются новым subsystem.

## Сверка с историческим AI Coach backlog

Исторический архив `ai-coach.zip` с tasks `82-97` рассмотрен как источник требований, а не как
исполняемый backlog. Его старая нумерация, dependency graph и provider choices не переносятся.

Полезные требования интегрированы в актуальные tasks:

- `84`: explicit `generic/personalized` classification, fail-closed provider/upstream privacy
  metadata и owner-selected `free-only`/bounded-paid cost policy;
- `85`: neutral capability/cost/privacy contracts, nullable usage/actual model, bounded
  retry/failover/cooldown taxonomy и отсутствие privacy downgrade;
- `86`: structured evidence bundle для `Почему?`, конкретные nutrition/training/cardio/anthropometry
  negative cases и обычный русский вместо обязательного внутреннего жаргона;
- `87A`: controlled personal-tools-unavailable state, safe Markdown/links, natural quick prompts и
  запрет AI-created reminders/proactive engagement;
- `87C1`: строгое разделение conversation, telemetry, canonical data и durable memory, а также
  account/unlink/clear lifecycle;
- `87C2`: deterministic candidate eligibility, conditional free-only guards, normalized errors,
  bounded attempts и opt-in live smoke seam.

Не перенесены как готовые решения:

- обязательные Cloudflare Workers AI, OrcaRouter и OpenRouter adapters или фиксированный порядок;
- три provider «на всякий случай» до beta evidence;
- безусловный `AI_FREE_ONLY=true` — cost policy выбирает owner в task `84`;
- отдельные implementation tasks для nutrition, training и `Почему?`: они остаются approved tool/
  evidence contracts внутри `86`, чтобы не расширять AI data scope автоматически;
- обязательная persisted conversation history и одинаковый AI entry в Web/TMA: persistence решает
  `84`, а TMA entry допускается только после mobile/latency evidence в umbrella `87`;
- исторические app-help тексты про заявку/модерацию тренера: knowledge grounding строится по
  фактическому продукту после task `70`, без возврата удалённого application flow;
- ранняя long-term memory, autonomous writes, streaming, web search, MCP, multi-agent и тяжёлый RAG.

## Не является решением

Эта ревизия не подтверждает текущий market demand, не назначает следующую task, не разрешает
production actions и не запускает реализацию `80` или любого другого направления.
