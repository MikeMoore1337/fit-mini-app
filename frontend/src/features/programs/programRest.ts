import type { ProgramTemplateCreate } from '../../shared/api/types';

type ProgramDay = ProgramTemplateCreate['days'][number];

export function applyRestSeconds(days: ProgramDay[], restSeconds: number): ProgramDay[] {
  return days.map((day) => ({
    ...day,
    exercises: day.exercises.map((exercise) => ({ ...exercise, rest_seconds: restSeconds })),
  }));
}
