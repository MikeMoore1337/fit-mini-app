import type { Workout } from '../../shared/api/types';

type WorkoutSet = Workout['exercises'][number]['sets'][number];

export const ACTIVE_WORKOUT_QUEUE_VERSION = 1 as const;
const ACTIVE_WORKOUT_QUEUE_PREFIX = 'fit_active_workout_v1_';
const ACTIVE_WORKOUT_REST_PREFIX = 'fit_active_workout_rest_v1_';
const ACTIVE_WORKOUT_POINTER_PREFIX = 'fit_active_workout_current_v1_user_';
const MAX_QUEUE_LENGTH = 256;

export interface ActiveWorkoutSetValues {
  actual_reps: number | null;
  actual_weight: number | null;
  rir?: WorkoutSet['rir'];
  set_kind?: WorkoutSet['set_kind'];
  reached_failure?: WorkoutSet['reached_failure'];
  is_completed: boolean;
}

export interface ActiveWorkoutMutation {
  mutation_id: string;
  set_id: number;
  expected_version: number;
  values: ActiveWorkoutSetValues;
  created_at: number;
}

export interface ActiveWorkoutQueue {
  schema_version: typeof ACTIVE_WORKOUT_QUEUE_VERSION;
  user_id: number;
  workout_id: number;
  queue: ActiveWorkoutMutation[];
  workout_snapshot?: Workout;
}

function scopedSuffix(userId: number, workoutId: number): string {
  return `user_${userId}_workout_${workoutId}`;
}

export function activeWorkoutQueueKey(userId: number, workoutId: number): string {
  return `${ACTIVE_WORKOUT_QUEUE_PREFIX}${scopedSuffix(userId, workoutId)}`;
}

export function activeWorkoutRestKey(userId: number, workoutId: number): string {
  return `${ACTIVE_WORKOUT_REST_PREFIX}${scopedSuffix(userId, workoutId)}`;
}

export function emptyActiveWorkoutQueue(userId: number, workoutId: number): ActiveWorkoutQueue {
  return {
    schema_version: ACTIVE_WORKOUT_QUEUE_VERSION,
    user_id: userId,
    workout_id: workoutId,
    queue: [],
  };
}

function validNullableNumber(value: unknown, integer: boolean): value is number | null {
  return (
    value === null ||
    (typeof value === 'number' &&
      Number.isFinite(value) &&
      value >= 0 &&
      (!integer || Number.isInteger(value)))
  );
}

function validMutation(value: unknown): value is ActiveWorkoutMutation {
  if (!value || typeof value !== 'object') return false;
  const item = value as Partial<ActiveWorkoutMutation>;
  return Boolean(
    typeof item.mutation_id === 'string' &&
    item.mutation_id.length >= 16 &&
    item.mutation_id.length <= 64 &&
    Number.isInteger(item.set_id) &&
    Number(item.set_id) > 0 &&
    Number.isInteger(item.expected_version) &&
    Number(item.expected_version) >= 1 &&
    Number.isFinite(item.created_at) &&
    item.values &&
    validNullableNumber(item.values.actual_reps, true) &&
    validNullableNumber(item.values.actual_weight, false) &&
    (item.values.rir === undefined ||
      item.values.rir === null ||
      ['0', '1', '2', '3', '4+'].includes(item.values.rir)) &&
    (item.values.set_kind === undefined ||
      item.values.set_kind === null ||
      ['warmup', 'working', 'drop'].includes(item.values.set_kind)) &&
    (item.values.reached_failure === undefined ||
      item.values.reached_failure === null ||
      typeof item.values.reached_failure === 'boolean') &&
    typeof item.values.is_completed === 'boolean',
  );
}

function validWorkoutSnapshot(value: unknown, workoutId: number): value is Workout {
  if (!value || typeof value !== 'object') return false;
  const workout = value as Partial<Workout>;
  return Boolean(
    workout.id === workoutId &&
    workout.status === 'in_progress' &&
    typeof workout.title === 'string' &&
    typeof workout.scheduled_date === 'string' &&
    Array.isArray(workout.exercises) &&
    workout.exercises.every(
      (exercise) =>
        exercise &&
        Number.isInteger(exercise.id) &&
        typeof exercise.exercise_title === 'string' &&
        Array.isArray(exercise.sets) &&
        exercise.sets.every(
          (set) =>
            set &&
            Number.isInteger(set.id) &&
            Number.isInteger(set.set_number) &&
            typeof set.is_completed === 'boolean',
        ),
    ),
  );
}

