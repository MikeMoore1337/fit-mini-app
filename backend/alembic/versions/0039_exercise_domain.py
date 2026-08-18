"""normalize exercise muscles, equipment, alternatives, and guide metadata

Revision ID: 0039_exercise_domain
Revises: 0038_food_progress_hardening
Create Date: 2026-08-18
"""

import sqlalchemy as sa

from alembic import op

revision = "0039_exercise_domain"
down_revision = "0038_food_progress_hardening"
branch_labels = None
depends_on = None

MUSCLES = (
    ("chest", "Грудь"),
    ("back", "Спина"),
    ("spinal_erectors", "Разгибатели спины"),
    ("quadriceps", "Квадрицепс"),
    ("hamstrings", "Бицепс бедра"),
    ("glutes", "Ягодицы"),
    ("legs", "Ноги"),
    ("posterior_chain", "Задняя цепь"),
    ("shoulders", "Плечи"),
    ("anterior_deltoid", "Передняя дельта"),
    ("middle_deltoid", "Средняя дельта"),
    ("posterior_deltoid", "Задняя дельта"),
    ("lower_trapezius", "Нижняя трапеция"),
    ("trapezius", "Трапеции"),
    ("biceps", "Бицепс"),
    ("triceps", "Трицепс"),
    ("forearms", "Предплечья"),
    ("grip", "Хват"),
    ("calves", "Икры"),
    ("abs", "Пресс"),
    ("core", "Кор"),
    ("obliques", "Косые мышцы"),
    ("adductors", "Приводящие"),
    ("full_body", "Все тело"),
    ("cardio", "Кардио"),
    ("conditioning", "Кондиция"),
)

EQUIPMENT = (
    ("bodyweight", "Собственный вес"),
    ("dumbbell", "Гантели"),
    ("barbell", "Штанга"),
    ("bench", "Скамья"),
    ("cable", "Тросовый блок"),
    ("machine", "Тренажёр"),
    ("kettlebell", "Гиря"),
    ("cardio", "Кардиооборудование"),
    ("other", "Другое"),
)

EQUIPMENT_BY_VALUE = {
    "Без оборудования": "bodyweight",
    "Брусья": "bodyweight",
    "Собственный вес": "bodyweight",
    "Турник": "bodyweight",
    "Гантели": "dumbbell",
    "Гантель": "dumbbell",
    "EZ-штанга": "barbell",
    "Штанга": "barbell",
    "Скамья": "bench",
    "Скамья Скотта": "bench",
    "Блок": "cable",
    "Кроссовер": "cable",
    "Машина Смита": "machine",
    "Тренажер": "machine",
    "Тренажёр": "machine",
    "Гиря": "kettlebell",
    "Бассейн": "cardio",
    "Беговая дорожка": "cardio",
    "Велосипед": "cardio",
    "Велотренажёр": "cardio",
    "Лыжный эргометр": "cardio",
    "Скакалка": "cardio",
    "Степпер": "cardio",
    "Эллиптический тренажёр": "cardio",
    "Канаты": "other",
    "Медбол": "other",
    "Ролик": "other",
    "Сани": "other",
    "Тумба": "other",
}

