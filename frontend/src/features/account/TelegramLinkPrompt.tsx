import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { TelegramLinkCreate } from '../../shared/api/types';
import { Card } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

function dismissalKey(userId: number): string {
  return `fit_telegram_link_prompt_dismissed_${userId}`;
}

export function TelegramLinkPrompt() {
  const { user, config } = useAuth();
  const { toast } = useFeedback();
  const [dismissed, setDismissed] = useState(() =>
    user ? localStorage.getItem(dismissalKey(user.id)) === 'true' : false,
  );
  const linkMutation = useMutation({
    mutationFn: () =>
      api<TelegramLinkCreate>('/api/v1/me/auth/telegram-link', {
        method: 'POST',
        body: {},
      }),
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  if (!user || user.telegram_user_id || !config?.telegram_bot_username || dismissed) return null;

  const botUsername = config.telegram_bot_username.replace(/^@/, '');

  return (
    <Card
      className="telegram-link-prompt"
      title="Подключите Telegram по желанию"
      description="Telegram не обязателен для тренировок в браузере. Подключите его, чтобы открывать тот же аккаунт в Mini App, получать уведомления и переходить к общению с тренером. Программы, тренировки и прогресс останутся общими."
    >
      <p className="muted top-gap">
        Мы создадим одноразовую ссылку на @{botUsername}. Откройте её под тем Telegram-аккаунтом,
        который хотите привязать.
      </p>
      <div className="toolbar wrap top-gap telegram-link-prompt__actions">
        {linkMutation.data ? (
          <a
            className="button-link"
            href={linkMutation.data.telegram_url}
            target="_blank"
            rel="noreferrer"
          >
            Открыть @{botUsername}
          </a>
        ) : (
          <button
            type="button"
            disabled={linkMutation.isPending}
            onClick={() => linkMutation.mutate()}
          >
            {linkMutation.isPending ? 'Создаём ссылку…' : 'Подключить Telegram'}
          </button>
        )}
        <button
          type="button"
          className="secondary"
          onClick={() => {
            localStorage.setItem(dismissalKey(user.id), 'true');
            setDismissed(true);
          }}
        >
          Не сейчас
        </button>
      </div>
    </Card>
  );
}
