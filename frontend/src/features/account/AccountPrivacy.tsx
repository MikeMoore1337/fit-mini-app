import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { TelegramLinkCreate } from '../../shared/api/types';
import { Badge, Card } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

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

export function AccountPrivacy() {
  const { user, logout } = useAuth();
  const { toast, confirm } = useFeedback();
  const telegramLinkMutation = useMutation({
    mutationFn: () =>
      api<TelegramLinkCreate>('/api/v1/me/auth/telegram-link', {
        method: 'POST',
        body: {},
      }),
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const exportMutation = useMutation({
    mutationFn: () => api<unknown>('/api/v1/me/export'),
    onSuccess: (payload) => {
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
      toast('Аккаунт удалён');
      await logout();
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  return (
    <>
      <Card
        title="Способы входа"
        description="Привяжите Telegram, чтобы видеть одни и те же данные в браузере и боте."
      >
        <div className="list-row top-gap">
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
        </div>
        {!user?.telegram_user_id && (
          <p className="muted top-gap">
            Если Telegram уже принадлежит другому аккаунту, автоматическое объединение будет
            заблокировано.
          </p>
        )}
      </Card>

      <Card title="Данные и аккаунт" description="Скачайте копию данных или удалите аккаунт.">
        <div className="toolbar wrap top-gap">
          <button
            type="button"
            className="secondary"
            disabled={exportMutation.isPending}
            onClick={() => exportMutation.mutate()}
          >
            {exportMutation.isPending ? 'Готовим архив…' : 'Скачать мои данные'}
          </button>
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
              )
                deleteMutation.mutate();
            }}
          >
            {deleteMutation.isPending ? 'Удаляем…' : 'Удалить аккаунт'}
          </button>
        </div>
      </Card>
    </>
  );
}
