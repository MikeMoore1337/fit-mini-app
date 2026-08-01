import type { Exercise, ProgramTemplateCreate } from '../../shared/api/types';

export const difficultyLabels = {
  beginner: 'Начальный',
  intermediate: 'Средний',
  advanced: 'Продвинутый',
} as const;

const difficultyOrder = { beginner: 0, intermediate: 1, advanced: 2 } as const;

export function orderExercisesForLevel(
  exercises: Exercise[],
  selectedLevel: ProgramTemplateCreate['level'],
): Exercise[] {
  return [...exercises].sort((left, right) => {
    const leftGroup =
      left.difficulty_level === selectedLevel ? -1 : difficultyOrder[left.difficulty_level];
    const rightGroup =
      right.difficulty_level === selectedLevel ? -1 : difficultyOrder[right.difficulty_level];
    return leftGroup - rightGroup || left.title.localeCompare(right.title, 'ru');
  });
}
