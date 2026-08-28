# YFC - карта юридических поверхностей

Использовать как навигацию, а не как доказательство того, что требование применимо.

## A. Аккаунт и идентификация

- Web login;
- Telegram Login;
- Telegram Mini App init/auth data;
- email/username/Telegram IDs;
- account linking;
- удаление аккаунта;
- экспорт данных.

Проверки: 152-ФЗ, доказуемость согласий, identity/data lifecycle, privacy docs.

## B. Тренировки

- планы тренировок;
- история;
- RIR/RPE и подобные показатели;
- адаптация нагрузки;
- упражнения и техника;
- комментарии тренера;
- ограничения пользователя.

Проверки: health-data classification, medical boundary, disclaimer effectiveness, trainer/user allocation of responsibility.

## C. Питание

- дневник;
- продукты;
- калории/макросы;
- adaptive calories;
- barcode/product APIs;
- внешние food databases.

Проверки: health/fitness claims, recommendation technologies, data licenses, external providers.

## D. Антропометрия и check-in

- вес;
- измерения;
- фото прогресса, если появятся;
- самочувствие/ограничения;
- заметки;
- тренды.

Проверки: категории ПД, специальные данные при наличии сведений о здоровье, retention, access, export/delete.

## E. AI Coach

- prompt;
- user context;
- health/training/nutrition context;
- provider routing;
- external LLM APIs;
- logs;
- conversation persistence;
- safety/medical boundaries.

Проверки: 152-ФЗ, cross-border, provider terms, disclosure, liability allocation, medical boundary, recommendation rules.

## F. Coach workspace

- тренер получает доступ к данным клиента;
- приглашения;
- назначение программ;
- комментарии;
- прогресс;
- nutrition access, если реализован.

Проверки: правовое основание и объём доступа, consent/contract, role boundaries, processing on behalf/independent operator questions.

## G. Landing / публичные страницы

- fitness/health claims;
- отзывы;
- кейсы;
- CTA;
- аналитика;
- cookies;
- рекламные интеграции;
- возрастные ограничения;
- legal links.

## H. Монетизация

- подписки;
- premium AI;
- услуги тренера;
- возвраты;
- отмена;
- чеки;
- pricing;
- offers/promotions.

Проверки зависят от того, кто владелец/исполнитель, его налогового режима и модели платежа.

## I. Infrastructure

- primary PostgreSQL;
- backups;
- logs;
- object storage;
- CDN;
- analytics;
- mail;
- Telegram;
- AI providers;
- monitoring.

Страна каждого элемента должна быть зафиксирована в `DATA_FLOW_REGISTER.md` / `THIRD_PARTY_REGISTER.md`.

Смена страны инфраструктуры - обязательный legal recheck trigger.
