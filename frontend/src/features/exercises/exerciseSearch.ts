import type { Exercise } from '../../shared/api/types';

export function matchesExerciseSearch(exercise: Exercise, rawQuery: string): boolean {
  const query = rawQuery.trim().toLocaleLowerCase('ru-RU');
  if (!query) return true;

  const haystack = [
    exercise.title,
    exercise.primary_muscle ?? '',
    exercise.equipment ?? '',
    ...(exercise.aliases ?? []),
    ...(exercise.alternatives ?? []).map((alternative) => alternative.title),
  ]
    .join(' ')
    .toLocaleLowerCase('ru-RU');

  return haystack.includes(query);
}
