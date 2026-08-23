import type { ApiSchemas } from '../../shared/api/types';

export type ProgramRevision = ApiSchemas['ProgramRevisionResponse'];
export type TrainingBlock = ApiSchemas['TrainingBlockResponse'];

export interface RevisionDifference {
  label: string;
  before: string;
  after: string;
}

export interface RevisionWorkoutReference {
  id: number;
  scheduledDate: string;
  status: string;
  title: string;
}

export interface RevisionWorkoutExercise {
  exerciseId: number;
  notes: string | null;
  prescribedReps: string;
  prescribedSets: number;
  restSeconds: number | null;
  sortOrder: number;
}

export interface RevisionWorkoutSnapshot extends RevisionWorkoutReference {
  dayNumber: number | null;
  exercises: RevisionWorkoutExercise[];
  weekNumber: number | null;
}

export interface RevisionPresentation {
  differences: RevisionDifference[];
  workoutContextLabel: string | null;
  workouts: RevisionWorkoutReference[];
}

type JsonRecord = Record<string, unknown>;

interface SnapshotBlock {
  id: number;
  title: string;
  startDate: string;
  endDate: string;
  purpose: string;
  notes: string | null;
  isDeload: boolean;
  status: string;
}

const blockStatusLabels: Record<string, string> = {
  planned: 'Запланирован',
  active: 'Идёт сейчас',
  completed: 'Завершён',
  archived: 'В архиве',
};

