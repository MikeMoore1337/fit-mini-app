import type { ProgramTemplateCreate } from '../../shared/api/types';

type ProgramDay = ProgramTemplateCreate['days'][number];

export function moveItem<T>(items: T[], from: number, to: number): T[] {
  if (from === to || from < 0 || to < 0 || from >= items.length || to >= items.length) return items;
  const next = [...items];
  const [moved] = next.splice(from, 1);
  next.splice(to, 0, moved!);
  return next;
}

export function removeExercise(day: ProgramDay, index: number): ProgramDay {
  const removedGroup = day.exercises[index]?.superset_group;
  return {
    ...day,
    exercises: day.exercises
      .filter((_, exerciseIndex) => exerciseIndex !== index)
      .map((exercise) =>
        removedGroup != null && exercise.superset_group === removedGroup
          ? { ...exercise, superset_group: null, superset_order: null }
          : exercise,
      ),
  };
}

export function toggleSuperset(day: ProgramDay, secondIndex: number, enabled: boolean): ProgramDay {
  if (secondIndex <= 0 || secondIndex >= day.exercises.length) return day;
  const firstIndex = secondIndex - 1;
  const affectedGroups = new Set(
    [day.exercises[firstIndex]?.superset_group, day.exercises[secondIndex]?.superset_group].filter(
      (group): group is number => group != null,
    ),
  );
  const cleared = day.exercises.map((exercise) =>
    exercise.superset_group != null && affectedGroups.has(exercise.superset_group)
      ? { ...exercise, superset_group: null, superset_order: null }
      : exercise,
  );
  if (!enabled) return { ...day, exercises: cleared };

  const nextGroup = Math.max(0, ...cleared.map((exercise) => exercise.superset_group ?? 0)) + 1;
  return {
    ...day,
    exercises: cleared.map((exercise, index) =>
      index === firstIndex
        ? { ...exercise, superset_group: nextGroup, superset_order: 1 }
        : index === secondIndex
          ? { ...exercise, superset_group: nextGroup, superset_order: 2 }
          : exercise,
    ),
  };
}

export function isPairedWithPrevious(day: ProgramDay, index: number): boolean {
  if (index <= 0) return false;
  const previous = day.exercises[index - 1];
  const current = day.exercises[index];
  return Boolean(
    previous?.superset_group &&
    previous.superset_group === current?.superset_group &&
    previous.superset_order === 1 &&
    current.superset_order === 2,
  );
}
