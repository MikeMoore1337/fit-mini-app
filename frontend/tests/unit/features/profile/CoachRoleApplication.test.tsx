import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CoachRoleApplicationCard } from '../../../../src/features/profile/CoachRoleApplication';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';

const apiMock = vi.hoisted(() => vi.fn());
const authState = vi.hoisted(() => ({ isCoach: false, isAdmin: false }));

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: { id: 10, is_coach: authState.isCoach, is_admin: authState.isAdmin },
  }),
}));

function renderCard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FeedbackProvider>
        <CoachRoleApplicationCard />
      </FeedbackProvider>
    </QueryClientProvider>,
  );
}

describe('CoachRoleApplicationCard', () => {
  beforeEach(() => {
    authState.isCoach = false;
    authState.isAdmin = false;
    apiMock.mockReset();
  });

  afterEach(cleanup);

  it('отправляет заявку из приложения после подтверждения', async () => {
    apiMock.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === '/api/v1/me/coach-application' && options?.method === 'POST') {
        return Promise.resolve({ id: 1, status: 'pending' });
      }
      return Promise.resolve(null);
    });
    renderCard();

    fireEvent.click(await screen.findByRole('button', { name: 'Стать тренером' }));
    fireEvent.click(screen.getByRole('button', { name: 'Отправить заявку' }));

    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith('/api/v1/me/coach-application', { method: 'POST' }),
    );
    expect(screen.queryByText(/Telegram-бота/)).not.toBeInTheDocument();
  });

  it('показывает статус и позволяет отменить ожидающую заявку', async () => {
    apiMock.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === '/api/v1/me/coach-application' && options?.method === 'DELETE') {
        return Promise.resolve(undefined);
      }
      return Promise.resolve({ id: 1, status: 'pending', source: 'web' });
    });
    renderCard();

    expect(await screen.findByText('Заявка отправлена')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Отменить заявку' }));

    await waitFor(() =>
      expect(apiMock).toHaveBeenCalledWith('/api/v1/me/coach-application', { method: 'DELETE' }),
    );
  });

  it('не показывается пользователю с ролью тренера', () => {
    authState.isCoach = true;
    renderCard();

    expect(screen.queryByText('Стать тренером')).not.toBeInTheDocument();
    expect(apiMock).not.toHaveBeenCalled();
  });
});
