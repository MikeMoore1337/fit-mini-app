# Third-party design skill references

При подготовке YFC Agents v6 были изучены и концептуально использованы идеи из:

1. `pbakaus/impeccable`
   - License: Apache License 2.0
   - Repository: https://github.com/pbakaus/impeccable

2. `emilkowalski/skills`
   - License: MIT
   - Repository: https://github.com/emilkowalski/skills

В пакет не vendored их исходный runtime/detector и не копируется их структура целиком.
YFC skills переработаны под собственную architecture/routing модель и требования Your Fitness Coach.

Заимствованные концептуальные направления:

- purpose-driven motion;
- interruptibility и spatial continuity;
- animation review;
- isolated UI variant prototyping;
- design critique/polish vocabulary;
- automated design findings как lint-сигналы, а не эстетический source of truth;
- проверка dependency перед добавлением новой UI-библиотеки.

При прямом vendor/copy исходного кода этих проектов в будущем необходимо соблюдать соответствующие условия Apache-2.0/MIT.
