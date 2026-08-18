---
name: mobile-engineer
description: Native and mobile-client engineering, device lifecycle, connectivity, storage, permissions and platform behavior.
---

# mobile-engineer

Учитывай ограничения реального устройства:

- app lifecycle;
- background/foreground transitions;
- interrupted network;
- offline/poor connectivity;
- permissions;
- secure local storage;
- deep links;
- keyboard/safe areas;
- orientation, если поддерживается;
- device performance;
- battery/network usage.

Не храни чувствительные данные в небезопасном локальном хранилище.

Состояние после kill/restart должно быть предсказуемым для критических сценариев.

Проверяй реальные размеры экранов/эмуляторы и релевантные OS states, а не только unit tests.
## Scope

Используй этот skill для native/mobile application surfaces. Для responsive web-интерфейса
предпочитай `frontend-engineer` и `ui-audit`, если задача не затрагивает native platform APIs или
жизненный цикл мобильного приложения.
