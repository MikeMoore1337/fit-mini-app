# Amendment to existing Task 111 - Progress bento

**Не заменяет существующую Task 111.**

Если Task 111 ещё pending, добавить:

- target IA/Progress hierarchy должна соответствовать owner-approved Task 115A;
- visual variants брать из Task 123 semantic system (`progress` family), а не создавать отдельный набор случайных gradients;
- bento используется для compact summary/meaningful insights, не для каждой строки данных;
- соблюдать `COMPACT_FIRST_UX_CONTRACT.md`: detail charts/history/periods открываются по intent; не делать все подробности permanently visible; один disclosure level максимум;
- missing data != zero;
- Mobile/TMA first, Desktop reflow отдельно;
- main UX-reset sequence теперь выполняет Task 82 до release gate; если Task 111 выполняется после этого цикла - встроить actual Sleep/Mood history/insights без отдельного top-level section и без parallel representation;
- если владелец сознательно выполняет 111 раньше 82 вне основной очереди - разрешён только conceptual slot без fake UI/data.

Рекомендуемая dependency: Task 123. Task 111 остаётся вне critical path 124A, если владелец отдельно не включает её в release candidate.
