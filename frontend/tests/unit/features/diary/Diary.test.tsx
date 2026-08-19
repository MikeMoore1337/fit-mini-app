import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { Diary } from '../../../../src/features/diary/Diary';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 10, profile: { timezone: 'Europe/Moscow' } } }),
}));

describe('Diary measurement guidance', () => {
  it('uses honest circumference labels and consistency guidance', async () => {
    apiMock.mockResolvedValue([]);
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <FeedbackProvider>
          <Diary />
        </FeedbackProvider>
      </QueryClientProvider>,
    );

    expect(screen.getByLabelText('Плечо (окружность), см')).toBeInTheDocument();
    expect(screen.getByLabelText('Бедро (окружность), см')).toBeInTheDocument();
    expect(screen.getByLabelText('Как делать замеры')).toHaveTextContent(
      'Окружность плеча не показывает отдельно размер бицепса',
    );
    expect(await screen.findByText('Замеров пока нет')).toBeInTheDocument();
  });
});
