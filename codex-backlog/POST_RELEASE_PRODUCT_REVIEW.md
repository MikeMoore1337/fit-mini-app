# Product review post-release направлений `80-101`

Дата ревизии: 2026-08-27.

## Итог

Tasks `80-101` и их буквенные подзадачи — trigger-gated pool после release gate `79`: реализация
начинается только после наблюдаемой проблемы/спроса, проверки более дешёвого решения и owner
decision. Номер задаёт предпочтительный порядок, но не заменяет Trigger или dependency.

Импорт XLSX/CSV и TXT/DOCX объединён в task `93` и поставлен после AI-кластера. Это один
пользовательский job и один pipeline: формат определяет extractor, а AI-разбор, exercise matching,
preview и confirmed write не должны расходиться между двумя реализациями. Food-photo остаётся
важной задачей `94`, следующей за AI-assisted import. Billing, локализация и private progress
photos без AI/body analysis остаются в конце.

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
| `80` | Ранний обязательный candidate после `79` | Hygiene/security/docs уменьшают риск следующих изменений; history rewrite и rotation требуют отдельного checkpoint. |
| `81` | Сохранить как optional feature | Hydration — короткий сценарий рядом с Nutrition; никакой навязанной медицинской нормы. |
| `82` | Объединить sleep + mood | Один optional wellbeing check-in; данные входят в отчёт только при заполнении и с coverage. |
| `83` | Узкий in-product handoff | Отчёт передаётся текущему trainer через существующие auth/relationship boundaries; external delivery остаётся в `95B`. |
| `84` | Расширить task `64` | Templates еды, воды и разминки default-off, с quiet hours и suppression/dedupe; второй scheduler не нужен. |
| `85` | Bounded editorial package | GI, источники КБЖУ, BMI и HR zones требуют reviewed primary sources и честных ограничений. |
| `86` | Conditional PWA | Только если launch/return ограничивает Web retention; PWA не обещает полный offline. |
| `87-89` | Строгая AI-цепочка | Сначала provider/privacy/safety/eval decision, затем grounded core и отдельно consented read-only tools. |
| `90A-90B` | Декомпозировать | Internal UI/evals и real-user rollout имеют разные evidence gates; синтетические user results запрещены. |
| `91` | Только после успешной beta | AI итог периода расширяет factual report; нужны consent, evidence anchors, domain evals и non-AI fallback. |
| `92A`, `92B` | Оценивать независимо | Memory решает continuity, routing — provider resilience/cost; допустим `Go` только для одной capability. |
| `93` | Объединить imports и выполнять после AI | Нужны corpus реальных файлов и измеримая экономия времени. AI создаёт проверяемый нейтральный draft и может rerank только bounded candidates. Stable ID, exact/alias/fuzzy retrieval и пороги детерминированы; неоднозначность разрешает пользователь. |
| `94A-94B` | Декомпозировать после AI/import | Фото еды сначала проходит corpus/eval/privacy/cost Go/No-Go; production output — только editable draft. |
| `95A-95B` | Только после gap task `67` | Browser print-to-PDF остаётся fallback; share/Telegram добавляют отдельный риск. |
| `96` | Research-only | Нужен один конкретный wearable datum/platform/job; calories/readiness не становятся product truth. |
| `97` | Conditional | Делегирование оправдано только реальной командой и responsibility matrix. |
| `98` | Research-only | Native feasibility запускается лишь при измеримом Web/TMA/PWA limitation. |
| `99A-99C` | Декомпозировать и оставить в хвосте | Commercial decision, billing state и rollout имеют разные owner checkpoints. |
| `100A-100B` | Декомпозировать и оставить в хвосте | Core locale и Public Web/SEO требуют разных scope и language review. |
| `101` | Последняя очередь | Body images чувствительны; нужны спрос, safe storage и lifecycle task `65`. AI/body analysis исключён. |
| `103-105` | Завершённая отдельная ветка | Telegram editorial operations архивированы и не входят в pending sequence. |
| `106` | Owner-selected bounded Landing task | Развести запуск Mini App, поддержку и подписку на подтверждённый публичный канал без redesign, нового Telegram runtime или изменения editorial pipeline. Implementation требует отдельного owner запуска. |

## Контракт AI-assisted импорта `93`

- Upload проходит allowlist, size/complexity limits, безопасное хранение и детерминированное
  извлечение текста/таблиц до AI.
- AI возвращает только строгую нейтральную схему, source spans и `null` для отсутствующих данных;
  он не пишет canonical entities и не придумывает значения.
- Matching сначала использует stable ID, normalization, exact match, global/user aliases и
  token/fuzzy retrieval с domain hints, включая транслитерацию и языковые варианты.
- AI может только rerank ограниченный список разрешённых кандидатов. Один AI-score никогда не
  является основанием для automatch.
- Private exercises другого пользователя не попадают в candidates. Новые user-scoped aliases
  сохраняются только после явного подтверждения и не меняют global aliases.
- До транзакционной записи пользователь видит preview, unresolved/ambiguous rows и вручную
  подтверждает каждое опасное сопоставление. Результат — редактируемый draft программы.

## Общие routing contracts

- Umbrella `90`, `92`, `94`, `95`, `99`, `100` запрещено выполнять одним change set.
- External research, real-user validation, production provider/price/channel actions и rollout
  требуют фактического evidence/owner checkpoint.
- Все UI tasks `80-101` наследуют active `DESIGN_V2_1`, Mobile Web/TMA contracts и owner screenshot
  checkpoint.
- Existing canonical domains (`36`, `65`, `67`, `71`, Telegram Core) переиспользуются.

## Сверка с историческим AI Coach backlog

Исторический архив `ai-coach.zip` рассмотрен только как источник требований. В актуальные tasks
перенесены `generic/personalized` classification, fail-closed privacy metadata, neutral provider
contracts, evidence bundles, controlled unavailable states, safe Markdown/links и независимые
memory/provider gates. Не перенесены фиксированные providers, лишняя provider redundancy,
autonomous writes, streaming, web search, MCP, multi-agent и тяжёлый RAG до доказанной потребности.

Эта ревизия не подтверждает market demand, не назначает следующую task и не разрешает production
actions.
