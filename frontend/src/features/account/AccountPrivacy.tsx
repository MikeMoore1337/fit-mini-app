import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import { Card } from '../../shared/ui/common';
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
  const { logout } = useAuth();
  const { toast, confirm } = useFeedback();
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
  );
}