export function loadActiveWorkoutQueue(
  userId: number,
  workoutId: number,
  validSetIds?: ReadonlySet<number>,
): ActiveWorkoutQueue {
  const key = activeWorkoutQueueKey(userId, workoutId);
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return emptyActiveWorkoutQueue(userId, workoutId);
    const parsed = JSON.parse(raw) as Partial<ActiveWorkoutQueue>;
    const snapshotValid =
      parsed.workout_snapshot === undefined ||
      validWorkoutSnapshot(parsed.workout_snapshot, workoutId);
    const snapshotSetIds = parsed.workout_snapshot
      ? new Set(
          parsed.workout_snapshot.exercises.flatMap((exercise) =>
            exercise.sets.map((set) => set.id),
          ),
        )
      : null;
    const valid =
      parsed.schema_version === ACTIVE_WORKOUT_QUEUE_VERSION &&
      parsed.user_id === userId &&
      parsed.workout_id === workoutId &&
      Array.isArray(parsed.queue) &&
      parsed.queue.length <= MAX_QUEUE_LENGTH &&
      snapshotValid &&
      parsed.queue.every(
        (item) =>
          validMutation(item) &&
          (!validSetIds || validSetIds.has(item.set_id)) &&
          (!snapshotSetIds || snapshotSetIds.has(item.set_id)),
      );
    if (valid) return parsed as ActiveWorkoutQueue;
    localStorage.removeItem(key);
  } catch {
    try {
      localStorage.removeItem(key);
    } catch {
      // Storage can be unavailable in restrictive webviews.
    }
  }
  return emptyActiveWorkoutQueue(userId, workoutId);
}

export function saveActiveWorkoutQueue(state: ActiveWorkoutQueue): boolean {
  const key = activeWorkoutQueueKey(state.user_id, state.workout_id);
  try {
    if (state.queue.length === 0 && !state.workout_snapshot) localStorage.removeItem(key);
    else localStorage.setItem(key, JSON.stringify(state));
    return true;
  } catch {
    // The live form still works when durable storage is unavailable.
    return false;
  }
}

export function createWorkoutMutationId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `fallback-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}-${Math.random().toString(36).slice(2)}`;
}

export function enqueueWorkoutMutation(
  state: ActiveWorkoutQueue,
  input: {
    setId: number;
    serverVersion: number;
    values: ActiveWorkoutSetValues;
    inFlightMutationId?: string | null;
    now?: number;
  },
): ActiveWorkoutQueue {
  const queue = [...state.queue];
  let replaceIndex = -1;
  for (let index = queue.length - 1; index >= 0; index -= 1) {
    const item = queue[index]!;
    if (item.set_id === input.setId && item.mutation_id !== input.inFlightMutationId) {
      replaceIndex = index;
      break;
    }
  }
  const previous = [...queue].reverse().find((item) => item.set_id === input.setId);
  const expectedVersion =
    replaceIndex >= 0
      ? queue[replaceIndex]!.expected_version
      : Math.max(input.serverVersion, previous ? previous.expected_version + 1 : 1);
  const mutation: ActiveWorkoutMutation = {
    mutation_id: createWorkoutMutationId(),
    set_id: input.setId,
    expected_version: expectedVersion,
    values: input.values,
    created_at: input.now ?? Date.now(),
  };
  if (replaceIndex >= 0) queue[replaceIndex] = mutation;
  else queue.push(mutation);
  return { ...state, queue: queue.slice(-MAX_QUEUE_LENGTH) };
}

export function acknowledgeWorkoutMutation(
  state: ActiveWorkoutQueue,
  mutationId: string,
  serverVersion: number,
): ActiveWorkoutQueue {
  const acknowledged = state.queue.find((item) => item.mutation_id === mutationId);
  if (!acknowledged) return state;
  const queue = state.queue.filter((item) => item.mutation_id !== mutationId);
  const nextIndex = queue.findIndex((item) => item.set_id === acknowledged.set_id);
  if (nextIndex >= 0) {
    queue[nextIndex] = { ...queue[nextIndex]!, expected_version: serverVersion };
  }
  return { ...state, queue };
}

export function resolveWorkoutVersionConflict(
  state: ActiveWorkoutQueue,
  mutationId: string,
  serverVersion: number,
): ActiveWorkoutQueue {
  const index = state.queue.findIndex((item) => item.mutation_id === mutationId);
  if (index < 0) return state;
  const current = state.queue[index]!;
  const queue = [...state.queue];
  const newerIndex = queue.findIndex(
    (item, itemIndex) => itemIndex > index && item.set_id === current.set_id,
  );
  if (newerIndex >= 0) {
    queue.splice(index, 1);
    const adjustedIndex = newerIndex - 1;
    queue[adjustedIndex] = { ...queue[adjustedIndex]!, expected_version: serverVersion };
  } else {
    queue[index] = { ...current, expected_version: serverVersion };
  }
  return { ...state, queue };
}

export function latestMutationForSet(
  state: ActiveWorkoutQueue,
  setId: number,
): ActiveWorkoutMutation | undefined {
  return [...state.queue].reverse().find((item) => item.set_id === setId);
}

