import { useState } from 'react';
import { useAuth } from './AuthProvider';
import { Card, ErrorState, LoadingState } from '../shared/ui/common';
import { EmailAuthPanel } from '../features/auth/EmailAuthPanel';
import { OAuthButtons } from '../features/auth/OAuthButtons';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, config, loading, error, devLogin, telegramLogin } = useAuth();
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

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
          config?.enable_web_auth
            ? 'Войдите через Telegram или используйте аккаунт с подтверждённым email.'
            : 'Откройте приложение внутри Telegram для безопасной авторизации.'
        }
      >
        <div className="stack top-gap">
          {(localError || error) && <ErrorState message={localError || error || ''} />}
          {window.Telegram?.WebApp?.initData && (
            <button disabled={busy} onClick={() => void run(() => telegramLogin())}>
              Войти через Telegram
            </button>
          )}
          {!window.Telegram?.WebApp?.initData && (
            <p className="auth-notice">
              {config?.enable_web_auth
                ? 'Telegram Mini App не обнаружен. Доступен вход через браузер.'
                : 'Telegram Mini App не обнаружен. Откройте приложение кнопкой внутри бота.'}
            </p>
          )}
          {config?.enable_web_auth && <OAuthButtons providers={config.oauth_providers ?? []} />}
          {config?.enable_web_auth && <EmailAuthPanel />}
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
