import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NutritionForm } from '../../../../src/features/nutrition/NutritionForm';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 10 } }),
}));

function renderForm() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <NutritionForm />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('NutritionForm', () => {
  beforeEach(() => {
    localStorage.clear();
    apiMock.mockReset();
    apiMock.mockResolvedValue({});
  });

  afterEach(cleanup);

  it('shows plain-language daily activity, goals and calculation details', () => {
    renderForm();

    expect(
      screen.getByRole('combobox', { name: /Как проходит большая часть/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('combobox', { name: /Сколько шагов вы обычно проходите/ }),
    ).toBeInTheDocument();
    expect(screen.getByText('Сохранять текущий вес и форму.')).toBeInTheDocument();
    expect(screen.getByText(/Не учитывайте здесь отдельную ходьбу/)).toBeInTheDocument();
    expect(screen.getByText('Целевая калорийность')).toBeInTheDocument();
    expect(
      screen.getByText('Стартовый ориентир. Проверьте результат по динамике за 14–21 день.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Точность стартовой оценки: высокая.')).toBeInTheDocument();
    expect(screen.getByText(/Смарт-часы и фитнес-браслеты оценивают/)).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/MET/i);
    expect(document.body).not.toHaveTextContent(/×\s*1[.,]5/);
  });

  it('adds and removes separately configured cardio trainings', () => {
    renderForm();

    fireEvent.click(screen.getByRole('button', { name: 'Добавить кардио' }));
    expect(screen.getByText('Кардио 1')).toBeInTheDocument();
    expect(screen.getByLabelText('Вид')).toHaveValue('walking');
    expect(screen.getByRole('combobox', { name: /Интенсивность/ })).toHaveValue('moderate');

    fireEvent.change(screen.getByRole('combobox', { name: /Интенсивность/ }), {
      target: { value: 'hard' },
    });
    expect(screen.getByText('Могу произнести только несколько слов подряд.')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Удалить кардио 1' }));
    expect(screen.queryByLabelText('Вид')).not.toBeInTheDocument();
    expect(screen.getByText('Если кардио нет, ничего добавлять не нужно.')).toBeInTheDocument();
  });

  it('lowers confidence when steps are unknown', () => {
    renderForm();

    fireEvent.change(screen.getByRole('combobox', { name: /Сколько шагов/ }), {
      target: { value: 'unknown' },
    });

    expect(screen.getByText('Точность стартовой оценки: низкая.')).toBeInTheDocument();
  });

  it('submits only the new detailed activity fields', async () => {
    renderForm();
    fireEvent.click(screen.getByRole('button', { name: 'Добавить кардио' }));
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить КБЖУ' }));

    await waitFor(() => expect(apiMock).toHaveBeenCalledOnce());
    const options = apiMock.mock.calls[0]![1];
    expect(options.body).toMatchObject({
      daily_routine: 'mixed',
      steps_range: 'from_7000_to_10000',
      strength_training_type: 'regular',
      cardio_trainings: [
        {
          kind: 'walking',
          trainings_per_week: 2,
          duration_minutes: 30,
          intensity: 'moderate',
        },
      ],
    });
    expect(options.body).not.toHaveProperty('daily_activity_level');
    expect(options.body).not.toHaveProperty('cardio_trainings_per_week');
    expect(options.body).not.toHaveProperty('cardio_intensity');
  });
});