export function clearActiveWorkoutDataForUser(userId: number): void {
  const prefixes = [
    `${ACTIVE_WORKOUT_QUEUE_PREFIX}user_${userId}_`,
    `${ACTIVE_WORKOUT_REST_PREFIX}user_${userId}_`,
    'fit_workout_set_',
    'fit_workout_pending_',
    'fit_workout_rest_deadline_',
  ];
  try {
    const keys = Array.from({ length: localStorage.length }, (_, index) => localStorage.key(index));
    for (const key of keys) {
      if (key && prefixes.some((prefix) => key.startsWith(prefix))) localStorage.removeItem(key);
    }
    localStorage.removeItem(`${ACTIVE_WORKOUT_POINTER_PREFIX}${userId}`);
  } catch {
    // Storage is optional in restrictive webviews.
  }
}

function readLegacySetValue(key: string): Record<string, unknown> | null {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return null;
    const parsed = JSON.parse(raw) as unknown;
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

function legacyField(
  primary: Record<string, unknown> | null,
  secondary: Record<string, unknown> | null,
  field: string,
  fallback: unknown,
): unknown {
  if (primary && Object.hasOwn(primary, field)) return primary[field];
  if (secondary && Object.hasOwn(secondary, field)) return secondary[field];
  return fallback;
}

export function saveActiveWorkoutSnapshot(
  userId: number,
  workout: Workout,
): ActiveWorkoutQueue | undefined {
  if (workout.status !== 'in_progress') return undefined;
  const pointerKey = `${ACTIVE_WORKOUT_POINTER_PREFIX}${userId}`;
  try {
    const previousWorkoutId = Number(localStorage.getItem(pointerKey));
    if (
      Number.isInteger(previousWorkoutId) &&
      previousWorkoutId > 0 &&
      previousWorkoutId !== workout.id
    ) {
      localStorage.removeItem(activeWorkoutQueueKey(userId, previousWorkoutId));
      localStorage.removeItem(activeWorkoutRestKey(userId, previousWorkoutId));
    }
    const setIds = new Set(
      workout.exercises.flatMap((exercise) => exercise.sets.map((set) => set.id)),
    );
    let current = loadActiveWorkoutQueue(userId, workout.id, setIds);
    const legacyKeys: string[] = [];
    for (const set of workout.exercises.flatMap((exercise) => exercise.sets)) {
      const draftKey = `fit_workout_set_${set.id}`;
      const pendingKey = `fit_workout_pending_${set.id}`;
      const draft = readLegacySetValue(draftKey);
      const pending = readLegacySetValue(pendingKey);
      if (draft === null && pending === null) continue;
      legacyKeys.push(draftKey, pendingKey);
      if (current.queue.some((item) => item.set_id === set.id)) continue;
      const actualReps = legacyField(pending, draft, 'actual_reps', set.actual_reps ?? null);
      const actualWeight = legacyField(pending, draft, 'actual_weight', set.actual_weight ?? null);
      const isCompleted = legacyField(pending, null, 'is_completed', set.is_completed);
      if (
        !validNullableNumber(actualReps, true) ||
        !validNullableNumber(actualWeight, false) ||
        typeof isCompleted !== 'boolean'
      )
        continue;
      current = enqueueWorkoutMutation(current, {
        setId: set.id,
        serverVersion: set.version,
        values: {
          actual_reps: actualReps,
          actual_weight: actualWeight,
          is_completed: isCompleted,
        },
      });
    }
    const next = { ...current, workout_snapshot: workout };
    if (saveActiveWorkoutQueue(next)) {
      for (const legacyKey of legacyKeys) localStorage.removeItem(legacyKey);
      localStorage.setItem(pointerKey, String(workout.id));
      return next;
    }
  } catch {
    // The live form still works when durable storage is unavailable.
  }
  return undefined;
}

export function loadCurrentActiveWorkoutSnapshot(userId: number): Workout | undefined {
  try {
    const pointerKey = `${ACTIVE_WORKOUT_POINTER_PREFIX}${userId}`;
    const workoutId = Number(localStorage.getItem(pointerKey));
    if (!Number.isInteger(workoutId) || workoutId <= 0) {
      localStorage.removeItem(pointerKey);
      return undefined;
    }
    return loadActiveWorkoutQueue(userId, workoutId).workout_snapshot;
  } catch {
    return undefined;
  }
}

export function clearActiveWorkoutData(userId: number, workoutId: number): void {
  try {
    localStorage.removeItem(activeWorkoutQueueKey(userId, workoutId));
    localStorage.removeItem(activeWorkoutRestKey(userId, workoutId));
    const pointerKey = `${ACTIVE_WORKOUT_POINTER_PREFIX}${userId}`;
    if (localStorage.getItem(pointerKey) === String(workoutId)) localStorage.removeItem(pointerKey);
  } catch {
    // Storage is optional in restrictive webviews.
  }
}
