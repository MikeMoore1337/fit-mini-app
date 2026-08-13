import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthGate, telegramMiniAppUrl } from '../../../src/app/AuthGate';

const { authConfig } = vi.hoisted(() => ({
  authConfig: {
    app_env: 'prod',
    enable_dev_auth: false,
    enable_web_auth: true,
    enable_email_auth: false,
    telegram_bot_username: 'fitness_bot',
    oauth_providers: ['telegram'],
  },
}));

vi.mock('../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: null,
    config: authConfig,
    loading: false,
    error: null,
    devLogin: vi.fn(),
    telegramLogin: vi.fn(),
  }),
}));

vi.mock('../../../src/features/auth/EmailAuthPanel', () => ({
  EmailAuthPanel: () => <div>EMAIL_AUTH_PANEL</div>,
}));

vi.mock('../../../src/features/auth/OAuthButtons', () => ({
  OAuthButtons: ({ providers }: { providers: string[] }) => <div>OAUTH:{providers.join(',')}</div>,
}));

describe('AuthGate', () => {
  beforeEach(() => {
    authConfig.enable_web_auth = true;
    authConfig.oauth_providers = ['telegram'];
  });

  it('показывает OAuth, но не показывает email-регистрацию при выключенном флаге', () => {
    render(<AuthGate>Приложение</AuthGate>);

    expect(screen.getByText('OAUTH:telegram')).toBeInTheDocument();
    expect(
      screen.getByText(/вход через Telegram откроет защищённую страницу/i),
    ).toBeInTheDocument();
    expect(screen.queryByText('EMAIL_AUTH_PANEL')).not.toBeInTheDocument();
  });

  it('offers a direct Telegram button when browser login is disabled', () => {
    authConfig.enable_web_auth = false;
    authConfig.oauth_providers = [];

    render(<AuthGate>Приложение</AuthGate>);

    expect(screen.getByText(/вход через браузер пока недоступен/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Открыть в Telegram' })).toHaveAttribute(
      'href',
      'https://t.me/fitness_bot?startapp',
    );
  });

  it('normalizes Telegram usernames for Mini App links', () => {
    expect(telegramMiniAppUrl('@fitness_bot')).toBe('https://t.me/fitness_bot?startapp');
  });
});