PROFILE_SECONDARY = {
    "chest_press": ["Трицепс", "Передняя дельта"],
    "chest_fly": ["Передняя дельта", "Бицепс"],
    "pushup_dip": ["Трицепс", "Передняя дельта", "Кор"],
    "vertical_pull": ["Бицепс", "Предплечья", "Задняя дельта"],
    "row": ["Бицепс", "Задняя дельта", "Предплечья"],
    "pullover": ["Грудь", "Трицепс", "Кор"],
    "hinge": ["Ягодицы", "Бицепс бедра", "Разгибатели спины", "Кор"],
    "squat": ["Ягодицы", "Бицепс бедра", "Кор"],
    "lunge": ["Ягодицы", "Бицепс бедра", "Кор"],
    "leg_isolation": ["Кор"],
    "glute": ["Бицепс бедра", "Кор"],
    "shoulder_press": ["Трицепс", "Передняя дельта", "Кор"],
    "shoulder_raise": ["Трапеции", "Передняя дельта", "Задняя дельта"],
    "arm_curl": ["Предплечья"],
    "triceps": ["Предплечья", "Кор"],
    "calf": ["Кор"],
    "core_static": ["Ягодицы", "Плечи"],
    "core_dynamic": ["Кор", "Косые мышцы"],
    "core_rotation": ["Кор", "Ягодицы"],
    "running": ["Ноги", "Ягодицы", "Икры", "Кор"],
    "walking": ["Ноги", "Ягодицы", "Икры", "Кор"],
    "cycling": ["Квадрицепс", "Ягодицы", "Икры", "Кор"],
    "elliptical": ["Ноги", "Ягодицы", "Икры", "Плечи", "Кор"],
    "stair_climber": ["Квадрицепс", "Ягодицы", "Икры", "Кор"],
    "swimming": ["Спина", "Плечи", "Кор", "Ноги"],
    "ski_erg": ["Спина", "Плечи", "Трицепс", "Кор", "Ноги"],
    "conditioning": ["Ноги", "Кор", "Плечи"],
    "carry": ["Предплечья", "Трапеции", "Кор", "Ягодицы"],
}

PROFILE_SLUGS = {
    "chest_press": {
        "bench-press",
        "incline-bench-press",
        "decline-bench-press",
        "close-grip-bench-press",
        "dumbbell-bench-press",
        "incline-dumbbell-press",
        "decline-dumbbell-press",
        "machine-chest-press",
        "smith-bench-press",
    },
    "chest_fly": {
        "dumbbell-fly",
        "incline-dumbbell-fly",
        "cable-fly",
        "low-to-high-cable-fly",
        "pec-deck",
    },
    "pushup_dip": {"push-up", "weighted-dip", "chest-dip", "bench-dip", "machine-dip"},
    "vertical_pull": {
        "pull-up",
        "chin-up",
        "lat-pulldown",
        "reverse-grip-lat-pulldown",
        "close-grip-lat-pulldown",
    },
    "row": {
        "barbell-row",
        "pendlay-row",
        "t-bar-row",
        "one-arm-dumbbell-row",
        "chest-supported-row",
        "seated-cable-row",
        "machine-row",
        "inverted-row",
        "meadows-row",
        "cable-row-one-arm",
        "face-pull",
        "upright-row",
        "renegade-row",
    },
    "pullover": {"dumbbell-pullover", "straight-arm-pulldown"},
    "hinge": {
        "deadlift",
        "rack-pull",
        "hyperextension",
        "good-morning",
        "romanian-deadlift",
        "stiff-leg-deadlift",
        "single-leg-rdl",
        "glute-ham-raise",
        "cable-pull-through",
        "kettlebell-swing",
        "sumo-deadlift",
    },
    "squat": {
        "squat",
        "front-squat",
        "hack-squat",
        "smith-squat",
        "goblet-squat",
        "belt-squat",
        "leg-press",
        "sissy-squat",
        "wall-sit",
        "kettlebell-goblet-squat",
    },
    "lunge": {
        "lunge",
        "walking-lunge",
        "reverse-lunge",
        "bulgarian-split-squat",
        "split-squat",
        "step-up",
    },
    "leg_isolation": {
        "leg-extension",
        "leg-curl",
        "seated-leg-curl",
        "standing-leg-curl",
        "nordic-curl",
        "hip-abduction",
        "hip-adduction",
        "cable-kickback",
    },
    "glute": {"hip-thrust", "single-leg-hip-thrust", "barbell-glute-bridge"},
    "shoulder_press": {
        "overhead-press",
        "seated-dumbbell-press",
        "arnold-press",
        "machine-shoulder-press",
        "smith-shoulder-press",
        "landmine-press",
    },
    "shoulder_raise": {
        "dumbbell-lateral-raise",
        "cable-lateral-raise",
        "machine-lateral-raise",
        "dumbbell-front-raise",
        "rear-delt-fly",
        "reverse-pec-deck",
        "barbell-shrug",
        "dumbbell-shrug",
        "y-raise",
    },
    "arm_curl": {
        "barbell-curl",
        "ez-bar-curl",
        "dumbbell-curl",
        "hammer-curl",
        "incline-dumbbell-curl",
        "preacher-curl",
        "cable-curl",
        "concentration-curl",
        "reverse-curl",
        "spider-curl",
        "machine-biceps-curl",
    },
    "triceps": {
        "skull-crusher",
        "rope-pushdown",
        "cable-pushdown",
        "overhead-triceps-extension",
        "dumbbell-overhead-extension",
        "lying-dumbbell-triceps-extension",
        "triceps-kickback",
        "single-arm-cable-triceps-extension",
    },
    "calf": {
        "standing-calf-raise",
        "seated-calf-raise",
        "donkey-calf-raise",
        "calf-press",
        "single-leg-calf-raise",
    },
    "core_static": {"plank", "side-plank", "hollow-hold", "dead-bug", "bird-dog"},
    "core_dynamic": {
        "crunch",
        "reverse-crunch",
        "cable-crunch",
        "hanging-leg-raise",
        "captain-chair-leg-raise",
        "ab-wheel",
        "mountain-climber",
    },
    "core_rotation": {"russian-twist", "pallof-press", "woodchopper"},
    "carry": {"farmer-walk", "suitcase-carry"},
    "running": {"outdoor-run", "treadmill-run"},
    "walking": {"outdoor-walk", "treadmill-walk"},
    "cycling": {"outdoor-cycling", "stationary-bike"},
    "elliptical": {"elliptical-trainer"},
    "stair_climber": {"stair-climber"},
    "swimming": {"swimming"},
    "ski_erg": {"ski-erg"},
    "conditioning": {
        "burpee",
        "box-jump",
        "jump-rope",
        "rowing-machine",
        "assault-bike",
        "battle-rope",
        "sled-push",
        "sled-pull",
        "medicine-ball-slam",
        "wall-ball",
        "thruster",
        "kettlebell-clean",
        "kettlebell-snatch",
        "turkish-get-up",
        "bear-crawl",
    },
}

