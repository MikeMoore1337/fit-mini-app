import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../../app/AuthProvider';
import { EmailAuthPanel } from '../../features/auth/EmailAuthPanel';
import { configuredOAuthProviders, OAuthButtons } from '../../features/auth/OAuthButtons';
import { safeAuthNextPath } from '../../shared/auth/redirects';
import { AppLink, useNavigation } from '../../shared/navigation/router';
import { ErrorState, LoadingState } from '../../shared/ui/common';
import { BrandLockup } from '../../shared/ui/BrandLogo';
import { PublicShell } from '../../shared/ui/PublicShell';
import { telegramMiniAppUrl } from '../../app/AuthGate';
import './auth.css';

const AUTH_ERROR_MESSAGES: Record<string, { title: string; message: string }> = {
  unavailable: {
    title: 'Способ входа временно недоступен',
    message: 'Выберите другой способ или повторите попытку позже.',
  },
  denied: {
    title: 'Вход отменён',
    message: 'Разрешение не было выдано. Можно выбрать этот способ ещё раз или попробовать другой.',
  },
  invalid_state: {
    title: 'Ссылка входа устарела',
    message: 'Начните вход заново — прежняя защищённая сессия больше недействительна.',
  },
  blocked: {
    title: 'Доступ к аккаунту ограничен',
    message: 'Войти сейчас нельзя. Если это неожиданно, обратитесь в поддержку.',
  },
  conflict: {
    title: 'Этот способ уже связан с другим аккаунтом',
    message:
      'Мы не объединяем аккаунты автоматически. Войдите другим способом или обратитесь в поддержку.',
  },
  provider_failure: {
    title: 'Не удалось завершить вход',
    message:
      'Сервис авторизации не ответил корректно. Повторите попытку или выберите другой способ.',
  },
};

function AuthErrorNotice({ code }: { code: string | null }) {
  const error = code ? AUTH_ERROR_MESSAGES[code] : null;
  if (!error) return null;
  return (
    <div className="login-alert" role="alert">
      <strong>{error.title}</strong>
      <span>{error.message}</span>
    </div>
  );
}

function DevLoginControls({ nextPath }: { nextPath: string }) {
  const { devLogin } = useAuth();
  const { navigate } = useNavigation();
  const [busyRole, setBusyRole] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const roles = [
    {
      label: 'Клиент',
      telegram_user_id: 2001,
      username: 'demo_client',
      is_coach: false,
      is_admin: false,
    },
    {
      label: 'Тренер',
      telegram_user_id: 1001,
      username: 'demo_coach',
      is_coach: true,
      is_admin: false,
    },
    {
      label: 'Админ',
      telegram_user_id: 1001,
      username: 'demo_admin',
      is_coach: true,
      is_admin: true,
    },
  ];

  return (
    <section className="login-dev" aria-label="Локальный режим разработки">
      <p>Локальный режим разработки</p>
      {error && <ErrorState message={error} />}
      <div className="auth-presets">
        {roles.map(({ label, ...input }) => (
          <button
            key={label}
            type="button"
            className="secondary"
            disabled={busyRole !== null}
            onClick={() => {
              setBusyRole(label);
              setError(null);
              void devLogin({ ...input, full_name: `Демо ${label.toLowerCase()}` })
                .then(() => navigate(nextPath, true))
                .catch((reason: unknown) =>
                  setError(reason instanceof Error ? reason.message : 'Не удалось войти'),
                )
                .finally(() => setBusyRole(null));
            }}
          >
            {busyRole === label ? 'Входим…' : label}
          </button>
        ))}
      </div>
    </section>
  );
}

