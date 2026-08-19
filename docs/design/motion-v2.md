# Design V2: motion

## Роль motion

Motion объясняет причинно-следственную связь: изменение state, навигацию, подтверждение действия,
обновление данных и появление следующего шага. Он не является отдельным декоративным слоем и не
должен замедлять workout, nutrition logging или recovery.

## Иерархия

1. **Immediate feedback:** pressed/focus/validation и подтверждение ввода.
2. **State transition:** current set → completed, rest start/end, loading → content, retry → result.
3. **Spatial transition:** dialog, drawer, sheet и navigation context.
4. **Data transition:** progress/chart update только там, где движение помогает понять изменение.

Если несколько изменений происходят вместе, current action получает первый perceptual signal;
secondary panels не анимируются одновременно ради эффекта.

## Duration и easing

Approved intent — короткая, спокойная и interruptible анимация без bounce. Reference candidates:

- `120–150 ms` для press/focus/compact feedback;
- `160–200 ms` для state change, expand/collapse и small overlay;
- `220–280 ms` только для крупного spatial transition, если он помогает orientation.

Базовый easing candidate — decelerating curve уровня `cubic-bezier(0.2, 0, 0, 1)`; exact values
уточняются на production pilot. Transform/opacity предпочтительнее layout animation, но не ценой
неверной semantic order. Interaction доступно сразу и не ждёт окончания decoration.

## Causality patterns

- Completed set подтверждается рядом с изменённой строкой; затем появляется rest state.
- Sync меняет pending → confirmed без layout jump и без конкуренции с primary action.
- Loading skeleton сохраняет финальную geometry; content не «прилетает» из случайного направления.
- Error появляется рядом с источником и сохраняет доступный content; retry показывает progress на
  том же action.
- Chart update сохраняет axes/labels, меняя только data representation.
- Drawer/sheet возникает из логичного edge; focus сразу переходит внутрь и возвращается инициатору.

## Reduced motion

При `prefers-reduced-motion: reduce`:

- smooth scroll отключён;
- transition сокращается до практически мгновенной смены state;
- transform/parallax/chart interpolation и decorative looping отсутствуют;
- loading и sync остаются понятны текстом/shape, а не движением;
- focus, error и success не теряют видимость.

Reduced motion — та же причинность с меньшим движением, а не выключение feedback.

## Запрещённая анимация

- bounce/spring у routine controls;
- looping pulse/glow вокруг lime;
- parallax, floating blobs, sparkles и auto-playing decoration;
- stagger всего списка при каждом открытии;
- count-up, который временно показывает неверное значение;
- layout shift ради entrance effect;
- анимация, скрывающая или задерживающая error/recovery;
- motion, для которого нет reduced-motion fallback.

Static references подтверждают hierarchy и final states. Timing, interruption, device performance и
Telegram lifecycle проверяются отдельно в production pilot.
