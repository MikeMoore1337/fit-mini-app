import { useState } from 'react';
import { useAuth } from './AuthProvider';
import { Card, ErrorState, LoadingState } from '../shared/ui/common';
import { EmailAuthPanel } from '../features/auth/EmailAuthPanel';
import { OAuthButtons } from '../features/auth/OAuthButtons';
import { AppThemeToggle } from '../shared/ui/AppThemeToggle';

export function telegramMiniAppUrl(username: string): string {
  const normalized = username.trim().replace(/^@/, '');
  return `https://t.me/${encodeURIComponent(normalized)}?startapp`;
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, config, loading, error, devLogin, telegramLogin } = useAuth();
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const oauthProviders = config?.oauth_providers ?? [];
  const hasBrowserAuth = Boolean(config?.enable_email_auth || oauthProviders.length);
  const telegramAppUrl = config?.telegram_bot_username
    ? telegramMiniAppUrl(config.telegram_bot_username)
    : null;

  if (loading)
    return (
      <main className="container">
        <LoadingState label="Проверяем авторизацию…" />
      </main>
    );
  if (user) return <>{children}</>;

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setLocalError(null);
    try {
      await action();
    } catch (reason) {
      setLocalError(reason instanceof Error ? reason.message : 'Не удалось войти');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="container">
      <Card
        className="auth-panel"
        title="Вход в Your Fitness Coach"
        description={
          hasBrowserAuth
            ? 'Выберите доступный безопасный способ входа.'
            : 'Откройте приложение внутри Telegram для безопасной авторизации.'
        }
      >
        <div className="stack top-gap">
          <div className="auth-theme-row">
            <AppThemeToggle />
          </div>
          {(localError || error) && <ErrorState message={localError || error || ''} />}
          {window.Telegram?.WebApp?.initData && (
            <button disabled={busy} onClick={() => void run(() => telegramLogin())}>
              Войти через Telegram
            </button>
          )}
          {!window.Telegram?.WebApp?.initData && (
            <div className="auth-notice" role="status">
              <span>
                {hasBrowserAuth
                  ? 'Telegram Mini App не обнаружен. Выберите способ входа ниже.'
                  : 'Вход через браузер пока недоступен. Сейчас приложение можно открыть через Telegram.'}
              </span>
              {!hasBrowserAuth && telegramAppUrl && (
                <a className="button-link" href={telegramAppUrl} target="_blank" rel="noreferrer">
                  Открыть в Telegram
                </a>
              )}
            </div>
          )}
          {config?.enable_web_auth && <OAuthButtons providers={oauthProviders} />}
          {config?.enable_email_auth && <EmailAuthPanel />}
          {config?.enable_dev_auth && (
            <div className="stack">
              <p className="muted">Локальный режим разработки</p>
              <div className="auth-presets">
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      devLogin({
                        telegram_user_id: 2001,
                        username: 'demo_client',
                        full_name: 'Демо клиент',
                        is_coach: false,
                        is_admin: false,
                      }),
                    )
                  }
                >
                  Клиент
                </button>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      devLogin({
                        telegram_user_id: 1001,
                        username: 'demo_coach',
                        full_name: 'Демо тренер',
                        is_coach: true,
                        is_admin: false,
                      }),
                    )
                  }
                >
                  Тренер
                </button>
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      devLogin({
                        telegram_user_id: 1001,
                        username: 'demo_admin',
                        full_name: 'Демо админ',
                        is_coach: true,
                        is_admin: true,
                      }),
                    )
                  }
                >
                  Админ
                </button>
              </div>
            </div>
          )}
        </div>
      </Card>
    </main>
  );
}
