import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AuthGate } from '../../../src/app/AuthGate';

vi.mock('../../../src/app/AuthProvider', () => ({
  useAuth: () => ({
    user: null,
    config: {
      app_env: 'prod',
      enable_dev_auth: false,
      enable_web_auth: true,
      enable_email_auth: false,
      telegram_bot_username: 'fitness_bot',
      oauth_providers: ['telegram'],
    },
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
  it('показывает OAuth, но не показывает email-регистрацию при выключенном флаге', () => {
    render(<AuthGate>Приложение</AuthGate>);

    expect(screen.getByText('OAUTH:telegram')).toBeInTheDocument();
    expect(screen.queryByText('EMAIL_AUTH_PANEL')).not.toBeInTheDocument();
  });
});