ALTERNATIVE_PAIRS = (
    ("bench-press", "dumbbell-bench-press"),
    ("bench-press", "machine-chest-press"),
    ("incline-bench-press", "incline-dumbbell-press"),
    ("decline-bench-press", "decline-dumbbell-press"),
    ("dumbbell-fly", "cable-fly"),
    ("incline-dumbbell-fly", "low-to-high-cable-fly"),
    ("push-up", "machine-chest-press"),
    ("pull-up", "lat-pulldown"),
    ("chin-up", "reverse-grip-lat-pulldown"),
    ("barbell-row", "chest-supported-row"),
    ("seated-cable-row", "machine-row"),
    ("one-arm-dumbbell-row", "cable-row-one-arm"),
    ("dumbbell-pullover", "straight-arm-pulldown"),
    ("squat", "goblet-squat"),
    ("squat", "leg-press"),
    ("front-squat", "hack-squat"),
    ("lunge", "reverse-lunge"),
    ("bulgarian-split-squat", "split-squat"),
    ("romanian-deadlift", "stiff-leg-deadlift"),
    ("leg-curl", "seated-leg-curl"),
    ("hip-thrust", "barbell-glute-bridge"),
    ("overhead-press", "seated-dumbbell-press"),
    ("machine-shoulder-press", "smith-shoulder-press"),
    ("dumbbell-lateral-raise", "cable-lateral-raise"),
    ("cable-lateral-raise", "machine-lateral-raise"),
    ("rear-delt-fly", "reverse-pec-deck"),
    ("barbell-shrug", "dumbbell-shrug"),
    ("barbell-curl", "ez-bar-curl"),
    ("dumbbell-curl", "cable-curl"),
    ("rope-pushdown", "cable-pushdown"),
    ("overhead-triceps-extension", "dumbbell-overhead-extension"),
    ("standing-calf-raise", "single-leg-calf-raise"),
    ("crunch", "cable-crunch"),
    ("hanging-leg-raise", "captain-chair-leg-raise"),
    ("outdoor-run", "treadmill-run"),
    ("outdoor-walk", "treadmill-walk"),
    ("outdoor-cycling", "stationary-bike"),
)

