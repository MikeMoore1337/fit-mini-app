# Design V2: системные основы

## Как читать значения

**Approved intent** обязателен для pilot и последующего rollout. **Implementation candidate** —
проверенная гипотеза reference prototype; её можно уточнить на реальном UI без изменения смысла.
Нельзя превращать candidate value в локальное исключение одного экрана.

## Semantic color roles

Следующие значения утверждены владельцем как palette baseline:

| Role | YFC Light | YFC Dark | Назначение |
|---|---:|---:|---|
| `canvas` | `#F4F5F2` | `#101310` | Фон страницы/application frame |
| `surface` | `#FFFFFF` | `#161916` | Основной рабочий surface |
| `surface-secondary` | `#ECEDE9` | `#1E221E` | Спокойная группировка/подложка |
| `surface-strong` | `#DADCD7` | `#292E29` | Выраженная нейтральная граница состояния |
| `text-primary` | `#161A17` | `#EEF0EA` | Основной текст и числа |
| `text-secondary` | `#59605B` | `#AFB5AD` | Meta, hints, secondary copy |
| `border` | `#C9CDC8` | `#3A413A` | Rules и quiet boundaries |
| `lime` | `#9EE02B` | `#A8E83A` | Primary/progress/focus/confirmed signal |
| `accent-text` | `#486414` | `#B9EA72` | Малый текстовый accent на neutral surface |
| `on-lime` | `#102015` | `#102015` | Текст и icon на lime fill |

Имена задают handoff contract, а не обязательные CSS identifiers. Success, warning, danger и info
получают отдельные semantic roles: status text, border, subtle surface и foreground. Их нельзя
выражать только цветом; label/icon/structure сохраняют смысл. Точные значения этих ролей являются
implementation candidates до contrast-проверки в pilot.

После owner checkpoint pilot success-состояния используют ту же lime family, что и брендовые
confirmed signals, но на neutral secondary surface. Отдельный бирюзово-зелёный success hue не
используется: в Dark это `#B9EA72` на `#1E221E`, в Light — `#486414` на `#ECEDE9`.

## Light/Dark behavior

- Пользователь выбирает `Light`, `Dark` или `Как в системе`.
- Default candidate — `Как в системе`; явный выбор пользователя приоритетнее настройки ОС.
- Content surfaces остаются внутри активной темы. Светлая card в Dark и тёмная card в Light не
  используются для обычной группировки.
- Различие тем не меняет geometry, hierarchy, component behavior или data semantics.
- Отдельная третья эстетическая тема не создаётся. Возможный high-contrast mode — будущая
  accessibility feature после отдельной проверки.

## Lime usage contract

Один ключевой primary action в локальном decision context обязан использовать lime fill. Это
относится к Landing CTA и основному безопасному действию Today, Active Workout, Nutrition и program
result. Provider choices в `/login`, navigation, secondary, recovery и destructive actions не
становятся lime только потому, что они clickable. Lime также используется для current/selected
state, progress endpoint, keyboard focus и подтверждённого success/sync. Raw lime нельзя применять
для мелкого текста: используется `accent-text`. На lime fill применяется только `on-lime`.
Несколько соседних full-lime elements не должны конкурировать. Rest timer использует theme-native
surface с lime boundary; full lime принадлежит текущему workout action.

## Typography

Approved intent:

- одна humanist sans family с системным fallback и без обязательного внешнего font request;
- выразительный medium/strong weight вместо повсеместного bold;
- отдельные уровни display, page, section, body, meta и data;
- русские labels и длинный текст читаются без искусственного uppercase;
- tabular numerals для времени, веса, повторов, КБЖУ и аналитики.

Implementation candidates: display около `48–64 px` desktop и `40–48 px` mobile; page title
`32–44 px`; section `22–30 px`; body `15–17 px`; meta не меньше читаемого `12–13 px`. Конкретный
scale проверяется на Landing, dense tables и 360 px, а не переносится механически на все surfaces.
Line-height у display плотный, у body и long text — спокойный. Максимальная ширина prose ограничена
читаемой строкой.

## Numeric/data typography

- Значение, unit и period визуально различаются, но остаются одной смысловой группой.
- Decimal separator и units следуют локали и фактическому contract продукта.
- Не выравнивать разные данные пробелами; использовать grid/table alignment.
- Progress показывает numerator/denominator или scale context, а не изолированный процент.
- Отсутствие данных не подменяется нулём; uncertainty и sufficiency описываются словами.

## Spacing, grid и container

Approved intent: desktop work composition использует устойчивую сетку, controlled asymmetry и
разную плотность по частоте действия. Mobile меняет порядок блоков. Повторяющиеся controls держат
touch target не меньше `44 px`.

Implementation candidate для spacing rhythm: `4 / 8 / 12 / 18 / 28 / 44`. Это не разрешение
использовать случайные промежуточные значения; pilot может скорректировать scale системно. Desktop
container и contextual rail выбираются по реальной data density, а не по одному глобальному узкому
content width.

## Radii, borders и shadows

- Основные buttons и form controls: утверждённая geometry `12 px`; compact controls — `8 px`.
  Круглые icon-only controls сохраняют круг только там, где это соответствует их семантике.
- Самостоятельные task regions используют `16 px`; panels верхнего уровня могут использовать
  `20 px`.
- Больший mobile shell radius является presentation artifact, а не token для production cards.
- Rules и borders являются главным способом группировки dense data.
- Shadows редки, малоконтрастны и обозначают реальное elevation/overlay, а не каждую card.
- Pills допустимы только для status, filter, tag или compact action с понятной семантикой.

## Surface hierarchy

`canvas` задаёт frame, `surface` — основную работу, `surface-secondary` — тихую группировку,
`surface-strong` — заметное нейтральное состояние. Card нужна, когда region имеет собственную задачу,
entity context, selection или elevation. Списки, таблицы, методика и аналитические evidence не
получают отдельную card автоматически.

## Focus и состояния

- Focus ring заметен в обеих темах и не зависит только от browser default; reference проверен с
  `3 px` outline.
- Error объясняет причину рядом с полем и сохраняет введённое значение.
- Success подтверждает завершённое действие; warning не выглядит как success.
- Disabled state всегда сопровождается причиной, если она не очевидна из контекста.
- Loading сохраняет layout и не показывает fake data; partial loading не стирает уже доступное.
- Empty даёт следующий шаг; permission/session/offline состояния объясняют recovery и data safety.

## Charts и data visualization

- Chart отвечает на вопрос лучше, чем список чисел; иначе используется текст/table.
- Outcome → evidence → methodology — базовая последовательность Progress.
- Lime отмечает endpoint/current series, но тип данных различается также формой, label или pattern.
- Axes, units, dates, missing data и calculation limitations остаются видимыми.
- Нет псевдонаучных score, скрытых коэффициентов и выводов из недостаточных данных.

## Icons, illustrations и images

Используются canonical brand assets и одна согласованная icon family. Icon не заменяет label там,
где смысл неоднозначен. Иллюстрация или decoration должна объяснять действие/данные или усиливать
brand motif. Product proof и exercise media имеют legal source, reserved dimensions, responsive
sizes и fallback. Synthetic people и случайные stock images не входят в систему.
