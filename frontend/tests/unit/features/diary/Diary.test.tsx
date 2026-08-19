import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Diary } from '../../../../src/features/diary/Diary';
import { dateInputValue } from '../../../../src/shared/dateTime';
import { queryKeys } from '../../../../src/shared/queryKeys';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 10, profile: { timezone: 'Europe/Moscow' } } }),
}));

function QueryProbe({ clientId, queryFn }: { clientId?: number; queryFn: () => Promise<unknown> }) {
  useQuery({
    queryKey:
      clientId == null
        ? queryKeys.progress.summary(30)
        : queryKeys.trainer.clientAnalytics(clientId),
    queryFn,
  });
  return null;
}

function renderDiary(options?: {
  clientId?: number;
  timeZone?: string;
  dependentQuery?: () => Promise<unknown>;
}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        {options?.dependentQuery && (
          <QueryProbe clientId={options.clientId} queryFn={options.dependentQuery} />
        )}
        <Diary clientId={options?.clientId} timeZone={options?.timeZone} />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('Diary measurement guidance', () => {
  beforeEach(() => {
    localStorage.clear();
    apiMock.mockReset();
    apiMock.mockResolvedValue([]);
  });

  afterEach(cleanup);

  it('uses honest circumference labels and consistency guidance', async () => {
    renderDiary();

    expect(screen.getByLabelText('Плечо (окружность), см')).toBeInTheDocument();
    expect(screen.getByLabelText('Бедро (окружность), см')).toBeInTheDocument();
    expect(screen.getByLabelText('Как делать замеры')).toHaveTextContent(
      'Окружность плеча не показывает отдельно размер бицепса',
    );
    expect(await screen.findByText('Замеров пока нет')).toBeInTheDocument();
  });

  it('refetches personal progress after a measurement mutation', async () => {
    const dependentQuery = vi.fn().mockResolvedValue({});
    renderDiary({ dependentQuery });
    await waitFor(() => expect(dependentQuery).toHaveBeenCalledOnce());

    fireEvent.change(screen.getByLabelText('Вес, кг'), { target: { value: '74' } });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить замер' }));

    await waitFor(() => expect(dependentQuery).toHaveBeenCalledTimes(2));
  });

  it('uses the client timezone and refetches trainer analytics', async () => {
    const dependentQuery = vi.fn().mockResolvedValue({});
    const timeZone = 'Pacific/Kiritimati';
    renderDiary({ clientId: 42, timeZone, dependentQuery });
    const dateInput = screen.getByLabelText('Дата');
    const clientToday = dateInputValue(new Date(), timeZone);
    expect(dateInput).toHaveValue(clientToday);
    expect(dateInput).toHaveAttribute('max', clientToday);
    await waitFor(() => expect(dependentQuery).toHaveBeenCalledOnce());

    fireEvent.change(screen.getByLabelText('Вес, кг'), { target: { value: '75' } });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить замер' }));

    await waitFor(() => expect(dependentQuery).toHaveBeenCalledTimes(2));
  });
});
