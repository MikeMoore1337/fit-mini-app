# Reference renders Design V2.1

Этот каталог содержит frozen renders, утверждённые владельцем для активной production-системы
`DESIGN_V2_1` в tasks `49D-49G`.

## Покрытие

| Файл | Surface |
| --- | --- |
| `landing-desktop-light.png`, `landing-desktop-dark.png` | Landing Quiet Pace, desktop Light/Dark |
| `landing-mobile-light.png`, `landing-mobile-dark.png` | самостоятельная mobile Landing composition |
| `login-desktop-mobile-light-dark.png` | `/login`: split `1.04fr/.96fr`, `35px`, provider track `240px`, states |
| `app-desktop-light-dark.png` | authenticated V2 content с rail `164px` |
| `mobile-web-core-light-dark.png` | общий Mobile Web component tree |
| `tma-core-light-dark.png` | TMA parity, safe area, BackButton и keyboard boundary |
| `system-states-light.png`, `system-states-dark.png` | loading/empty/error/success/disabled states |

`render-manifest.sha256` фиксирует точные approved bytes. Renders задают hierarchy/composition, но
не доказывают runtime behavior, OAuth, assistive technology, physical keyboard, field performance
или real Telegram Android/iOS.

Для implementation acceptance использовать вместе с:

- `../../design-direction-v2.1.md`;
- `../../responsive-v2.1.md`;
- `../../component-states-v2.1.md`;
- `../../landing-login-v2.1.md`;
- `../../tma-platform-v2.1.md`.
