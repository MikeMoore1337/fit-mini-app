import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { WorkoutHistoryItem, WorkoutScheduleItem } from '../../shared/api/types';
import { Badge, Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

const HISTORY_PAGE_SIZE = 10;

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
  const rows = history.data?.pages.flat() ?? [];
  const clearHistory = useMutation({
    mutationFn: () => api('/api/v1/workouts/history', { method: 'DELETE' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['workout', 'history'] });
      toast('История тренировок очищена');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const stats = rows.reduce(
    (result, item) => ({
      workouts: result.workouts + 1,
      sets: result.sets + item.completed_sets,
      volume: result.volume + item.volume_kg,
    }),
    { workouts: 0, sets: 0, volume: 0 },
  );
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
                <Badge>{item.status}</Badge>
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
        {history.isLoading ? (
          <LoadingState />
        ) : history.error ? (
          <ErrorState message={(history.error as Error).message} />
        ) : !rows.length ? (
          <EmptyState title="История пока пуста" />
        ) : (
          <>
            <div className="metric-grid top-gap">
              <div className="metric">
                <span>Тренировок</span>
                <strong>{stats.workouts}</strong>
              </div>
              <div className="metric">
                <span>Подходов</span>
                <strong>{stats.sets}</strong>
              </div>
              <div className="metric">
                <span>Объём</span>
                <strong>{Math.round(stats.volume)} кг</strong>
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
