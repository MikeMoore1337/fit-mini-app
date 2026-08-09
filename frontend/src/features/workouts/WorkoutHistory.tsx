import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type {
  WorkoutHistoryItem,
  WorkoutHistorySummary,
  WorkoutScheduleItem,
} from '../../shared/api/types';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

const HISTORY_PAGE_SIZE = 10;
const statusLabels: Record<string, string> = {
  planned: 'Запланирована',
  in_progress: 'В процессе',
  completed: 'Завершена',
  skipped: 'Пропущена',
};

export function WorkoutHistory() {
  const queryClient = useQueryClient();
  const { confirm, toast } = useFeedback();
  const week = useQuery({
    queryKey: ['workout', 'week'],
    queryFn: () => api<WorkoutScheduleItem[]>('/api/v1/workouts/week'),
  });
  const history = useInfiniteQuery({
    queryKey: ['workout', 'history'],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api<WorkoutHistoryItem[]>(
        `/api/v1/workouts/history?offset=${pageParam}&limit=${HISTORY_PAGE_SIZE}`,
      ),
    getNextPageParam: (lastPage, pages) =>
      lastPage.length === HISTORY_PAGE_SIZE ? pages.flat().length : undefined,
  });
  const summary = useQuery({
    queryKey: ['workout', 'history', 'summary'],
    queryFn: () => api<WorkoutHistorySummary>('/api/v1/workouts/history/summary'),
  });
  const rows = history.data?.pages.flat() ?? [];
  const clearHistory = useMutation({
    mutationFn: () => api('/api/v1/workouts/history', { method: 'DELETE' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workout'] });
      toast('История тренировок очищена');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  return (
    <div className="stack">
      <Card title="Неделя">
        {week.isLoading ? (
          <LoadingState />
        ) : week.error ? (
          <ErrorState message={(week.error as Error).message} />
        ) : !week.data?.length ? (
          <EmptyState title="На этой неделе нет тренировок" />
        ) : (
          <div className="list-grid top-gap">
            {week.data.map((item) => (
              <article className="list-row" key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <p className="muted">{item.scheduled_date}</p>
                </div>
                <Badge>{statusLabels[item.status] ?? item.status}</Badge>
              </article>
            ))}
          </div>
        )}
      </Card>
      <Card
        title="История"
        actions={
          rows.length ? (
            <button
              className="btn-danger"
              disabled={clearHistory.isPending}
              onClick={async () => {
                if (
                  await confirm({
                    title: 'Очистить историю?',
                    message: 'Завершённые тренировки и их подходы будут удалены безвозвратно.',
                    confirmText: 'Очистить',
                  })
                )
                  clearHistory.mutate();
              }}
            >
              Очистить
            </button>
          ) : undefined
        }
      >
        {history.isLoading || summary.isLoading ? (
          <LoadingState />
        ) : history.error || summary.error ? (
          <ErrorState message={((history.error || summary.error) as Error).message} />
        ) : !rows.length ? (
          <EmptyState title="История пока пуста" />
        ) : (
          <>
            <div className="metric-grid top-gap">
              <div className="metric">
                <span>Тренировок</span>
                <strong>{summary.data?.workouts_completed ?? 0}</strong>
              </div>
              <div className="metric">
                <span>Подходов</span>
                <strong>{summary.data?.completed_sets ?? 0}</strong>
              </div>
              <div className="metric">
                <span>Объём</span>
                <strong>{Math.round(summary.data?.volume_kg ?? 0)} кг</strong>
              </div>
            </div>
            <div className="list-grid top-gap">
              {rows.map((item) => (
                <article className="list-row" key={item.id}>
                  <div>
                    <strong>{item.title}</strong>
                    <p className="muted">
                      {item.scheduled_date} · {item.completed_sets} подходов
                    </p>
                  </div>
                  <strong>{item.volume_kg} кг</strong>
                </article>
              ))}
            </div>
            {history.hasNextPage && (
              <button
                className="secondary top-gap"
                disabled={history.isFetchingNextPage}
                onClick={() => void history.fetchNextPage()}
              >
                {history.isFetchingNextPage ? 'Загружаем…' : 'Показать ещё'}
              </button>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
