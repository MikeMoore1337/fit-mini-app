# Пользовательский аватар

## Назначение и границы

Собственный аватар используется только для узнаваемости авторизованного аккаунта внутри Your
Fitness Coach. Он не является публичным профилем, фотографией прогресса, источником анализа
внешности или материалом для AI/analytics. Изображение не передаётся во внешние CDN, Telegram API
или сторонние сервисы.

Цепочка отображения едина для Web, Mobile Web и общей TMA UI:

```text
custom avatar -> provider photo_url -> deterministic emoji fallback
```

`users.photo_url` продолжает принадлежать auth-provider lifecycle. Собственный аватар хранится в
отдельных server-owned полях `users.custom_avatar_*`, поэтому новый вход через provider не
перезаписывает выбор пользователя. Binary-колонка помечена как deferred и не загружается обычным
чтением пользователя.

## Upload и нормализация

- authenticated `PUT /api/v1/me/avatar` принимает один multipart-файл;
- максимальный исходный размер — `5 MiB`;
- поддерживаются только однокадровые JPEG, PNG и WebP, определённые по декодированному содержимому,
  а не расширению или client MIME;
- максимальная сторона — `8192 px`, максимум декодированных пикселей — `25 000 000`;
- cooperative processing deadline — `3 s`; между decode, crop и encode запрос прекращается при
  превышении лимита;
- orientation нормализуется, затем выполняется center-crop до квадрата `512x512`;
- результат заново кодируется как WebP размером не более `1 MiB`; исходные EXIF/GPS, filename и
  прочие metadata не сохраняются.

Ошибочный upload не меняет уже сохранённую запись. Replace выполняется в транзакции после полной
проверки нового изображения и сериализуется блокировкой строки пользователя.

## Доступ и lifecycle

Bytes доступны только владельцу через authenticated `GET /api/v1/me/avatar`. Endpoint не содержит
user ID или bearer token в URL и возвращает `Cache-Control: private, no-store` и
`X-Content-Type-Options: nosniff`. Другим пользователям, тренерам и администраторам новый доступ не
добавляется.

`DELETE /api/v1/me/avatar` обнуляет только поля custom avatar и немедленно возвращает provider/emoji
fallback. При account deletion media удаляется атомарно вместе со строкой пользователя. Account
export включает `avatar/avatar.webp` и metadata/hash в `account.json`.

Удаление убирает canonical blob из рабочей PostgreSQL-базы. Уже созданные резервные копии базы
живут по действующей политике backup retention и не обещают мгновенного физического исчезновения;
они не являются активной продуктовой копией и исчезают только по штатному lifecycle резервов.

Логи и audit events содержат только безопасные технические metadata (`content_type`, размеры и
число bytes). Image bytes, base64, filename, EXIF, URL и request body не логируются.