export default function LoginPage() {
  const { user, config, loading, error } = useAuth();
  const { navigate } = useNavigation();
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const nextPath = safeAuthNextPath(params.get('next'));
  const authErrorCode = params.get('auth_error');
  const providers = configuredOAuthProviders(config?.enable_web_auth ? config.oauth_providers : []);
  const telegramAppUrl = config?.telegram_bot_username
    ? telegramMiniAppUrl(config.telegram_bot_username)
    : null;
  const designPilot49e =
    import.meta.env.DEV && document.documentElement.dataset.designPilot === '49e';

  useEffect(() => {
    if (!loading && user) navigate(nextPath, true);
  }, [loading, navigate, nextPath, user]);

  return (
    <PublicShell
      className="auth-public-shell auth-public-shell--design-v2"
      headerAction={
        designPilot49e ? (
          <a className="login-home-link" href="#login-content">
            Войти
          </a>
        ) : (
          <AppLink className="login-home-link" to="/">
            На главную
          </AppLink>
        )
      }
      skipTarget="login-content"
    >
      <main id="login-content" className="login-layout" tabIndex={-1}>
        <section className="login-intro" aria-labelledby="login-title">
          {designPilot49e ? (
            <>
              <BrandLockup className="login-pilot-brand" />
              <div className="login-pilot-continuation">
                <p className="login-kicker">Продолжение</p>
                <h1 id="login-title">
                  <span className="login-pilot-title--desktop">Вернитесь к своему плану.</span>
                  <span className="login-pilot-title--mobile">Войти и продолжить</span>
                </h1>
                <p className="login-pilot-copy--desktop">
                  Вход связывает browser и Telegram с одной учётной записью. Аккаунты не
                  объединяются автоматически.
                </p>
                <p className="login-pilot-copy--mobile">
                  После входа откроется раздел «Питание». Используйте уже связанный способ.
                </p>
              </div>
              <small className="login-pilot-surface-note">Web · защищённый переход</small>
            </>
          ) : (
            <>
              <p className="login-kicker">Безопасный доступ к вашему профилю</p>
              <h1 id="login-title">Продолжить в Your Fitness Coach</h1>
              <p>Тренировки, питание и измерения остаются в одном профиле.</p>
              <ul aria-label="Что останется доступно после входа">
                <li>Тренировки и программы</li>
                <li>Питание и измерения</li>
                <li>Один профиль в браузере и Telegram</li>
              </ul>
            </>
          )}
        </section>

        <section className="login-card" aria-label="Способы входа">
          {designPilot49e && (
            <div className="login-pilot-auth-heading">
              <p className="login-kicker">Вход</p>
              <h2>Выберите способ</h2>
              <p>После входа: Питание → Сегодня</p>
            </div>
          )}
          {loading || user ? (
            <LoadingState label={user ? 'Перенаправляем…' : 'Проверяем авторизацию…'} />
          ) : (
            <div className="login-card__content">
              <AuthErrorNotice code={authErrorCode} />
              {error && (
                <ErrorState message="Не удалось связаться с сервером. Проверьте интернет и повторите попытку." />
              )}
              {providers.length > 0 && <OAuthButtons providers={providers} nextPath={nextPath} />}
              {!providers.length && !config?.enable_email_auth && (
                <div className="login-unavailable" role="status">
                  <strong>Вход через браузер пока недоступен</strong>
                  <span>Откройте приложение в Telegram или повторите попытку позже.</span>
                </div>
              )}
              {!providers.includes('telegram') && telegramAppUrl && (
                <a
                  className="login-telegram-fallback"
                  href={telegramAppUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  Открыть в Telegram
                </a>
              )}
              {config?.enable_email_auth && <EmailAuthPanel nextPath={nextPath} />}
              {config?.enable_dev_auth && <DevLoginControls nextPath={nextPath} />}
              {(error || authErrorCode) && (
                <button
                  type="button"
                  className="login-retry"
                  onClick={() => window.location.reload()}
                >
                  Повторить
                </button>
              )}
            </div>
          )}
          <p className="login-privacy-note">
            {designPilot49e
              ? 'Valid TMA launch: browser providers не показываются.'
              : 'Провайдер подтверждает личность, а данные тренировок остаются в Your Fitness Coach.'}
          </p>
        </section>
      </main>
    </PublicShell>
  );
}
