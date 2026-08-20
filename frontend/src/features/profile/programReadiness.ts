import type { UserProfile } from '../../shared/api/types';

export type ProgramProfileReadiness = {
  completed: number;
  total: number;
  isComplete: boolean;
};

export function programProfileReadiness(
  profile: UserProfile | null | undefined,
): ProgramProfileReadiness {
  const fields = [
    Boolean(profile?.goal),
    Boolean(profile?.level),
    typeof profile?.workouts_per_week === 'number' && profile.workouts_per_week > 0,
  ];
  const completed = fields.filter(Boolean).length;
  return { completed, total: fields.length, isComplete: completed === fields.length };
}
