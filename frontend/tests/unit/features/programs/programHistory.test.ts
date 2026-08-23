import { describe, expect, it } from 'vitest';
import {
  buildRevisionPresentation,
  formatRevisionMoment,
  primaryBlockHeading,
  primaryTrainingBlock,
  revisionWorkoutSnapshot,
  type ProgramRevision,
  type TrainingBlock,
} from '../../../../src/features/programs/programHistory';

describe('formatRevisionMoment', () => {
  it('показывает время ревизии без технических секунд', () => {
    expect(formatRevisionMoment('2026-08-21T12:34:56')).toMatch(/^21\.08\.2026, 12:34$/);
  });
});

function revision(overrides: Partial<ProgramRevision> = {}): ProgramRevision {
  return {
    id: 2,
    user_program_id: 77,
    revision_number: 2,
    changed_by_user_id: 11,
    actor_role: 'trainer',
    change_kind: 'block_updated',
    reason: 'Снизить нагрузку перед следующим этапом',
    changed_fields: { block_id: 301, fields: ['purpose', 'is_deload'] },
    snapshot: {},
    created_at: '2026-08-22T12:00:00',
    ...overrides,
  };
}

function block(overrides: Partial<TrainingBlock> = {}): TrainingBlock {
  return {
    id: 301,
    user_program_id: 77,
    title: 'Техническая база',
    start_date: '2026-08-03',
    end_date: '2026-08-23',
    duration_days: 21,
    purpose: 'Закрепить технику',
    priority_muscle_ids: [],
    notes: null,
    is_deload: false,
    status: 'planned',
    created_by_user_id: 1,
    created_at: '2026-08-03T08:00:00',
    updated_at: null,
    ...overrides,
  };
}

describe('program history presentation', () => {
  it('builds a readable before-to-after block diff and uses workouts from that revision snapshot', () => {
    const oldBlock = block();
    const nextBlock = block({
      purpose: 'Закрепить технику и снизить накопленный объём',
      is_deload: true,
      status: 'active',
    });
    const workout = {
      id: 42,
      scheduled_date: '2026-08-20',
      title: 'Силовая база',
      status: 'completed',
      exercises: [],
    };
    const previous = revision({
      id: 1,
      revision_number: 1,
      snapshot: { training_blocks: [oldBlock], workouts: [workout] },
    });
    const current = revision({
      snapshot: { training_blocks: [nextBlock], workouts: [workout] },
    });

    const presentation = buildRevisionPresentation(current, previous);

    expect(presentation.differences).toEqual([
      {
        label: 'Цель',
        before: 'Закрепить технику',
        after: 'Закрепить технику и снизить накопленный объём',
      },
      { label: 'Облегчённый период', before: 'Нет', after: 'Да' },
      { label: 'Статус', before: 'Запланирован', after: 'Идёт сейчас' },
    ]);
    expect(presentation.workoutContextLabel).toBe('Тренировки этапа в версии v2');
    expect(presentation.workouts).toEqual([
      {
        id: 42,
        scheduledDate: '2026-08-20',
        status: 'completed',
        title: 'Силовая база',
      },
    ]);
  });

  it('ties a plan revision only to workouts whose saved structure changed', () => {
    const unchanged = {
      id: 41,
      scheduled_date: '2026-08-10',
      day_number: 1,
      title: 'Завершённая тренировка',
      status: 'planned',
      exercises: [{ exercise_id: 1 }],
    };
    const before = {
      id: 42,
      scheduled_date: '2026-08-24',
      day_number: 1,
      title: 'Будущая тренировка',
      status: 'planned',
      exercises: [{ exercise_id: 1 }],
    };
    const after = { ...before, exercises: [{ exercise_id: 1 }, { exercise_id: 2 }] };
    const previous = revision({
      id: 1,
      revision_number: 1,
      change_kind: 'assigned',
      changed_fields: {},
      snapshot: { workouts: [unchanged, before] },
    });
    const current = revision({
      change_kind: 'plan_updated',
      changed_fields: { day_number: 1, workouts_updated: 1 },
      snapshot: { workouts: [{ ...unchanged, status: 'completed' }, after] },
    });

    const presentation = buildRevisionPresentation(current, previous);

    expect(presentation.workouts.map((item) => item.id)).toEqual([42]);
    expect(presentation.differences).toEqual([
      { label: 'Обновлено тренировок', before: '0', after: '1' },
      { label: 'День программы', before: 'Без изменения', after: 'День 1' },
    ]);
  });

  it('reads the exact exercise prescription from a selected revision snapshot', () => {
    const selected = revision({
      revision_number: 3,
      snapshot: {
        workouts: [
          {
            id: 943,
            scheduled_date: '2026-08-20',
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
                notes: 'Сохранённая подсказка',
              },
            ],
          },
        ],
      },
    });

    expect(revisionWorkoutSnapshot(selected, 943)).toEqual({
      id: 943,
      scheduledDate: '2026-08-20',
      status: 'completed',
      title: 'Контекст версии',
      dayNumber: 2,
      weekNumber: 3,
      exercises: [
        {
          exerciseId: 11,
          notes: 'Сохранённая подсказка',
          prescribedReps: '8–10',
          prescribedSets: 3,
          restSeconds: 90,
          sortOrder: 1,
        },
      ],
    });
  });

  it('prioritizes active, planned, completed and archived blocks in that order', () => {
    const archived = block({ id: 1, status: 'archived' });
    const completed = block({ id: 2, status: 'completed' });
    const planned = block({ id: 3, status: 'planned' });
    const active = block({ id: 4, status: 'active' });

    expect(primaryTrainingBlock([archived, completed, planned, active])).toBe(active);
    expect(primaryTrainingBlock([archived, completed, planned])).toBe(planned);
    expect(primaryTrainingBlock([archived, completed])).toBe(completed);
    expect(primaryTrainingBlock([archived])).toBe(archived);
    expect(primaryBlockHeading(active)).toBe('Текущий тренировочный блок');
  });
});
