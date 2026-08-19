# Commercial Definition of Done

Используй как финальную рамку для крупной production-работы. Применяй только пункты, релевантные
реальному типу продукта и изменению; не создавай формальный отчёт по неприменимым пунктам.

## Product Experience

- Критические пользовательские сценарии соответствуют acceptance criteria.
- Главный путь к ценности понятен и не содержит известного лишнего friction.
- Первый пользовательский опыт не требует ненужных настроек до получения пользы.
- После критического действия пользователь получает понятный результат/feedback.
- Для релевантных ошибок есть recovery, retry, cancel или понятный следующий шаг.
- Повторяющиеся действия не требуют очевидной лишней ручной работы.
- Нет известных блокирующих дефектов или тупиков критического сценария.

## UI / UX

- Desktop/mobile и ключевые responsive переходы проверены, если применимо.
- Нет overflow/overlap/обрезки критичного контента на поддерживаемых размерах.
- Loading/error/empty/disabled/permission/session-expired states существуют там, где нужны.
- Primary/secondary actions и visual hierarchy понятны.
- UI не выглядит как набор случайных/шаблонных компонентов и сохраняет единый visual language.
- Существенная визуальная работа проверена по фактическому render, а не только по коду.

## Accessibility

- Для web, если проект не задаёт более строгой цели, применимые требования ориентированы на WCAG 2.2 AA.
- Keyboard navigation, focus order и visible focus проверены для критических потоков.
- Semantic HTML/labels/accessible names корректны.
- Contrast, touch targets и reduced motion учтены.
- Автоматический scanner не является единственным accessibility evidence.

## Code

- Изменение не содержит ненужного scope.
- Нет обходов линтера/типов без причины.
- Зависимости оправданы и закреплены lockfile/эквивалентом.
- Ошибки и partial failure имеют предсказуемое поведение.
- Новая сложность имеет продуктовую/техническую причину.

## Data

- Инварианты защищены на подходящем уровне.
- Ownership и lifecycle данных понятны.
- Миграции воспроизводимы и безопасны для существующих данных.
- Destructive changes имеют forward-fix/rollback/expand-contract стратегию по необходимости.
- Для критических данных есть проверяемая backup/restore стратегия, если это требуется риском.

## Privacy

- Собираются только данные, необходимые для функции/явно заявленной цели.
- Access boundaries и data exposure проверены.
- Retention/deletion semantics определены для чувствительных данных.
- Export/account deletion реализованы согласованно со scope, если они требуются продуктом.
- Logs/analytics/traces не содержат лишних персональных/чувствительных payloads.
- Third-party integrations получают минимально необходимый набор данных.
- Privacy-sensitive UX не использует deceptive defaults.

## Security

- AuthN/AuthZ проверяются на доверенной стороне.
- Tenant/user/object isolation не зависит от UI.
- Секретов нет в коде, client bundle, логах и artifacts.
- Внешние входы валидируются; релевантные web/API abuse paths рассмотрены.
- Security-sensitive изменения проверены по применимым требованиям OWASP ASVS 5.0.0 или проектного baseline.
- Dependency/supply-chain риски учтены пропорционально threat model.

## QA

- Unit/integration/contract/UI/e2e покрытие соответствует риску, без бессмысленного дублирования.
- Negative/error/recovery paths проверены.
- Regression test добавлен для существенного исправленного дефекта, где это целесообразно.
- Критические интеграционные failure modes и backward compatibility проверены.
- Visual/accessibility checks добавлены там, где соответствующий риск существенен.

## Performance

- Нет очевидных N+1, unbounded operations и ненужной блокировки критического пути.
- Критический performance path измерен до/после, если риск существенный.
- Для web при отсутствии другого project budget ориентир Core Web Vitals: LCP <= 2.5 s, INP <= 200 ms, CLS <= 0.1 по field data p75 для mobile/desktop.
- Lab benchmark не выдаётся за реальный production experience.
- Поведение при нагрузке/деградации проверено, если это критично для продукта.

## Product Observability

- Logs/metrics/traces коррелируются для критических потоков, если stack это поддерживает.
- Инженер может найти root cause типового критического сбоя без чтения случайных сырых логов.
- Есть product-critical success/failure signal для действительно важных сценариев, если observability scope это оправдывает.
- Metrics не используют опасную high-cardinality разметку без причины.
- Alerts ориентированы на action/user/SLO impact, а не на шум.

## Operations

- Конфигурация отделена от кода; секреты управляются безопасно.
- Есть health/readiness для сервиса, если требуется deployment model.
- Deployment order, migration order и rollback/forward-fix понятны.
- External dependencies, queues/jobs и feature flags учтены.
- Release success criteria определены для значимого production change.

## Documentation

- Setup и команды актуальны.
- Environment variables/API contracts/migrations/deployment описаны, если изменение делает старую документацию неверной.
- Существенные архитектурные, security/privacy и operational ограничения зафиксированы.
- Audit material и чувствительные operational details не публикуются в пользовательской документации без необходимости.

## Final evidence

Перед завершением крупной работы кратко зафиксируй:

- что реально реализовано;
- какие проверки выполнены;
- какие critical paths проверены вручную/автоматически;
- какие риски или ограничения остаются;
- что намеренно не входит в scope.

Не объявляй production-ready только потому, что код компилируется и happy path проходит.
