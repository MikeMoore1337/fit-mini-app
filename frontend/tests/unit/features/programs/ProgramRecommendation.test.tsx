import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProgramRecommendation } from '../../../../src/features/programs/ProgramRecommendation';

const authState = vi.hoisted(() => ({
  profile: null as {
    goal?: string | null;
    level?: string | null;
    workouts_per_week?: number | null;
  } | null,
}));

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: { profile: authState.profile } }),
}));

const template = {
  id: 20,
  title: 'Программа на всё тело',
  slug: 'full-body',
  goal: 'recomposition',
  level: 'beginner',
  split_type: 'full_body',
  owner_user_id: null,
  owner_telegram_user_id: null,
  owner_full_name: null,
  created_by_user_id: null,
  is_public: true,
  is_example: true,
  is_assigned_to_current_user: false,
  is_active_for_current_user: false,
  can_edit: false,
  assigned_by_user_id: null,
  assigned_by_full_name: null,
  days: [
    {
      id: 1,
      day_number: 1,
      title: 'Всё тело',
      exercises: [],
    },
  ],
};

function renderWizard(onPreview = vi.fn(), onEditCopy = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <ProgramRecommendation
        open
        onEditCopy={onEditCopy}
        onOpenChange={vi.fn()}
        onPreview={onPreview}
      />
    </QueryClientProvider>,
  );
}

describe('ProgramRecommendation wizard', () => {
  beforeEach(() => {
    authState.profile = null;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('collects every criterion, keeps answers on back navigation and sends canonical enums', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          status: 'recommended',
          criteria: {
            goal: 'muscle_gain',
            experience: 'advanced',
            workouts_per_week: 5,
            training_location: 'home',
            available_equipment_ids: ['dumbbell', 'barbell'],
            profile_fields_used: [],
          },
          missing_fields: [],
          message: 'Сначала посмотрите состав программы.',
          recommendation: {
            template,
            reason: 'Подходит по выбранным параметрам.',
            fit_facts: ['Оборудование подходит: гантели, штанга.'],
            limitations: [],
          },
          alternatives: [],
          requires_explicit_start: true,
        }),
        { status: 200 },
      ),
    );
    const onPreview = vi.fn();
    renderWizard(onPreview);

    expect(screen.getByRole('button', { name: 'Далее' })).toBeDisabled();
    expect(screen.getAllByRole('radio')).toHaveLength(5);
    fireEvent.click(screen.getByRole('radio', { name: /Набор мышц/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));

    fireEvent.click(screen.getByRole('radio', { name: /Тренируюсь давно/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    expect(screen.getAllByRole('radio')).toHaveLength(8);
    fireEvent.click(screen.getByRole('radio', { name: /^5тренировки/ }));

    fireEvent.click(screen.getByRole('button', { name: 'Назад' }));
    expect(screen.getByRole('radio', { name: /Тренируюсь давно/ })).toBeChecked();
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    expect(screen.getByRole('radio', { name: /^5тренировки/ })).toBeChecked();
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));

    fireEvent.click(screen.getByRole('radio', { name: /Дома/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    fireEvent.click(screen.getByRole('radio', { name: /Учесть только доступное/ }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'Гантели' }));
    fireEvent.click(screen.getByRole('checkbox', { name: 'Штанга' }));
    fireEvent.click(screen.getByRole('button', { name: 'Показать рекомендацию' }));

    expect(await screen.findByText('Программа на всё тело')).toBeInTheDocument();
    const [, request] = vi.mocked(globalThis.fetch).mock.calls[0]!;
    expect(JSON.parse(String(request?.body))).toEqual({
      goal: 'muscle_gain',
      experience: 'advanced',
      workouts_per_week: 5,
      training_location: 'home',
      available_equipment_ids: ['dumbbell', 'barbell'],
    });
    expect(screen.queryByRole('button', { name: /запустить/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Посмотреть план' }));
    expect(onPreview).toHaveBeenCalledWith(expect.objectContaining({ id: 20 }));
  });

  it('prefills trustworthy profile fields and offers all manual exits for no match', async () => {
    authState.profile = {
      goal: 'strength',
      level: 'intermediate',
      workouts_per_week: 4,
    };
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          status: 'no_match',
          criteria: {
            goal: 'strength',
            experience: 'intermediate',
            workouts_per_week: 4,
            training_location: null,
            available_equipment_ids: null,
            profile_fields_used: [],
          },
          missing_fields: [],
          message: 'Проверенного силового шаблона пока нет.',
          recommendation: null,
          alternatives: [],
          requires_explicit_start: true,
        }),
        { status: 200 },
      ),
    );
    renderWizard();

    expect(screen.getByText(/подставили достоверные ответы из профиля/i)).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: /Увеличение силы/ })).toBeChecked();
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    expect(screen.getByRole('radio', { name: /Тренируюсь регулярно/ })).toBeChecked();
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    expect(screen.getByRole('radio', { name: /^4тренировки/ })).toBeChecked();
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    fireEvent.click(screen.getByRole('radio', { name: /Место не важно/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Далее' }));
    fireEvent.click(screen.getByRole('radio', { name: /Не проверять оборудование/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Показать рекомендацию' }));

    expect(await screen.findByRole('heading', { name: 'Совпадений нет' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Изменить параметры' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Выбрать из шаблонов' })).toHaveAttribute(
      'href',
      '#program-library',
    );
    expect(screen.getByRole('link', { name: 'Создать свою' })).toHaveAttribute(
      'href',
      '#program-builder',
    );
  });
});
