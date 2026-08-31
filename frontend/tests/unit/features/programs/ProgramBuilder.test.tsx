import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProgramBuilder } from '../../../../src/features/programs/ProgramBuilder';
import { NavigationProvider } from '../../../../src/shared/navigation/router';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.fn();
const reloadUser = vi.fn();

vi.mock('../../../../src/shared/api/client', async () => {
  const actual = await vi.importActual('../../../../src/shared/api/client');
  return { ...actual, api: (...args: unknown[]) => apiMock(...args) };
});

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: { id: 7, profile: { timezone: 'Europe/Moscow' } },
    reloadUser,
  }),
}));

const catalog = [
  {
    id: 11,
    title: 'Жим штанги лёжа',
    slug: 'bench-press',
    metric_type: 'strength',
    primary_muscle: 'Грудь',
    equipment: 'Штанга',
    primary_muscle_ids: ['chest'],
    secondary_muscle_ids: ['triceps'],
    equipment_ids: ['barbell'],
    aliases: [],
    movement_pattern: 'chest_press',
    machine_variant_tags: [],
    execution_variant_tags: ['bilateral'],
    alternatives: [],
    difficulty_level: 'beginner',
    is_custom: false,
    is_personalized: false,
    has_guide: false,
  },
  {
    id: 12,
    title: 'Велотренажёр',
    slug: 'stationary-bike',
    metric_type: 'cardio',
    primary_muscle: 'Кардио',
    equipment: 'Велотренажёр',
    primary_muscle_ids: ['cardio'],
    secondary_muscle_ids: [],
    equipment_ids: ['cardio'],
    aliases: [],
    movement_pattern: null,
    machine_variant_tags: [],
    execution_variant_tags: ['cyclic'],
    alternatives: [],
    difficulty_level: 'beginner',
    is_custom: false,
    is_personalized: false,
    has_guide: false,
  },
  {
    id: 13,
    title: 'Верхняя рычажная тяга с упором грудью',
    slug: 'lever-high-row',
    metric_type: 'strength',
    primary_muscle: 'Спина',
    equipment: 'Тренажёр',
    primary_muscle_ids: ['back'],
    secondary_muscle_ids: ['biceps', 'posterior_deltoid', 'forearms'],
    equipment_ids: ['machine'],
    aliases: ['верхняя тяга хаммер', 'high row'],
    movement_pattern: 'row',
    machine_variant_tags: ['plate_loaded', 'lever', 'independent'],
    execution_variant_tags: ['bilateral', 'unilateral'],
    alternatives: [],
    difficulty_level: 'beginner',
    is_custom: false,
    is_personalized: false,
    has_guide: true,
  },
];

function renderBuilder() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <NavigationProvider>
          <ProgramBuilder defaultOpen />
        </NavigationProvider>
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('ProgramBuilder type-aware prescription', () => {
  beforeEach(() => {
    localStorage.clear();
    Object.defineProperty(Element.prototype, 'scrollIntoView', {
      configurable: true,
      value: vi.fn(),
    });
    apiMock.mockReset();
    reloadUser.mockReset();
    apiMock.mockImplementation((path: string) => {
      if (path === '/api/v1/programs/exercises') return Promise.resolve(catalog);
      if (path === '/api/v1/programs/templates') return Promise.resolve({ template: { id: 1 } });
      throw new Error(`Unexpected API path: ${path}`);
    });
  });

  afterEach(cleanup);

  it('для cardio запрашивает длительность и не отправляет силовое назначение', async () => {
    const user = userEvent.setup();
    renderBuilder();

    const picker = await screen.findByRole('combobox', { name: 'Поиск упражнения' });
    await user.click(picker);
    await user.click(screen.getByRole('option', { name: /Велотренажёр/ }));

    const duration = screen.getByRole('spinbutton', { name: 'Плановая длительность, мин' });
    const exerciseRow = duration.closest<HTMLElement>('.program-exercise-row');
    expect(exerciseRow).not.toBeNull();
    expect(duration).toHaveValue(30);
    expect(within(exerciseRow!).queryByText('Рабочие подходы')).not.toBeInTheDocument();
    expect(within(exerciseRow!).queryByText('Повторы')).not.toBeInTheDocument();
    expect(within(exerciseRow!).queryByText('Отдых, сек')).not.toBeInTheDocument();
    await user.clear(duration);
    await user.type(duration, '25');
    await user.click(screen.getByRole('button', { name: 'Создать программу' }));

    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith(
        '/api/v1/programs/templates',
        expect.objectContaining({
          method: 'POST',
          body: expect.objectContaining({
            days: [
              expect.objectContaining({
                exercises: [
                  expect.objectContaining({
                    exercise_id: 12,
                    prescribed_sets: null,
                    prescribed_reps: null,
                    prescribed_duration_minutes: 25,
                  }),
                ],
              }),
            ],
          }),
        }),
      ),
    );
  });

  it('находит machine/lever упражнение по разговорному alias и добавляет canonical item', async () => {
    const user = userEvent.setup();
    renderBuilder();

    const picker = await screen.findByRole('combobox', { name: 'Поиск упражнения' });
    await user.type(picker, 'верхняя тяга хаммер');

    const listbox = screen.getByRole('listbox');
    const option = within(listbox).getByRole('option', {
      name: /Верхняя рычажная тяга с упором грудью/,
    });
    expect(option).toBeVisible();
    expect(within(listbox).getAllByRole('option')).toHaveLength(1);
    await user.click(option);

    await waitFor(() =>
      expect(screen.getByRole('combobox', { name: 'Поиск упражнения' })).toHaveValue(
        'Верхняя рычажная тяга с упором грудью',
      ),
    );
    expect(screen.getByRole('spinbutton', { name: 'Рабочие подходы' })).toBeVisible();
  });
});