const workoutStatusLabels: Record<string, string> = {
  planned: 'Запланирована',
  in_progress: 'Выполняется',
  completed: 'Завершена',
  skipped: 'Пропущена',
  cancelled: 'Отменена',
};

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function recordArray(value: unknown): JsonRecord[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function stringValue(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function numberValue(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function booleanValue(value: unknown): boolean {
  return value === true;
}

export function formatProgramDate(value: string): string {
  const date = new Date(`${value}T12:00:00Z`);
  if (Number.isNaN(date.valueOf())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

export function formatRevisionMoment(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return value;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function blockStatusLabel(status: TrainingBlock['status'] | string): string {
  return blockStatusLabels[status] ?? status;
}

export function workoutStatusLabel(status: string): string {
  return workoutStatusLabels[status] ?? 'Статус сохранён в версии';
}

function snapshotRecord(revision?: ProgramRevision): JsonRecord {
  return revision && isRecord(revision.snapshot) ? revision.snapshot : {};
}

function snapshotBlocks(revision?: ProgramRevision): SnapshotBlock[] {
  return recordArray(snapshotRecord(revision).training_blocks)
    .map((block): SnapshotBlock | null => {
      const id = numberValue(block.id);
      if (id == null) return null;
      return {
        id,
        title: stringValue(block.title, `Этап ${id}`),
        startDate: stringValue(block.start_date),
        endDate: stringValue(block.end_date),
        purpose: stringValue(block.purpose),
        notes: typeof block.notes === 'string' ? block.notes : null,
        isDeload: booleanValue(block.is_deload),
        status: stringValue(block.status),
      };
    })
    .filter((block): block is SnapshotBlock => block !== null);
}

function snapshotWorkouts(revision?: ProgramRevision): RevisionWorkoutReference[] {
  return recordArray(snapshotRecord(revision).workouts)
    .map((workout): RevisionWorkoutReference | null => {
      const id = numberValue(workout.id);
      if (id == null) return null;
      return {
        id,
        scheduledDate: stringValue(workout.scheduled_date),
        status: stringValue(workout.status),
        title: stringValue(workout.title, `Тренировка ${id}`),
      };
    })
    .filter((workout): workout is RevisionWorkoutReference => workout !== null);
}

function snapshotWorkoutRecords(revision?: ProgramRevision): Map<number, JsonRecord> {
  const result = new Map<number, JsonRecord>();
  for (const workout of recordArray(snapshotRecord(revision).workouts)) {
    const id = numberValue(workout.id);
    if (id != null) result.set(id, workout);
  }
  return result;
}

function snapshotExercise(value: JsonRecord): RevisionWorkoutExercise | null {
  const exerciseId = numberValue(value.exercise_id);
  if (exerciseId == null) return null;
  return {
    exerciseId,
    notes: typeof value.notes === 'string' ? value.notes : null,
    prescribedReps: stringValue(value.prescribed_reps, 'Не указано'),
    prescribedSets: numberValue(value.prescribed_sets) ?? 0,
    restSeconds: numberValue(value.rest_seconds),
    sortOrder: numberValue(value.sort_order) ?? 0,
  };
}

export function revisionWorkoutSnapshot(
  revision: ProgramRevision | undefined,
  workoutId: number,
): RevisionWorkoutSnapshot | null {
  const workout = snapshotWorkoutRecords(revision).get(workoutId);
  if (!workout) return null;
  return {
    id: workoutId,
    scheduledDate: stringValue(workout.scheduled_date),
    status: stringValue(workout.status),
    title: stringValue(workout.title, `Тренировка ${workoutId}`),
    dayNumber: numberValue(workout.day_number),
    weekNumber: numberValue(workout.week_number),
    exercises: recordArray(workout.exercises)
      .map(snapshotExercise)
      .filter((exercise): exercise is RevisionWorkoutExercise => exercise !== null)
      .sort(
        (left, right) => left.sortOrder - right.sortOrder || left.exerciseId - right.exerciseId,
      ),
  };
}

function displayValue(
  field: keyof SnapshotBlock,
  value: SnapshotBlock[keyof SnapshotBlock] | undefined,
): string {
  if (field === 'startDate' || field === 'endDate') {
    return typeof value === 'string' && value ? formatProgramDate(value) : 'Не указано';
  }
  if (field === 'status') return blockStatusLabels[String(value)] ?? String(value);
  if (field === 'isDeload') return value ? 'Да' : 'Нет';
  if (value == null || value === '') return 'Не указано';
  return String(value);
}

function blockDifferences(current: SnapshotBlock, previous?: SnapshotBlock): RevisionDifference[] {
  const fields: Array<{ key: keyof SnapshotBlock; label: string }> = [
    { key: 'title', label: 'Название этапа' },
    { key: 'startDate', label: 'Начало' },
    { key: 'endDate', label: 'Окончание' },
    { key: 'purpose', label: 'Цель' },
    { key: 'notes', label: 'Заметка' },
    { key: 'isDeload', label: 'Облегчённый период' },
    { key: 'status', label: 'Статус' },
  ];
  return fields.flatMap(({ key, label }) => {
    const before = previous?.[key];
    const after = current[key];
    if (previous && before === after) return [];
    return [
      {
        label,
        before: previous ? displayValue(key, before) : 'Не было',
        after: displayValue(key, after),
      },
    ];
  });
}

function programRecord(revision?: ProgramRevision): JsonRecord {
  const program = snapshotRecord(revision).program;
  return isRecord(program) ? program : {};
}

function programDifference(
  label: string,
  previousValue: unknown,
  currentValue: unknown,
): RevisionDifference | null {
  if (previousValue === currentValue) return null;
  return {
    label,
    before: previousValue == null || previousValue === '' ? 'Не было' : String(previousValue),
    after: currentValue == null || currentValue === '' ? 'Не указано' : String(currentValue),
  };
}

function changedWorkoutReferences(
  revision: ProgramRevision,
  previous?: ProgramRevision,
): RevisionWorkoutReference[] {
  const currentRows = snapshotWorkoutRecords(revision);
  const previousRows = snapshotWorkoutRecords(previous);
  const references = snapshotWorkouts(revision);
  if (!previous) return references;
  const changedFields = isRecord(revision.changed_fields) ? revision.changed_fields : {};
  const changedDayNumber = numberValue(changedFields.day_number);
  const structuralValue = (workout?: JsonRecord) =>
    workout
      ? {
          day_number: numberValue(workout.day_number),
          title: stringValue(workout.title),
          exercises: recordArray(workout.exercises).map((exercise) => ({
            exercise_id: numberValue(exercise.exercise_id),
            sort_order: numberValue(exercise.sort_order),
            prescribed_sets: numberValue(exercise.prescribed_sets),
            prescribed_reps: stringValue(exercise.prescribed_reps),
            rest_seconds: numberValue(exercise.rest_seconds),
            notes: typeof exercise.notes === 'string' ? exercise.notes : null,
            superset_group: stringValue(exercise.superset_group),
            superset_order: numberValue(exercise.superset_order),
          })),
        }
      : null;
  return references.filter((workout) => {
    const current = currentRows.get(workout.id);
    const old = previousRows.get(workout.id);
    if (changedDayNumber != null && numberValue(current?.day_number) !== changedDayNumber) {
      return false;
    }
    return JSON.stringify(structuralValue(current)) !== JSON.stringify(structuralValue(old));
  });
}

function workoutsInsideBlock(
  revision: ProgramRevision,
  block: SnapshotBlock,
): RevisionWorkoutReference[] {
  return snapshotWorkouts(revision).filter(
    (workout) =>
      workout.scheduledDate &&
      workout.scheduledDate >= block.startDate &&
      workout.scheduledDate <= block.endDate,
  );
}

export function buildRevisionPresentation(
  revision: ProgramRevision,
  previous?: ProgramRevision,
): RevisionPresentation {
  const changedFields = isRecord(revision.changed_fields) ? revision.changed_fields : {};
  const targetBlockId = numberValue(changedFields.block_id);
  const currentBlock =
    targetBlockId == null
      ? undefined
      : snapshotBlocks(revision).find((block) => block.id === targetBlockId);
  const previousBlock =
    targetBlockId == null
      ? undefined
      : snapshotBlocks(previous).find((block) => block.id === targetBlockId);

  if (currentBlock) {
    return {
      differences: blockDifferences(currentBlock, previousBlock),
      workoutContextLabel: `Тренировки этапа в версии v${revision.revision_number}`,
      workouts: workoutsInsideBlock(revision, currentBlock),
    };
  }

  const currentProgram = programRecord(revision);
  const previousProgram = programRecord(previous);
  if (revision.change_kind === 'assigned') {
    return {
      differences: [
        {
          label: 'Программа',
          before: 'Не была назначена',
          after: stringValue(currentProgram.title, 'Назначена'),
        },
        {
          label: 'Тренировок в плане',
          before: '0',
          after: String(snapshotWorkouts(revision).length),
        },
      ],
      workoutContextLabel: `Тренировки первой версии v${revision.revision_number}`,
      workouts: snapshotWorkouts(revision),
    };
  }

  if (revision.change_kind === 'program_archived') {
    const difference = programDifference(
      'Статус программы',
      blockStatusLabels[stringValue(previousProgram.status)] ?? previousProgram.status,
      'В архиве',
    );
    return {
      differences: difference ? [difference] : [],
      workoutContextLabel: null,
      workouts: [],
    };
  }

  const affectedWorkouts = changedWorkoutReferences(revision, previous);
  const workoutCount = numberValue(changedFields.workouts_updated);
  const differences: RevisionDifference[] = [];
  if (workoutCount != null) {
    differences.push({ label: 'Обновлено тренировок', before: '0', after: String(workoutCount) });
  }
  const dayNumber = numberValue(changedFields.day_number);
  if (dayNumber != null) {
    differences.push({
      label: 'День программы',
      before: 'Без изменения',
      after: `День ${dayNumber}`,
    });
  }
  if (!differences.length && affectedWorkouts.length) {
    differences.push({
      label: 'Состав плана',
      before: 'Предыдущая версия',
      after: `${affectedWorkouts.length} ${affectedWorkouts.length === 1 ? 'тренировка изменена' : 'тренировки изменены'}`,
    });
  }

  return {
    differences,
    workoutContextLabel: affectedWorkouts.length
      ? `Тренировки, изменённые в версии v${revision.revision_number}`
      : null,
    workouts: affectedWorkouts,
  };
}

export function primaryTrainingBlock(blocks: TrainingBlock[]): TrainingBlock | null {
  const ordered = [...blocks].sort(
    (left, right) => left.start_date.localeCompare(right.start_date) || left.id - right.id,
  );
  return (
    ordered.find((block) => block.status === 'active') ??
    ordered.find((block) => block.status === 'planned') ??
    [...ordered].reverse().find((block) => block.status === 'completed') ??
    [...ordered].reverse().find((block) => block.status === 'archived') ??
    null
  );
}

export function primaryBlockHeading(block: TrainingBlock): string {
  if (block.status === 'active') return 'Текущий тренировочный блок';
  if (block.status === 'planned') return 'Следующий тренировочный блок';
  if (block.status === 'completed') return 'Последний завершённый блок';
  return 'Архивный тренировочный блок';
}
