import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ProfileForm } from '../../../../src/features/profile/ProfileForm';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());
const reloadUser = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 10, profile: null }, reloadUser }),
}));

const previewByGoal = {
  fat_loss: { min_bpm: 130, max_bpm: 140 },
  recomposition: { min_bpm: 124, max_bpm: 140 },
  maintenance: { min_bpm: 119, max_bpm: 140 },
  muscle_gain: { min_bpm: 119, max_bpm: 130 },
} as const;

const zones = [
  { zone: 1, title: 'Восстановление', min_bpm: 130, max_bpm: 140 },
  { zone: 2, title: 'Лёгкая', min_bpm: 140, max_bpm: 151 },
  { zone: 3, title: 'Аэробная', min_bpm: 151, max_bpm: 162 },
  { zone: 4, title: 'Пороговая', min_bpm: 162, max_bpm: 173 },
  { zone: 5, title: 'Максимальная', min_bpm: 173, max_bpm: 184 },
];

function renderForm() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <ProfileForm />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

function birthDateInput(): HTMLInputElement {
  const label = screen.getByText('Дата рождения').closest('label');
  const input = label?.querySelector('input');
  if (!input) throw new Error('Birth date input not found');
  return input;
}

function restingHeartRateInput(): HTMLInputElement {
  const label = screen.getByText('Средний пульс в покое, уд/мин').closest('label');
  const input = label?.querySelector('input');
  if (!input) throw new Error('Resting heart rate input not found');
  return input;
}

describe('ProfileForm heart rate preview', () => {
  beforeEach(() => {
    localStorage.clear();
    apiMock.mockReset();
    apiMock.mockImplementation(
      (path: string, options?: { body: { goal: keyof typeof previewByGoal } }) => {
        if (path.endsWith('/body-priority-options'))
          return Promise.resolve({ items: [{ id: 'chest', name: 'Грудь' }] });
        return Promise.resolve({
          estimated_max_heart_rate: 184,
          heart_rate_reserve: 109,
          heart_rate_calculation_method: 'heart_rate_reserve',
          heart_rate_zones: zones,
          recommended_cardio_range: previewByGoal[options!.body.goal],
        });
      },
    );
  });

  afterEach(cleanup);

  it('updates only the recommendation when the goal changes', async () => {
    renderForm();
    fireEvent.change(birthDateInput(), { target: { value: '1992-08-12' } });
    fireEvent.change(restingHeartRateInput(), {
      target: { value: '75' },
    });
    fireEvent.change(screen.getByLabelText('Цель'), { target: { value: 'fat_loss' } });

    expect((await screen.findAllByText('130–140 уд/мин')).length).toBeGreaterThan(1);
    const zoneList = screen.getByText('Пульсовые зоны').parentElement?.nextElementSibling;
    expect(zoneList).not.toBeNull();
    const initialZones = zoneList?.textContent;

    fireEvent.change(screen.getByLabelText('Цель'), { target: { value: 'recomposition' } });
    await screen.findByText('124–140 уд/мин');

    fireEvent.change(screen.getByLabelText('Цель'), { target: { value: 'maintenance' } });
    await screen.findByText('119–140 уд/мин');

    fireEvent.change(screen.getByLabelText('Цель'), { target: { value: 'muscle_gain' } });
    await screen.findByText('119–130 уд/мин');

    expect(screen.getByText('184 уд/мин')).toBeInTheDocument();
    expect(zoneList?.textContent).toBe(initialZones);
    expect(document.body).not.toHaveTextContent(/HRR|MET/);
  });

  it('treats nonnumeric input as empty and does not preview an out-of-range value', async () => {
    renderForm();
    fireEvent.change(birthDateInput(), { target: { value: '1992-08-12' } });
    const restingHeartRate = restingHeartRateInput();
    fireEvent.change(restingHeartRate, {
      target: { value: 'abc' },
    });
    await waitFor(() =>
      expect(
        apiMock.mock.calls.filter(([path]) => path.endsWith('/heart-rates/preview')),
      ).toHaveLength(1),
    );
    expect(restingHeartRate).toHaveValue(null);
    const previewCall = apiMock.mock.calls.find(([path]) => path.endsWith('/heart-rates/preview'));
    expect(previewCall?.[1].body.resting_heart_rate).toBeNull();

    apiMock.mockClear();
    fireEvent.change(restingHeartRate, {
      target: { value: '121' },
    });
    await new Promise((resolve) => window.setTimeout(resolve, 0));
    expect(
      apiMock.mock.calls.filter(([path]) => path.endsWith('/heart-rates/preview')),
    ).toHaveLength(0);
  });
});
