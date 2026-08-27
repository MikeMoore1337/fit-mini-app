# YFC Motion Standards - heuristic baseline

Значения ниже - starting ranges, а не абсолютные запреты.

## Timing

| Interaction | Typical range |
| --- | --- |
| press feedback | 80-160 ms |
| tooltip/small popover | 120-220 ms |
| dropdown/select | 140-280 ms |
| modal/sheet | 180-450 ms |
| page/section transition | 180-500 ms |
| success/progress moment | 250-900 ms |
| explanatory/marketing motion | по narrative, измерять отдельно |

Если более длинное значение ощущается лучше и не мешает flow, оно допустимо.

## Easing heuristics

- entering/exiting: обычно strong `ease-out`;
- on-screen reposition/morph: `ease-in-out` или spring;
- hover/color: `ease`;
- constant progress: `linear`;
- gesture: spring/physics или direct tracking.

Не использовать easing по привычке - оцени feel.

Примеры starting curves:

```css
--yfc-ease-out: cubic-bezier(0.22, 1, 0.36, 1);
--yfc-ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
--yfc-ease-snap: cubic-bezier(0.16, 1, 0.3, 1);
```

Не создавай параллельные tokens, если проект уже имеет motion tokens.

## Scale

Для появления обычно лучше небольшое изменение scale + opacity, чем dramatic `scale(0)`, но это heuristic.

Допустимы более сильные transformations для intentional sport-tech scene/celebration.

## Stagger

Для группы элементов starting range:

- 25-80 ms между элементами.

Не stagger'ить каждый frequent list render, если это замедляет считывание.

## Springs

Используй spring, когда нужны:

- interruption;
- drag;
- momentum;
- physical response;
- live re-target.

Starting direction:

- restrained UI: low/no bounce;
- gesture release: small bounce допустим;
- celebration: больше character, если не мешает.

## Hover

Hover-specific motion должен быть gated для pointer devices, когда touch может получить stuck-hover.

## Performance

Предпочитай GPU/compositor-friendly properties.

Но UX-correct measured layout animation лучше, чем неправильный transform-hack.

Проверяй:

- dropped frames;
- main-thread load;
- layout shift;
- offscreen CPU;
- low-end device;
- TMA;
- browser resize/keyboard.
