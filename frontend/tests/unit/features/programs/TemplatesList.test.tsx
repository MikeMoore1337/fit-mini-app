import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { TemplatesList } from '../../../../src/features/programs/TemplatesList';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: { id: 1, profile: { timezone: 'Europe/Moscow' } },
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
      return new Response(JSON.stringify({ detail: 'Unexpected request' }), { status: 500 });
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('opens a personal copy editor for a ready-made template', async () => {
    renderList();

    fireEvent.click(await screen.findByRole('button', { name: 'Редактировать копию' }));

    expect(screen.getByText('copy:Готовый шаблон')).toBeInTheDocument();
  });

  it('updates an owned template directly', async () => {
    renderList();

    const programCard = (await screen.findByText('Моя программа')).closest('article');
    expect(programCard).not.toBeNull();
    fireEvent.click(within(programCard!).getByRole('button', { name: 'Редактировать' }));

    expect(screen.getByText('update:Моя программа')).toBeInTheDocument();
  });

  it('shows that the active program is already assigned', async () => {
    renderList();

    expect(await screen.findByRole('button', { name: 'Уже назначена' })).toBeDisabled();
  });
});
