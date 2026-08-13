import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AccountPrivacy } from '../../../../src/features/account/AccountPrivacy';

const { apiMock, authState, toastMock } = vi.hoisted(() => ({
  apiMock: vi.fn(),
  authState: {
    user: {
      id: 77,
      telegram_user_id: null as number | null,
      auth_providers: [] as string[],
    },
    config: {
      oauth_providers: [] as string[],
    },
  },
  toastMock: vi.fn(),
}));

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: authState.user, config: authState.config, logout: vi.fn() }),
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
    authState.user.auth_providers = [];
    authState.config.oauth_providers = [];
    apiMock.mockReset();
    toastMock.mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

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

  it('creates an explicit OAuth link for a configured provider', async () => {
    authState.user.auth_providers = ['telegram'];
    authState.config.oauth_providers = ['google'];
    apiMock.mockResolvedValue({
      oauth_url: '/api/v1/auth/oauth/google/link/start?token=safe-token',
      expires_in_seconds: 600,
    });
    renderPrivacy();

    fireEvent.click(screen.getByRole('button', { name: 'Привязать Google' }));

    const link = await screen.findByRole('link', { name: 'Продолжить с Google' });
    expect(apiMock).toHaveBeenCalledWith('/api/v1/me/auth/oauth-link/google', {
      method: 'POST',
      body: {},
    });
    expect(link).toHaveAttribute('href', '/api/v1/auth/oauth/google/link/start?token=safe-token');
  });

  it('marks an OAuth provider already linked to this profile', () => {
    authState.user.auth_providers = ['google', 'telegram'];
    authState.config.oauth_providers = ['google'];
    renderPrivacy();

    const googleRow = screen.getByText('Google').closest('.list-row');
    expect(googleRow).not.toBeNull();
    expect(within(googleRow as HTMLElement).getByText('Привязан')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Привязать Google' })).not.toBeInTheDocument();
  });

  it('offers VK ID linking when the backend exposes it', async () => {
    authState.user.auth_providers = ['telegram'];
    authState.config.oauth_providers = ['google', 'yandex', 'vk'];
    apiMock.mockResolvedValue({
      oauth_url: '/api/v1/auth/oauth/vk/link/start?token=safe-token',
      expires_in_seconds: 600,
    });
    renderPrivacy();

    fireEvent.click(screen.getByRole('button', { name: 'Привязать VK ID' }));

    const link = await screen.findByRole('link', { name: 'Продолжить с VK ID' });
    expect(apiMock).toHaveBeenCalledWith('/api/v1/me/auth/oauth-link/vk', {
      method: 'POST',
      body: {},
    });
    expect(link).toHaveAttribute('href', '/api/v1/auth/oauth/vk/link/start?token=safe-token');
  });
});
