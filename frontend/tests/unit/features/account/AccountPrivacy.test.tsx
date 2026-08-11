import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AccountPrivacy } from '../../../../src/features/account/AccountPrivacy';

const { apiMock, authState, toastMock } = vi.hoisted(() => ({
  apiMock: vi.fn(),
  authState: {
    user: { id: 77, telegram_user_id: null as number | null },
  },
  toastMock: vi.fn(),
}));

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: authState.user, logout: vi.fn() }),
}));
vi.mock('../../../../src/shared/ui/FeedbackProvider', () => ({
  useFeedback: () => ({ toast: toastMock, confirm: vi.fn() }),
}));

function renderPrivacy() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <AccountPrivacy />
    </QueryClientProvider>,
  );
}

describe('AccountPrivacy Telegram linking', () => {
  beforeEach(() => {
    authState.user.telegram_user_id = null;
    apiMock.mockReset();
    toastMock.mockReset();
  });

  afterEach(() => vi.restoreAllMocks());

  it('creates an explicit short-lived link before opening Telegram', async () => {
    apiMock.mockResolvedValue({
      telegram_url: 'https://t.me/fitness_bot?start=link_safe-token',
      expires_in_seconds: 600,
    });
    renderPrivacy();

    fireEvent.click(screen.getByRole('button', { name: 'Привязать Telegram' }));

    const link = await screen.findByRole('link', { name: 'Открыть Telegram' });
    expect(apiMock).toHaveBeenCalledWith('/api/v1/me/auth/telegram-link', {
      method: 'POST',
      body: {},
    });
    expect(link).toHaveAttribute('href', 'https://t.me/fitness_bot?start=link_safe-token');
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('shows linked status and does not offer another link', () => {
    authState.user.telegram_user_id = 12345;
    renderPrivacy();

    expect(screen.getByText('Привязан')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Привязать Telegram' })).not.toBeInTheDocument();
  });
});
