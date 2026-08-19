import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { TemplatesList } from '../../../../src/features/programs/TemplatesList';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      profile: {
        timezone: 'Europe/Moscow',
        goal: 'recomposition',
        level: 'beginner',
        workouts_per_week: 3,
      },
    },
    reloadUser: vi.fn(),
  }),
}));

vi.mock('../../../../src/features/programs/ProgramBuilder', () => ({
  ProgramBuilder: ({
    editingTemplate,
    saveAsCopy,
  }: {
    editingTemplate: { title: string };
    saveAsCopy: boolean;
  }) => <div>{`${saveAsCopy ? 'copy' : 'update'}:${editingTemplate.title}`}</div>,
}));

const templateBase = {
  slug: 'template',
  goal: 'recomposition',
  level: 'intermediate',
  owner_user_id: null,
  owner_telegram_user_id: null,
  owner_full_name: null,
  created_by_user_id: null,
  is_public: true,
  is_assigned_to_current_user: false,
  is_active_for_current_user: false,
  assigned_by_user_id: null,
  assigned_by_full_name: null,
  days: [
    {
      id: 1,
      day_number: 1,
      title: 'День 1',
      exercises: [
        {
          id: 1,
          exercise_id: 1,
          exercise_title: 'Приседания',
          prescribed_sets: 3,
          prescribed_reps: '8',
          rest_seconds: 90,
          notes: null,
          has_guide: true,
        },
      ],
    },
  ],
};

function renderList() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <TemplatesList />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('TemplatesList editing', () => {
  beforeEach(() => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const path = String(input);
      if (path === '/api/v1/programs/templates/mine') {
        return new Response(
          JSON.stringify([
            {
              ...templateBase,
              id: 10,
              title: 'Готовый шаблон',
              is_example: true,
              can_edit: false,
            },
            {
              ...templateBase,
              id: 11,
              title: 'Моя программа',
              slug: 'custom-template',
              is_example: false,
              can_edit: true,
              is_public: false,
              owner_user_id: 1,
            },
            {
              ...templateBase,
              id: 12,
              title: 'Активная программа',
              slug: 'active-template',
              is_example: false,
              can_edit: true,
              is_public: false,
              owner_user_id: 1,
              is_active_for_current_user: true,
            },
          ]),
          { status: 200 },
        );
      }
      if (path === '/api/v1/programs/templates/hidden') {
        return new Response(JSON.stringify([]), { status: 200 });
      }
      if (path === '/api/v1/programs/templates/recommendation') {
        return new Response(
          JSON.stringify({
            status: 'recommended',
            criteria: {
              goal: 'recomposition',
              experience: 'beginner',
              workouts_per_week: 3,
              training_location: null,
              available_equipment_ids: null,
              profile_fields_used: [],
            },
            missing_fields: [],
            message: 'Сначала посмотрите состав программы.',
            recommendation: {
              template: {
                ...templateBase,
                id: 20,
                title: 'Фуллбади по правилам',
                split_type: 'full_body',
                is_example: true,
                can_edit: false,
              },
              reason: 'Подходит по цели, уровню и частоте.',
              fit_facts: ['Три тренировки за цикл.'],
              limitations: ['Оборудование не проверялось.'],
            },
            alternatives: [],
            requires_explicit_start: true,
          }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('opens a personal copy editor for a ready-made template', async () => {
    renderList();

    fireEvent.click(await screen.findByRole('button', { name: 'Настроить копию' }));

    expect(screen.getByText('copy:Готовый шаблон')).toBeInTheDocument();
  });

  it('updates an owned template directly', async () => {
    renderList();

    const programCard = (
      await screen.findByRole('button', { name: 'Посмотреть программу «Моя программа»' })
    ).closest('article');
    expect(programCard).not.toBeNull();
    fireEvent.click(within(programCard!).getByRole('button', { name: 'Редактировать' }));

    expect(screen.getByText('update:Моя программа')).toBeInTheDocument();
  });

  it('shows that the active program is already assigned', async () => {
    renderList();

    expect(await screen.findByRole('heading', { name: 'Активная программа' })).toBeInTheDocument();
    expect(screen.getByText('Активна')).toBeInTheDocument();
  });

  it('previews a deterministic recommendation before explicit start', async () => {
    renderList();

    fireEvent.click(screen.getByRole('button', { name: 'Начать подбор' }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    fireEvent.click(screen.getByRole('radio', { name: /Место не важно/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    fireEvent.click(screen.getByRole('radio', { name: /Не проверять оборудование/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Показать рекомендацию' }));

    expect(await screen.findByText('Фуллбади по правилам')).toBeInTheDocument();
    expect(screen.getByText('Подходит по цели, уровню и частоте.')).toBeInTheDocument();
    expect(screen.getByText('Оборудование не проверялось.')).toBeInTheDocument();

    fireEvent.click(
      within(screen.getByRole('dialog', { name: 'Ваш результат' })).getByRole('button', {
        name: 'Посмотреть план',
      }),
    );
    expect(screen.getByRole('dialog', { name: /Фуллбади по правилам/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Настроить расписание и запустить' }));
    expect(screen.getByRole('dialog', { name: /Фуллбади по правилам/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Назначить по расписанию' }));
    expect(
      await screen.findByRole('dialog', { name: 'Заменить активную программу?' }),
    ).toBeInTheDocument();

    const requestedPaths = vi.mocked(globalThis.fetch).mock.calls.map(([input]) => String(input));
    expect(requestedPaths).toContain('/api/v1/programs/templates/recommendation');
    expect(requestedPaths.some((path) => path.includes('/assign-to-me'))).toBe(false);
  });
});
