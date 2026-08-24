import { useMutation } from '@tanstack/react-query';
import { productEventSurface, trackProductEvent } from '../../shared/analytics/productEvents';
import { useAuth } from '../../app/AuthProvider';
import { api, ApiError } from '../../shared/api/client';
import type { OAuthLinkCreate, TelegramLinkCreate } from '../../shared/api/types';
import { Badge, Card, DisclosureIcon } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

const PROVIDER_LABELS: Record<string, string> = {
  google: 'Google',
  yandex: 'Яндекс',
  vk: 'VK ID',
  apple: 'Apple',
};

function downloadJson(payload: unknown): void {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: 'application/json;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `fitmini-account-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function linkingErrorMessage(reason: unknown): string {
  if (reason instanceof ApiError && reason.status === 409) {
    return 'Этот способ уже связан с аккаунтом. Автоматическое объединение недоступно.';
  }
  return 'Не удалось подготовить привязку. Проверьте соединение и попробуйте снова.';
}

export function AccountPrivacy() {
  const { user, config, logout } = useAuth();
  const { toast, confirm } = useFeedback();
  const telegramLinkMutation = useMutation({
    mutationFn: () =>
      api<TelegramLinkCreate>('/api/v1/me/auth/telegram-link', {
        method: 'POST',
        body: {},
      }),
    onError: () => toast('Не удалось подготовить привязку Telegram', 'error'),
  });
  const oauthLinkMutation = useMutation({
    mutationFn: async (provider: string) => ({
      provider,
      link: await api<OAuthLinkCreate>(`/api/v1/me/auth/oauth-link/${provider}`, {
        method: 'POST',
        body: {},
      }),
    }),
    onError: (_reason, provider) =>
      toast(`Не удалось подготовить привязку ${PROVIDER_LABELS[provider] ?? provider}`, 'error'),
  });
  const availableOAuthProviders = (config?.oauth_providers ?? []).filter(
    (provider) => provider in PROVIDER_LABELS,
  );
  const linkedProviders = new Set(user?.auth_providers ?? []);
  const exportMutation = useMutation({
    mutationFn: () => api<unknown>('/api/v1/me/export'),
    onSuccess: (payload) => {
      trackProductEvent({ name: 'data_export_requested', surface: productEventSurface() });
      downloadJson(payload);
      toast('Архив данных скачан');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const deleteMutation = useMutation({
    mutationFn: () =>
      api<void>('/api/v1/me/account', {
        method: 'DELETE',
        body: { confirmation: 'DELETE' },
      }),
    onSuccess: async () => {
      trackProductEvent({ name: 'account_delete_completed', surface: productEventSurface() });
      toast('Аккаунт удалён');
      await logout();
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  return (
    <>
      <details className="card profile-disclosure">
        <summary>
          <span>
            <strong>Способы входа</strong>
            <small>
              Привяжите дополнительные способы входа, чтобы открывать один профиль в браузере и
              Telegram.
            </small>
          </span>
          <DisclosureIcon />
        </summary>
        <div className="profile-disclosure__body">
          <div className="list-row auth-method-row" aria-busy={telegramLinkMutation.isPending}>
            <div className="list-row__main">
              <strong>Telegram</strong>
              <span className="muted">
                {user?.telegram_user_id
                  ? 'Подключён к текущему аккаунту.'
                  : 'Привязка выполняется одноразовой ссылкой и действует 10 минут.'}
              </span>
            </div>
            <div className="list-row__actions">
              {user?.telegram_user_id ? (
                <Badge>Привязан</Badge>
              ) : telegramLinkMutation.data ? (
                <a
                  className="button-link"
                  href={telegramLinkMutation.data.telegram_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Открыть Telegram
                </a>
              ) : (
                <button
                  type="button"
                  className="secondary"
                  disabled={telegramLinkMutation.isPending}
                  onClick={() => telegramLinkMutation.mutate()}
                >
                  {telegramLinkMutation.isPending ? 'Создаём ссылку…' : 'Привязать Telegram'}
                </button>
              )}
            </div>
            {telegramLinkMutation.isError && (
              <p className="auth-method-row__feedback" role="alert">
                {linkingErrorMessage(telegramLinkMutation.error)}
              </p>
            )}
            {telegramLinkMutation.data && (
              <p className="auth-method-row__feedback" role="status">
                Ссылка готова и действует 10 минут.
              </p>
            )}
          </div>
          {!user?.telegram_user_id && (
            <p className="muted">
              Если Telegram уже принадлежит другому аккаунту, автоматическое объединение будет
              заблокировано.
            </p>
          )}
          {availableOAuthProviders.map((provider) => {
            const label = PROVIDER_LABELS[provider];
            const pending = oauthLinkMutation.isPending && oauthLinkMutation.variables === provider;
            const createdLink =
              oauthLinkMutation.data?.provider === provider ? oauthLinkMutation.data.link : null;
            const providerError =
              oauthLinkMutation.isError && oauthLinkMutation.variables === provider
                ? oauthLinkMutation.error
                : null;
            return (
              <div className="list-row auth-method-row" key={provider} aria-busy={pending}>
                <div className="list-row__main">
                  <strong>{label}</strong>
                  <span className="muted">
                    {linkedProviders.has(provider)
                      ? 'Подключён к текущему аккаунту.'
                      : 'После подтверждения можно будет входить этим способом в тот же профиль.'}
                  </span>
                </div>
                <div className="list-row__actions">
                  {linkedProviders.has(provider) ? (
                    <Badge>Привязан</Badge>
                  ) : createdLink ? (
                    <a className="button-link" href={createdLink.oauth_url}>
                      Продолжить с {label}
                    </a>
                  ) : (
                    <button
                      type="button"
                      className="secondary"
                      disabled={oauthLinkMutation.isPending}
                      onClick={() => oauthLinkMutation.mutate(provider)}
                    >
                      {pending ? 'Готовим переход…' : `Привязать ${label}`}
                    </button>
                  )}
                </div>
                {providerError && (
                  <p className="auth-method-row__feedback" role="alert">
                    {linkingErrorMessage(providerError)}
                  </p>
                )}
                {createdLink && (
                  <p className="auth-method-row__feedback" role="status">
                    Ссылка готова. Завершите привязку у провайдера.
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </details>

      <Card
        title="Копия данных"
        description="Скачайте данные аккаунта перед удалением или для личного архива."
      >
        <div className="profile-data-export top-gap">
          <p className="muted">Архив формируется в JSON и сохраняется только на ваше устройство.</p>
          <button
            type="button"
            className="secondary"
            disabled={exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
          >
            {exportMutation.isPending ? 'Готовим архив…' : 'Скачать мои данные'}
          </button>
        </div>
      </Card>

      <section className="profile-danger-zone" aria-labelledby="profile-danger-title">
        <div>
          <span className="eyebrow">Опасное действие</span>
          <h3 id="profile-danger-title">Удаление аккаунта</h3>
          <p>
            Профиль, замеры, программы и история тренировок будут удалены без возможности
            восстановления.
          </p>
        </div>
        <div className="profile-danger-zone__action">
          <button
            type="button"
            className="btn-danger"
            disabled={deleteMutation.isPending}
            onClick={async () => {
              if (
                await confirm({
                  title: 'Удалить аккаунт?',
                  message:
                    'Профиль, замеры, программы и история тренировок будут удалены безвозвратно. Перед удалением можно скачать копию данных.',
                  confirmText: 'Удалить навсегда',
                })
              ) {
                trackProductEvent({
                  name: 'account_delete_started',
                  surface: productEventSurface(),
                });
                deleteMutation.mutate();
              }
            }}
          >
            {deleteMutation.isPending ? 'Удаляем…' : 'Удалить аккаунт'}
          </button>
        </div>
      </section>
    </>
  );
}
