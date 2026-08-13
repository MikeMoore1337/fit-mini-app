import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { TelegramLinkPrompt } from '../../../../src/features/account/TelegramLinkPrompt';

const { apiMock, authState, toastMock } = vi.hoisted(() => ({
  apiMock: vi.fn(),
  authState: {
    user: { id: 77, telegram_user_id: null as number | null },
    config: { telegram_bot_username: 'your_fitness_coach_bot' },
  },
  toastMock: vi.fn(),
}));

vi.mock('../../../../src/shared/api/client', () => ({ api: apiMock }));
vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => authState,
}));
vi.mock('../../../../src/shared/ui/FeedbackProvider', () => ({
  useFeedback: () => ({ toast: toastMock }),
}));

function renderPrompt() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <TelegramLinkPrompt />
    </QueryClientProvider>,
  );
}

describe('TelegramLinkPrompt', () => {
  beforeEach(() => {
    localStorage.clear();
    authState.user.id = 77;
    authState.user.telegram_user_id = null;
    authState.config.telegram_bot_username = 'your_fitness_coach_bot';
    apiMock.mockReset();
    toastMock.mockReset();
  });

  afterEach(cleanup);

  it('explains optional Telegram linking and creates a short-lived bot link', async () => {
    apiMock.mockResolvedValue({
      telegram_url: 'https://t.me/your_fitness_coach_bot?start=link_safe-token',
      expires_in_seconds: 600,
    });
    renderPrompt();

    expect(screen.getByText('Подключите Telegram по желанию')).toBeInTheDocument();
    expect(screen.getByText(/Telegram не обязателен/)).toBeInTheDocument();
    expect(screen.getByText(/@your_fitness_coach_bot/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Подключить Telegram' }));

    const link = await screen.findByRole('link', { name: 'Открыть @your_fitness_coach_bot' });
    expect(apiMock).toHaveBeenCalledWith('/api/v1/me/auth/telegram-link', {
      method: 'POST',
      body: {},
    });
    expect(link).toHaveAttribute(
      'href',
      'https://t.me/your_fitness_coach_bot?start=link_safe-token',
    );
  });

  it('stays hidden for the current user after choosing not now', () => {
    renderPrompt();

    fireEvent.click(screen.getByRole('button', { name: 'Не сейчас' }));

    expect(screen.queryByText('Подключите Telegram по желанию')).not.toBeInTheDocument();
    expect(localStorage.getItem('fit_telegram_link_prompt_dismissed_77')).toBe('true');
  });

  it('does not appear when Telegram is already linked or the bot is unavailable', () => {
    authState.user.telegram_user_id = 12345;
    renderPrompt();
    expect(screen.queryByText('Подключите Telegram по желанию')).not.toBeInTheDocument();

    cleanup();
    authState.user.telegram_user_id = null;
    authState.config.telegram_bot_username = '';
    renderPrompt();
    expect(screen.queryByText('Подключите Telegram по желанию')).not.toBeInTheDocument();
  });
});
