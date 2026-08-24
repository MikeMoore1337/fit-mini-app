import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import LoginPage from '../../../../src/pages/auth/LoginPage';
import { NavigationProvider } from '../../../../src/shared/navigation/router';

const { authState } = vi.hoisted(() => ({
  authState: {
    user: null as { id: number } | null,
    config: {
      app_env: 'prod',
      enable_dev_auth: false,
      enable_web_auth: true,
      enable_email_auth: false,
      telegram_bot_username: 'fitness_bot',
      oauth_providers: ['telegram', 'google', 'yandex', 'vk'] as string[],
    },
    loading: false,
    error: null as string | null,
    devLogin: vi.fn(),
  },
}));

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => authState,
}));

function renderLogin() {
  return render(
    <NavigationProvider>
      <LoginPage />
    </NavigationProvider>,
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    authState.user = null;
    authState.loading = false;
    authState.error = null;
    authState.config.enable_web_auth = true;
    authState.config.enable_email_auth = false;
    authState.config.oauth_providers = ['telegram', 'google', 'yandex', 'vk'];
    window.history.replaceState(null, '', '/login?next=%2Fcoach');
  });

  afterEach(() => {
    cleanup();
    localStorage.clear();
  });

  it('shows the required configured providers and preserves safe next', () => {
    renderLogin();

    expect(screen.getByRole('heading', { name: /Вернитесь к своему плану/ })).toBeInTheDocument();
    expect(screen.getByText(/Аккаунты не объединяются автоматически/)).toBeInTheDocument();
    expect(document.querySelector('.auth-public-shell--design-v2-1')).toBeInTheDocument();
    for (const [name, provider] of [
      ['Войти через Telegram', 'telegram'],
      ['Продолжить с Google', 'google'],
      ['Войти с Яндекс ID', 'yandex'],
      ['Войти с VK ID', 'vk'],
    ]) {
      expect(screen.getByRole('link', { name })).toHaveAttribute(
        'href',
        `/api/v1/auth/oauth/${provider}/start?next=%2Fcoach`,
      );
    }
    expect(screen.queryByLabelText('Вход по email')).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /^Войти$/ })).not.toBeInTheDocument();
    expect(document.querySelector('.login-continuation-brand .yfc-lockup__mark')).toHaveAttribute(
      'src',
      '/assets/brand/yfc-mark-dark.svg',
    );
    expect(document.querySelector('.public-shell__header .yfc-lockup__wordmark')).toHaveTextContent(
      'Your FitnessCoach',
    );
  });

  it('falls back to Telegram when browser providers are unavailable', () => {
    authState.config.enable_web_auth = false;
    authState.config.oauth_providers = [];
    renderLogin();

    expect(screen.getByText('Вход через браузер пока недоступен')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Открыть в Telegram' })).toHaveAttribute(
      'href',
      'https://t.me/fitness_bot?startapp',
    );
  });

  it('renders a controlled OAuth error without exposing unknown query data', () => {
    window.history.replaceState(
      null,
      '',
      '/login?next=https%3A%2F%2Fevil.example&auth_error=invalid_state&code=secret-code',
    );
    renderLogin();

    expect(screen.getByText('Ссылка входа устарела')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('secret-code');
    expect(screen.getByRole('link', { name: 'Продолжить с Google' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/google/start?next=%2Fapp',
    );
  });

  it('redirects an already authenticated account to the intended destination', async () => {
    authState.user = { id: 9 };
    renderLogin();

    await waitFor(() => expect(window.location.pathname).toBe('/coach'));
  });

  it('explains clean onboarding and provides an explicit return to the demo scenario', () => {
    window.history.replaceState(null, '', '/login?next=%2Fapp&from=demo&scenario=trainer');
    renderLogin();

    expect(screen.getByText('После демо — чистый профиль')).toBeVisible();
    expect(screen.getByText(/Изменения не переносятся/)).toBeVisible();
    expect(screen.getByRole('link', { name: 'Вернуться в демо' })).toHaveAttribute(
      'href',
      '/demo?scenario=trainer',
    );
  });
});
