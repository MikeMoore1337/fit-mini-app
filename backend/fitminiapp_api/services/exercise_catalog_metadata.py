from __future__ import annotations

from typing import TypedDict


class ExerciseCatalogMetadata(TypedDict):
    aliases: tuple[str, ...]
    movement_pattern: str
    machine_variant_tags: tuple[str, ...]
    execution_variant_tags: tuple[str, ...]


class ExerciseGuideContent(TypedDict):
    steps: list[str]
    breathing: str
    mistakes: list[str]
    secondary: list[str]


UPPER_BODY_MACHINE_SLUGS = (
    "machine-incline-chest-press",
    "independent-lever-chest-press",
    "lever-high-row",
    "lever-low-row",
    "independent-lever-lat-pulldown",
    "machine-pullover",
    "independent-lever-shoulder-press",
    "machine-decline-chest-press",
    "machine-triceps-extension",
    "chest-supported-dumbbell-row",
)

LOWER_BODY_MACHINE_SLUGS = (
    "pendulum-squat",
    "plate-loaded-leg-press",
    "unilateral-leg-press",
    "machine-hip-thrust",
    "smith-split-squat",
    "machine-glute-kickback",
    "v-squat-machine",
    "reverse-hyperextension",
)


CATALOG_METADATA: dict[str, ExerciseCatalogMetadata] = {
    "leg-press": {
        "aliases": (
            "leg press",
            "жим ногами широкая постановка",
            "жим ногами узкая постановка",
            "жим ногами стопы выше",
            "жим ногами стопы ниже",
        ),
        "movement_pattern": "squat",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "hack-squat": {
        "aliases": ("гакк", "hack squat", "гакк машина"),
        "movement_pattern": "squat",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "smith-squat": {
        "aliases": ("смит присед", "smith squat", "присед в машине смита"),
        "movement_pattern": "squat",
        "machine_variant_tags": ("smith",),
        "execution_variant_tags": ("bilateral",),
    },
    "leg-extension": {
        "aliases": ("разгибание ног в тренажере", "leg extension"),
        "movement_pattern": "leg_isolation",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "leg-curl": {
        "aliases": ("сгибание ног лежа", "lying leg curl"),
        "movement_pattern": "leg_isolation",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "seated-leg-curl": {
        "aliases": ("сгибание ног сидя", "seated leg curl"),
        "movement_pattern": "leg_isolation",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "standing-leg-curl": {
        "aliases": ("сгибание ног стоя", "standing leg curl"),
        "movement_pattern": "leg_isolation",
        "machine_variant_tags": (),
        "execution_variant_tags": ("unilateral",),
    },
    "hip-abduction": {
        "aliases": ("разведение ног в тренажере", "отведение бедер", "hip abduction machine"),
        "movement_pattern": "leg_isolation",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "hip-adduction": {
        "aliases": ("сведение ног в тренажере", "сведение бедер", "hip adduction machine"),
        "movement_pattern": "leg_isolation",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "standing-calf-raise": {
        "aliases": ("подъемы на носки в тренажере стоя", "standing calf raise machine"),
        "movement_pattern": "calf",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "seated-calf-raise": {
        "aliases": ("подъемы на носки в тренажере сидя", "seated calf raise machine"),
        "movement_pattern": "calf",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "calf-press": {
        "aliases": ("жим носками", "calf press machine"),
        "movement_pattern": "calf",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "pendulum-squat": {
        "aliases": (
            "маятниковый присед",
            "маятник в тренажере",
            "pendulum squat",
            "pendulum machine squat",
        ),
        "movement_pattern": "squat",
        "machine_variant_tags": ("plate_loaded", "lever"),
        "execution_variant_tags": ("bilateral",),
    },
    "plate-loaded-leg-press": {
        "aliases": (
            "жим ногами на блинах",
            "жим ногами с дисками",
            "plate loaded leg press",
            "рычажный жим ногами",
        ),
        "movement_pattern": "squat",
        "machine_variant_tags": ("plate_loaded",),
        "execution_variant_tags": ("bilateral",),
    },
    "unilateral-leg-press": {
        "aliases": (
            "жим одной ногой",
            "жим ногами одной ногой",
            "single leg press",
            "unilateral leg press",
        ),
        "movement_pattern": "squat",
        "machine_variant_tags": ("selectorized", "plate_loaded"),
        "execution_variant_tags": ("unilateral",),
    },
    "machine-hip-thrust": {
        "aliases": (
            "ягодичный тренажер",
            "ягодичный тренажёр",
            "glute drive",
            "machine hip thrust",
            "рычажный ягодичный мост",
        ),
        "movement_pattern": "glute",
        "machine_variant_tags": ("plate_loaded", "lever"),
        "execution_variant_tags": ("bilateral",),
    },
    "smith-split-squat": {
        "aliases": (
            "смит сплит",
            "сплит присед в смите",
            "smith split squat",
            "smith lunge",
            "выпады в смите",
        ),
        "movement_pattern": "lunge",
        "machine_variant_tags": ("smith",),
        "execution_variant_tags": ("unilateral",),
    },
    "machine-glute-kickback": {
        "aliases": (
            "разгибание бедра в тренажере",
            "ягодичный кикбэк в тренажере",
            "machine glute kickback",
            "glute kickback machine",
        ),
        "movement_pattern": "leg_isolation",
        "machine_variant_tags": ("selectorized", "lever"),
        "execution_variant_tags": ("unilateral",),
    },
    "v-squat-machine": {
        "aliases": (
            "v присед в тренажере",
            "рычажный v присед",
            "v squat",
            "v squat machine",
        ),
        "movement_pattern": "squat",
        "machine_variant_tags": ("plate_loaded", "lever"),
        "execution_variant_tags": ("bilateral",),
    },
    "reverse-hyperextension": {
        "aliases": (
            "обратная гиперэкстензия",
            "обратная гиперэкстензия в тренажере",
            "reverse hyper",
            "reverse hyperextension",
        ),
        "movement_pattern": "hinge",
        "machine_variant_tags": ("lever",),
        "execution_variant_tags": ("bilateral",),
    },
    "machine-incline-chest-press": {
        "aliases": (
            "наклонный жим в тренажере",
            "жим в тренажере на верх груди",
            "incline machine press",
            "incline chest press machine",
            "селекторный жим вверх",
        ),
        "movement_pattern": "chest_press",
        "machine_variant_tags": ("selectorized",),
        "execution_variant_tags": ("bilateral",),
    },
    "independent-lever-chest-press": {
        "aliases": (
            "жим в хаммере",
            "hammer press",
            "рычажный жим",
            "рычажный жим грудь",
            "на блинах грудь",
            "plate loaded chest press",
            "конвергентный жим",
            "iso lateral chest press",
        ),
        "movement_pattern": "chest_press",
        "machine_variant_tags": ("plate_loaded", "lever", "independent", "converging"),
        "execution_variant_tags": ("bilateral", "unilateral"),
    },
    "lever-high-row": {
        "aliases": (
            "верхняя рычажная тяга",
            "верхняя тяга хаммер",
            "high row",
            "high row hammer",
            "рычажная тяга сверху",
        ),
        "movement_pattern": "row",
        "machine_variant_tags": ("plate_loaded", "lever", "independent"),
        "execution_variant_tags": ("bilateral", "unilateral"),
    },
    "lever-low-row": {
        "aliases": (
            "нижняя рычажная тяга",
            "нижняя тяга хаммер",
            "low row",
            "low row hammer",
            "тяга на блинах снизу",
        ),
        "movement_pattern": "row",
        "machine_variant_tags": ("plate_loaded", "lever", "independent"),
        "execution_variant_tags": ("bilateral", "unilateral"),
    },
    "independent-lever-lat-pulldown": {
        "aliases": (
            "вертикальная рычажная тяга",
            "вертикальная тяга хаммер",
            "lever lat pulldown",
            "iso lateral pulldown",
            "рычажная тяга сверху вниз",
        ),
        "movement_pattern": "vertical_pull",
        "machine_variant_tags": ("plate_loaded", "lever", "independent"),
        "execution_variant_tags": ("bilateral", "unilateral"),
    },
    "machine-pullover": {
        "aliases": (
            "пуловер в тренажере",
            "machine pullover",
            "рычажный пуловер",
            "пуловер на блинах",
        ),
        "movement_pattern": "pullover",
        "machine_variant_tags": ("selectorized", "lever"),
        "execution_variant_tags": ("bilateral",),
    },
    "independent-lever-shoulder-press": {
        "aliases": (
            "жим плечами в хаммере",
            "рычажный жим плечами",
            "plate loaded shoulder press",
            "lever shoulder press",
            "iso lateral shoulder press",
            "жим над головой на блинах",
        ),
        "movement_pattern": "shoulder_press",
        "machine_variant_tags": ("plate_loaded", "lever", "independent"),
        "execution_variant_tags": ("bilateral", "unilateral"),
    },
    "machine-decline-chest-press": {
        "aliases": (
            "жим вниз в тренажере",
            "рычажный жим вниз",
            "decline machine press",
            "decline chest press machine",
        ),
        "movement_pattern": "chest_press",
        "machine_variant_tags": ("selectorized",),
        "execution_variant_tags": ("bilateral",),
    },
    "machine-triceps-extension": {
        "aliases": (
            "трицепс в тренажере",
            "разгибание локтей в тренажере",
            "machine triceps extension",
        ),
        "movement_pattern": "triceps",
        "machine_variant_tags": ("selectorized",),
        "execution_variant_tags": ("bilateral",),
    },
    "chest-supported-dumbbell-row": {
        "aliases": (
            "тяга гантелей лежа на наклонной скамье",
            "chest supported dumbbell row",
            "dumbbell incline row",
        ),
        "movement_pattern": "row",
        "machine_variant_tags": (),
        "execution_variant_tags": ("bilateral",),
    },
    "machine-biceps-curl": {
        "aliases": (
            "сгибание на скамье Скотта в тренажере",
            "сгибание рук на скамье Скотта в тренажере",
            "machine preacher curl",
        ),
        "movement_pattern": "arm_curl",
        "machine_variant_tags": ("selectorized",),
        "execution_variant_tags": ("bilateral",),
    },
}


ITEM_GUIDE_CONTENT: dict[str, ExerciseGuideContent] = {
    "pendulum-squat": {
        "steps": [
            "Встань на платформу, расположи плечи под упорами и выбери устойчивую постановку стоп, предусмотренную тренажёром.",
            "Сними рычаг со стопоров и плавно согни тазобедренные и коленные суставы до глубины, на которой стопы и корпус сохраняют опору.",
            "Надави всей стопой на платформу и поднимись по дуге тренажёра без резкого выпрямления коленей.",
        ],
        "breathing": "Вдох перед опусканием, выдох после прохождения тяжёлой части подъёма.",
        "mistakes": [
            "Пятки отрываются от платформы",
            "Колени заметно смещаются внутрь относительно стоп",
            "Отскок из нижнего положения вместо контролируемого разворота",
        ],
        "secondary": ["Ягодицы", "Бицепс бедра", "Икры"],
    },
    "plate-loaded-leg-press": {
        "steps": [
            "Настрой спинку и сядь так, чтобы таз и спина оставались на опоре, затем поставь стопы на платформу.",
            "Сними платформу со стопоров и опусти её до доступной амплитуды без отрыва таза; положение стоп можно менять только сохраняя устойчивую опору.",
            "Выжми платформу всей стопой и остановись до жёсткой блокировки коленей, затем верни стопоры после последнего повтора.",
        ],
        "breathing": "Вдох при контролируемом опускании платформы, выдох после прохождения тяжёлой части жима.",
        "mistakes": [
            "Таз отрывается от спинки в нижней точке",
            "Пятки теряют контакт с платформой",
            "Платформа резко опускается на ограничители",
        ],
        "secondary": ["Ягодицы", "Бицепс бедра", "Икры"],
    },
    "unilateral-leg-press": {
        "steps": [
            "Сядь по центру спинки, поставь одну стопу на платформу, а свободную ногу убери в предусмотренное тренажёром устойчивое положение.",
            "Опусти платформу рабочей ногой без поворота таза, направляя колено по линии стопы.",
            "Выжми платформу всей стопой без резкой блокировки колена и повтори тот же setup для другой стороны.",
        ],
        "breathing": "Вдох при опускании платформы, выдох после прохождения тяжёлой части жима.",
        "mistakes": [
            "Таз разворачивается или смещается на сиденье",
            "Колено уходит в сторону от линии стопы",
            "Свободная нога помогает двигать платформу",
        ],
        "secondary": ["Ягодицы", "Бицепс бедра", "Икры"],
    },
    "machine-hip-thrust": {
        "steps": [
            "Настрой опору и ремень или подушку по инструкции тренажёра, зафиксируй таз и поставь стопы устойчиво.",
            "Разогни тазобедренные суставы и подними рычаг до положения, где корпус и бёдра образуют почти прямую линию без прогиба поясницы.",
            "Плавно опусти таз, сохраняя контакт с опорами и натяжение ремня или подушки.",
        ],
        "breathing": "Вдох при опускании таза, выдох во время разгибания бёдер.",
        "mistakes": [
            "Движение завершается прогибом поясницы вместо разгибания бёдер",
            "Стопы сдвигаются или теряют полный контакт с опорой",
            "Рычаг резко опускается на ограничитель",
        ],
        "secondary": ["Бицепс бедра", "Кор"],
    },
    "smith-split-squat": {
        "steps": [
            "Установи страховочные упоры, расположи гриф на верхней части спины и прими устойчивую разножку под направляющими.",
            "Опустись вниз, сгибая обе ноги и сохраняя переднюю стопу полностью на полу, а корпус — устойчивым под грифом.",
            "Оттолкнись передней ногой и поднимись без поворота таза; перед сменой стороны надёжно верни гриф на фиксаторы.",
        ],
        "breathing": "Вдох перед опусканием, выдох после прохождения тяжёлой части подъёма.",
        "mistakes": [
            "Слишком узкая разножка не даёт устойчивой опоры",
            "Пятка передней ноги отрывается от пола",
            "Корпус смещается вперёд или в сторону относительно грифа",
        ],
        "secondary": ["Квадрицепс", "Ягодицы", "Бицепс бедра", "Кор"],
    },
    "machine-glute-kickback": {
        "steps": [
            "Настрой подушку и опоры так, чтобы рабочее бедро двигалось свободно, а таз и корпус оставались зафиксированы.",
            "Отведи бедро назад по траектории тренажёра без разворота таза и без дополнительного прогиба поясницы.",
            "Плавно верни рычаг до исходного положения, сохраняя опору корпуса.",
        ],
        "breathing": "Выдох при отведении бедра назад, вдох при контролируемом возврате.",
        "mistakes": [
            "Раскачивание корпусом для разгона рычага",
            "Разворот таза вслед за рабочей ногой",
            "Слишком большая амплитуда за счёт прогиба поясницы",
        ],
        "secondary": ["Бицепс бедра", "Кор"],
    },
    "v-squat-machine": {
        "steps": [
            "Расположи плечи под упорами, прижми таз и спину к наклонной опоре и поставь стопы устойчиво на платформу.",
            "Сними рычаг со стопоров и опустись по заданной траектории, сохраняя контакт корпуса с опорой и колени по линии стоп.",
            "Надави всей стопой и поднимись без резкой блокировки коленей, затем верни стопоры после подхода.",
        ],
        "breathing": "Вдох перед опусканием, выдох после прохождения тяжёлой части подъёма.",
        "mistakes": [
            "Таз отрывается от наклонной опоры",
            "Колени смещаются внутрь относительно стоп",
            "Резкий разворот движения на ограничителях",
        ],
        "secondary": ["Ягодицы", "Бицепс бедра", "Икры"],
    },
    "reverse-hyperextension": {
        "steps": [
            "Расположи таз у края опоры, зафиксируй корпус и возьмись за рукояти, оставив ноги свободно опущенными.",
            "Подними ноги разгибанием в тазобедренных суставах примерно до линии корпуса без резкого маха и чрезмерного прогиба поясницы.",
            "Плавно опусти ноги, сохраняя таз и верх тела на опоре.",
        ],
        "breathing": "Выдох при подъёме ног, вдох при контролируемом опускании.",
        "mistakes": [
            "Разгон ног раскачиванием",
            "Подъём выше доступной амплитуды за счёт прогиба поясницы",
            "Таз или корпус теряют устойчивый контакт с опорой",
        ],
        "secondary": ["Ягодицы", "Бицепс бедра", "Разгибатели спины", "Кор"],
    },
    "machine-incline-chest-press": {
        "steps": [
            "Настрой сиденье так, чтобы рукояти начинали движение у верхней части груди, и прижми спину к опоре.",
            "Выжми рукояти вперёд и немного вверх, сохраняя запястья над локтями и плечи опущенными.",
            "Плавно верни рычаги до комфортного положения локтей, не ударяя весовым стеком.",
        ],
        "breathing": "Вдох при возврате рукоятей, выдох после прохождения тяжёлой части жима.",
        "mistakes": [
            "Сиденье настроено слишком высоко или низко",
            "Плечи отрываются от спинки",
            "Весовой стек ударяется между повторами",
        ],
        "secondary": ["Трицепс", "Передняя дельта"],
    },
    "independent-lever-chest-press": {
        "steps": [
            "Настрой сиденье, прижми спину и лопатки к опоре и возьмись за независимые рукояти на уровне середины груди.",
            "Выжми оба рычага вперёд; при одностороннем варианте не разворачивай корпус вслед за рабочей рукой.",
            "Верни рукояти под контролем, сохраняя одинаковую амплитуду справа и слева.",
        ],
        "breathing": "Вдох при возврате рычагов, выдох после прохождения тяжёлой части жима.",
        "mistakes": [
            "Поворот корпуса при независимой работе рук",
            "Неравная амплитуда справа и слева",
            "Резкое опускание дисков на упоры",
        ],
        "secondary": ["Трицепс", "Передняя дельта"],
    },
    "lever-high-row": {
        "steps": [
            "Настрой сиденье и грудной упор так, чтобы дотянуться до верхних рукоятей без отрыва груди.",
            "Потяни локти вниз и назад, сохраняя грудь на опоре и запястья нейтральными.",
            "Плавно выпрями руки вверх-вперёд, не позволяя плечам резко тянуться к ушам.",
        ],
        "breathing": "Выдох во время тяги, вдох при контролируемом возврате рычагов.",
        "mistakes": [
            "Отрыв груди от опоры",
            "Рывок корпусом вместо тяги локтями",
            "Неравная траектория независимых рычагов",
        ],
        "secondary": ["Бицепс", "Задняя дельта", "Предплечья"],
    },
    "lever-low-row": {
        "steps": [
            "Настрой грудной упор и возьмись за нижние рукояти, сохраняя нейтральную спину и почти прямые руки.",
            "Потяни локти назад к талии, не отрывая грудь от опоры и не поднимая плечи.",
            "Верни рычаги вперёд-вниз под контролем, сохраняя устойчивое положение корпуса.",
        ],
        "breathing": "Выдох во время тяги к корпусу, вдох при возвращении рычагов.",
        "mistakes": [
            "Отталкивание грудью от опоры",
            "Локти уходят слишком высоко",
            "Резкий бросок рычагов вперёд",
        ],
        "secondary": ["Бицепс", "Задняя дельта", "Предплечья"],
    },
    "independent-lever-lat-pulldown": {
        "steps": [
            "Настрой сиденье и упор для бёдер, затем возьмись за независимые верхние рукояти.",
            "Опусти локти к бокам, сохраняя корпус устойчивым; при работе одной рукой не наклоняйся в сторону.",
            "Плавно выпрями руки вверх, не позволяя рычагам резко уйти на упоры.",
        ],
        "breathing": "Выдох при опускании рычагов, вдох при возвращении рук вверх.",
        "mistakes": [
            "Сильный отклон корпуса назад",
            "Поворот корпуса при односторонней тяге",
            "Резкое выпрямление рук под нагрузкой",
        ],
        "secondary": ["Бицепс", "Предплечья", "Задняя дельта"],
    },
    "machine-pullover": {
        "steps": [
            "Настрой сиденье и локтевые упоры так, чтобы плечи двигались свободно, а спина оставалась на опоре.",
            "Опусти рычаг дугой к корпусу, сохраняя угол в локтях и не подавая грудную клетку вперёд.",
            "Верни рычаг вверх до комфортного растяжения без отрыва таза и прогиба поясницы.",
        ],
        "breathing": "Выдох при опускании рычага к корпусу, вдох при контролируемом возврате.",
        "mistakes": [
            "Разгибание локтей вместо движения плечом",
            "Избыточный прогиб поясницы",
            "Слишком глубокий возврат за доступную амплитуду плеч",
        ],
        "secondary": ["Грудь", "Трицепс", "Кор"],
    },
    "independent-lever-shoulder-press": {
        "steps": [
            "Настрой сиденье так, чтобы рукояти были около плеч, и прижми спину к опоре.",
            "Выжми независимые рычаги вверх; при работе одной рукой сохраняй рёбра и таз неподвижными.",
            "Опусти рукояти под контролем до комфортного положения локтей без удара дисков об упоры.",
        ],
        "breathing": "Вдох перед жимом, выдох после прохождения тяжёлой части движения.",
        "mistakes": [
            "Сильный прогиб поясницы",
            "Наклон корпуса при одностороннем жиме",
            "Неравная амплитуда независимых рычагов",
        ],
        "secondary": ["Трицепс", "Передняя дельта", "Кор"],
    },
    "machine-decline-chest-press": {
        "steps": [
            "Настрой сиденье так, чтобы рукояти начинали движение у нижней части груди, и сохрани опору спины.",
            "Выжми рукояти вперёд и немного вниз, не поднимая плечи и не отрывая корпус от спинки.",
            "Плавно верни вес до комфортного положения локтей, не ударяя стеком.",
        ],
        "breathing": "Вдох при возврате рукоятей, выдох после прохождения тяжёлой части жима.",
        "mistakes": [
            "Рукояти находятся слишком высоко относительно груди",
            "Плечи подаются вперёд в конце жима",
            "Резкий возврат веса на упоры",
        ],
        "secondary": ["Трицепс", "Передняя дельта"],
    },
    "machine-triceps-extension": {
        "steps": [
            "Настрой сиденье и локтевые упоры так, чтобы ось вращения тренажёра совпадала с локтями.",
            "Разогни локти, сохраняя плечи на опоре и запястья в нейтральном положении.",
            "Плавно согни руки до доступной амплитуды, не позволяя весовому стеку ударяться.",
        ],
        "breathing": "Выдох при разгибании рук, вдох при контролируемом сгибании локтей.",
        "mistakes": [
            "Локти смещены относительно оси тренажёра",
            "Плечи отрываются от упоров",
            "Резкое возвращение веса",
        ],
        "secondary": ["Предплечья", "Кор"],
    },
    "chest-supported-dumbbell-row": {
        "steps": [
            "Ляг грудью на наклонную скамью, упрись стопами в пол и опусти гантели на прямых руках.",
            "Потяни локти назад вдоль корпуса, сохраняя грудь на скамье и нейтральные запястья.",
            "Плавно опусти гантели до полного контролируемого выпрямления рук.",
        ],
        "breathing": "Выдох во время тяги, вдох при опускании гантелей.",
        "mistakes": [
            "Отрыв груди от скамьи",
            "Плечи тянутся к ушам",
            "Удар гантелей друг о друга или о скамью",
        ],
        "secondary": ["Бицепс", "Задняя дельта", "Предплечья"],
    },
}


MEDIA_ALT_BY_PHASE: dict[str, dict[str, str]] = {
    "pendulum-squat": {
        "eccentric_end": "Маятниковый присед: нижнее положение на дуге тренажёра, стопы устойчивы на платформе",
        "concentric_end": "Маятниковый присед: верхнее положение, плечи под упорами и колени без жёсткой блокировки",
    },
    "plate-loaded-leg-press": {
        "eccentric_end": "Жим ногами с дисками: нижнее положение, платформа приближена к корпусу без отрыва таза",
        "concentric_end": "Жим ногами с дисками: платформа выжата, стопы полностью сохраняют опору",
    },
    "unilateral-leg-press": {
        "eccentric_end": "Жим одной ногой: нижнее положение, рабочее колено согнуто по линии стопы",
        "concentric_end": "Жим одной ногой: платформа выжата рабочей ногой, таз остаётся по центру спинки",
    },
    "machine-hip-thrust": {
        "eccentric_end": "Ягодичный мост в рычажном тренажёре: таз опущен, стопы и верх спины на опорах",
        "concentric_end": "Ягодичный мост в рычажном тренажёре: бёдра разогнуты, корпус и бёдра образуют линию",
    },
    "smith-split-squat": {
        "eccentric_end": "Сплит-присед в Смите: нижнее положение в разножке, передняя стопа полностью на полу",
        "concentric_end": "Сплит-присед в Смите: верхнее положение под грифом, таз направлен вперёд",
    },
    "machine-glute-kickback": {
        "eccentric_end": "Разгибание бедра в тренажёре: исходное положение, рабочая стопа на рычажной площадке у корпуса",
        "concentric_end": "Разгибание бедра в тренажёре: конечное положение, площадка отведена назад без поворота таза",
    },
    "v-squat-machine": {
        "eccentric_end": "V-присед в тренажёре: нижнее положение, спина и таз сохраняют контакт с наклонной опорой",
        "concentric_end": "V-присед в тренажёре: верхнее положение, плечи под упорами и стопы на платформе",
    },
    "reverse-hyperextension": {
        "eccentric_end": "Обратная гиперэкстензия: ноги опущены, таз и корпус зафиксированы на опоре",
        "concentric_end": "Обратная гиперэкстензия: ноги подняты примерно до линии корпуса без чрезмерного прогиба",
    },
    "machine-incline-chest-press": {
        "eccentric_end": "Жим от груди вверх в тренажёре: исходное положение, рукояти у верхней части груди",
        "concentric_end": "Жим от груди вверх в тренажёре: конечное положение, руки выпрямлены по диагонали вверх",
    },
    "independent-lever-chest-press": {
        "eccentric_end": "Независимый рычажный жим от груди: исходное положение, рукояти у груди",
        "concentric_end": "Независимый рычажный жим от груди: конечное положение, оба рычага выжаты вперёд",
    },
    "lever-high-row": {
        "eccentric_end": "Верхняя рычажная тяга: исходное положение, грудь на опоре и руки направлены вверх-вперёд",
        "concentric_end": "Верхняя рычажная тяга: конечное положение, локти отведены вниз и назад",
    },
    "lever-low-row": {
        "eccentric_end": "Нижняя рычажная тяга: исходное положение, грудь на опоре и руки направлены вперёд-вниз",
        "concentric_end": "Нижняя рычажная тяга: конечное положение, локти отведены назад к талии",
    },
    "independent-lever-lat-pulldown": {
        "eccentric_end": "Вертикальная рычажная тяга: исходное положение, независимые рукояти над головой",
        "concentric_end": "Вертикальная рычажная тяга: конечное положение, локти опущены к бокам",
    },
    "machine-pullover": {
        "eccentric_end": "Пуловер в тренажёре: исходное положение, рычаг над головой и спина на опоре",
        "concentric_end": "Пуловер в тренажёре: конечное положение, рычаг опущен дугой к корпусу",
    },
    "independent-lever-shoulder-press": {
        "eccentric_end": "Независимый рычажный жим над головой: исходное положение, рукояти около плеч",
        "concentric_end": "Независимый рычажный жим над головой: конечное положение, рычаги выжаты вверх",
    },
    "machine-decline-chest-press": {
        "eccentric_end": "Жим от груди вниз в тренажёре: исходное положение, рукояти у нижней части груди",
        "concentric_end": "Жим от груди вниз в тренажёре: конечное положение, руки выпрямлены вперёд-вниз",
    },
    "machine-triceps-extension": {
        "eccentric_end": "Разгибание рук в тренажёре: исходное положение, локти на опоре и руки согнуты",
        "concentric_end": "Разгибание рук в тренажёре: конечное положение, локти разогнуты под контролем",
    },
    "chest-supported-dumbbell-row": {
        "eccentric_end": "Тяга гантелей с упором грудью: исходное положение, руки опущены под скамьёй",
        "concentric_end": "Тяга гантелей с упором грудью: конечное положение, локти отведены назад",
    },
}


def base_exercise_slug(slug: str) -> str:
    return slug.split("-u-", maxsplit=1)[0]


def exercise_catalog_metadata(slug: str) -> ExerciseCatalogMetadata | None:
    return CATALOG_METADATA.get(base_exercise_slug(slug))