GENERATED_CARDIO_SLUGS = {
    "outdoor-run",
    "elliptical-trainer",
    "outdoor-cycling",
    "stationary-bike",
    "outdoor-walk",
    "treadmill-walk",
    "stair-climber",
    "swimming",
    "ski-erg",
}
DEFAULT_SAFETY_NOTES = [
    "Используй нагрузку и амплитуду, при которых сохраняется описанная техника; "
    "при острой боли останови подход."
]

SLUG_TO_PROFILE = {slug: profile for profile, slugs in PROFILE_SLUGS.items() for slug in slugs}
MUSCLE_IDENTIFIER_BY_NAME = {name: identifier for identifier, name in MUSCLES}


def _create_schema() -> None:
    op.create_table(
        "muscles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(length=48), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name="muscles_pkey"),
        sa.UniqueConstraint("identifier", name="uq_muscles_identifier"),
        sa.UniqueConstraint("name", name="uq_muscles_name"),
    )
    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name="equipment_pkey"),
        sa.UniqueConstraint("identifier", name="uq_equipment_identifier"),
        sa.UniqueConstraint("name", name="uq_equipment_name"),
    )
    op.create_table(
        "exercise_muscles",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("muscle_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_exercise_muscles_position"),
        sa.CheckConstraint("role IN ('primary', 'secondary')", name="ck_exercise_muscles_role"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["muscle_id"], ["muscles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("exercise_id", "muscle_id", name="exercise_muscles_pkey"),
        sa.UniqueConstraint(
            "exercise_id", "role", "position", name="uq_exercise_muscles_role_position"
        ),
    )
    op.create_index(
        "ix_exercise_muscles_muscle_role_exercise",
        "exercise_muscles",
        ["muscle_id", "role", "exercise_id"],
    )
    op.create_table(
        "exercise_equipment",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_exercise_equipment_position"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("exercise_id", "equipment_id", name="exercise_equipment_pkey"),
        sa.UniqueConstraint("exercise_id", "position", name="uq_exercise_equipment_position"),
    )
    op.create_index(
        "ix_exercise_equipment_equipment_exercise",
        "exercise_equipment",
        ["equipment_id", "exercise_id"],
    )
    op.create_table(
        "exercise_alternatives",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("alternative_exercise_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "exercise_id < alternative_exercise_id",
            name="ck_exercise_alternatives_ordered_pair",
        ),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alternative_exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint(
            "exercise_id", "alternative_exercise_id", name="exercise_alternatives_pkey"
        ),
    )
    op.create_index(
        "ix_exercise_alternatives_reverse",
        "exercise_alternatives",
        ["alternative_exercise_id", "exercise_id"],
    )
    op.create_table(
        "exercise_guide_metadata",
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("safety_notes", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_license", sa.String(length=128), nullable=False),
        sa.Column("source_license_url", sa.Text(), nullable=True),
        sa.Column("media_reference", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("exercise_id", name="exercise_guide_metadata_pkey"),
    )


def _backfill() -> None:
    connection = op.get_bind()
    muscles_table = sa.table(
        "muscles",
        sa.column("identifier", sa.String()),
        sa.column("name", sa.String()),
    )
    equipment_table = sa.table(
        "equipment",
        sa.column("identifier", sa.String()),
        sa.column("name", sa.String()),
    )
    op.bulk_insert(
        muscles_table,
        [{"identifier": identifier, "name": name} for identifier, name in MUSCLES],
    )
    op.bulk_insert(
        equipment_table,
        [{"identifier": identifier, "name": name} for identifier, name in EQUIPMENT],
    )
    muscle_ids = dict(connection.execute(sa.text("SELECT identifier, id FROM muscles")).all())
    equipment_ids = dict(connection.execute(sa.text("SELECT identifier, id FROM equipment")).all())
    rows = (
        connection.execute(
            sa.text(
                "SELECT id, slug, primary_muscle, equipment, created_by_user_id, "
                "source_exercise_id FROM exercises ORDER BY id"
            )
        )
        .mappings()
        .all()
    )
    by_id = {row["id"]: row for row in rows}
    base_by_slug = {
        row["slug"]: row
        for row in rows
        if row["created_by_user_id"] is None and row["source_exercise_id"] is None
    }

    muscle_links = []
    equipment_links = []
    guides = []
    for row in rows:
        source = by_id.get(row["source_exercise_id"])
        base_slug = source["slug"] if source is not None else row["slug"]
        profile = SLUG_TO_PROFILE.get(base_slug)
        used_muscles = set()
        primary_identifier = MUSCLE_IDENTIFIER_BY_NAME.get(row["primary_muscle"])
        if primary_identifier is not None:
            muscle_links.append(
                {
                    "exercise_id": row["id"],
                    "muscle_id": muscle_ids[primary_identifier],
                    "role": "primary",
                    "position": 0,
                }
            )
            used_muscles.add(primary_identifier)
        if profile is not None:
            position = 0
            for name in PROFILE_SECONDARY[profile]:
                identifier = MUSCLE_IDENTIFIER_BY_NAME[name]
                if identifier in used_muscles:
                    continue
                muscle_links.append(
                    {
                        "exercise_id": row["id"],
                        "muscle_id": muscle_ids[identifier],
                        "role": "secondary",
                        "position": position,
                    }
                )
                used_muscles.add(identifier)
                position += 1

        equipment_identifier = EQUIPMENT_BY_VALUE.get(row["equipment"])
        if equipment_identifier is not None:
            equipment_links.append(
                {
                    "exercise_id": row["id"],
                    "equipment_id": equipment_ids[equipment_identifier],
                    "position": 0,
                }
            )

        if profile is not None:
            generated = base_slug in GENERATED_CARDIO_SLUGS
            guides.append(
                {
                    "exercise_id": row["id"],
                    "safety_notes": list(DEFAULT_SAFETY_NOTES),
                    "source_name": "Your Fitness Coach" if generated else "free-exercise-db",
                    "source_url": "/"
                    if generated
                    else "https://github.com/yuhonas/free-exercise-db",
                    "source_license": "Иллюстрация создана для приложения"
                    if generated
                    else "Unlicense (общественное достояние)",
                    "source_license_url": None
                    if generated
                    else "https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md",
                    "media_reference": f"exercise-guides:{base_slug}",
                }
            )

    if muscle_links:
        connection.execute(
            sa.text(
                "INSERT INTO exercise_muscles "
                "(exercise_id, muscle_id, role, position) "
                "VALUES (:exercise_id, :muscle_id, :role, :position)"
            ),
            muscle_links,
        )
    if equipment_links:
        connection.execute(
            sa.text(
                "INSERT INTO exercise_equipment (exercise_id, equipment_id, position) "
                "VALUES (:exercise_id, :equipment_id, :position)"
            ),
            equipment_links,
        )
    if guides:
        guide_table = sa.table(
            "exercise_guide_metadata",
            sa.column("exercise_id", sa.Integer()),
            sa.column("safety_notes", sa.JSON()),
            sa.column("source_name", sa.String()),
            sa.column("source_url", sa.Text()),
            sa.column("source_license", sa.String()),
            sa.column("source_license_url", sa.Text()),
            sa.column("media_reference", sa.String()),
        )
        op.bulk_insert(guide_table, guides)

    alternatives = []
    for left_slug, right_slug in ALTERNATIVE_PAIRS:
        left = base_by_slug.get(left_slug)
        right = base_by_slug.get(right_slug)
        if left is None or right is None:
            continue
        first_id, second_id = sorted((left["id"], right["id"]))
        alternatives.append({"exercise_id": first_id, "alternative_exercise_id": second_id})
    if alternatives:
        connection.execute(
            sa.text(
                "INSERT INTO exercise_alternatives "
                "(exercise_id, alternative_exercise_id) "
                "VALUES (:exercise_id, :alternative_exercise_id)"
            ),
            alternatives,
        )


def upgrade() -> None:
    _create_schema()
    _backfill()


def downgrade() -> None:
    op.drop_table("exercise_guide_metadata")
    op.drop_index("ix_exercise_alternatives_reverse", table_name="exercise_alternatives")
    op.drop_table("exercise_alternatives")
    op.drop_index("ix_exercise_equipment_equipment_exercise", table_name="exercise_equipment")
    op.drop_table("exercise_equipment")
    op.drop_index("ix_exercise_muscles_muscle_role_exercise", table_name="exercise_muscles")
    op.drop_table("exercise_muscles")
    op.drop_table("equipment")
    op.drop_table("muscles")
