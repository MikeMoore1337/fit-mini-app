import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { HistoricalProgramWorkout } from '../../../../src/features/programs/HistoricalProgramWorkout';
import type { ProgramRevision } from '../../../../src/features/programs/programHistory';

const apiMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', async () => {
  const actual = await vi.importActual<typeof import('../../../../src/shared/api/client')>(
    '../../../../src/shared/api/client',
  );
  return { ...actual, api: apiMock };
});

describe('HistoricalProgramWorkout', () => {
  beforeEach(() => {
    apiMock.mockReset();
  });

  it('renders the selected revision snapshot instead of the current workout with the same id', async () => {
    const revision: ProgramRevision = {
      id: 3,
      user_program_id: 77,
      revision_number: 3,
      changed_by_user_id: 11,
      actor_role: 'trainer',
      change_kind: 'plan_updated',
      reason: 'Изменить будущую тренировку',
      changed_fields: { day_number: 2, workouts_updated: 1 },
      snapshot: {
        workouts: [
          {
            id: 943,
            scheduled_date: '2026-08-22',
            day_number: 2,
            week_number: 3,
            title: 'Контекст версии',
            status: 'completed',
            exercises: [
              {
                exercise_id: 11,
                sort_order: 1,
                prescribed_sets: 3,
                prescribed_reps: '8–10',
                rest_seconds: 90,
                notes: null,
              },
            ],
          },
        ],
      },
      created_at: '2026-08-20T12:00:00',
    };
    apiMock.mockImplementation(async (path: string) => {
      if (path.endsWith('/revisions')) return [revision];
      if (path.endsWith('/exercises')) {
        return [
          {
            id: 11,
            title: 'Присед со штангой',
            primary_muscle_ids: [],
            secondary_muscle_ids: [],
            equipment_ids: [],
            alternatives: [],
            difficulty_level: 'intermediate',
            is_custom: false,
            is_personalized: false,
            has_guide: false,
          },
        ];
      }
      throw new Error(`Unexpected API path: ${path}`);
    });
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <HistoricalProgramWorkout programId={77} revisionNumber={3} workoutId={943} />
      </QueryClientProvider>,
    );

    expect(await screen.findByRole('heading', { name: 'Контекст версии' })).toBeInTheDocument();
    expect(screen.getByText('Снимок программы · v3')).toBeInTheDocument();
    expect(screen.getByText('Присед со штангой')).toBeInTheDocument();
    expect(screen.getByText('3 подх. · 8–10 повт. · отдых 90 сек.')).toBeInTheDocument();
    expect(screen.getByText(/доступен только для просмотра/)).toBeInTheDocument();
  });
});
