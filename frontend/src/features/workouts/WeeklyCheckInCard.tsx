import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type {
  WeeklyCheckInCurrent,
  WeeklyCheckInHistory,
  WeeklyCheckInSubmit,
} from '../../shared/api/types';
import { Badge, Card, ErrorState, LoadingState } from '../../shared/ui/common';
import { useFeedback } from '../../shared/ui/FeedbackProvider';

const scoreOptions = [1, 2, 3, 4, 5] as const;

function formatPeriod(start: string, end: string): string {
  const format = (value: string) =>
    new Date(`${value}T12:00:00`).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
    });
  return `${format(start)} — ${format(end)}`;
}

function optionalScore(value: string): number | null {
  return value ? Number(value) : null;
}

export function WeeklyCheckInCard() {
  const queryClient = useQueryClient();
  const { toast, confirm } = useFeedback();
  const [trainingLoad, setTrainingLoad] = useState('');
  const [recovery, setRecovery] = useState('');
  const [hunger, setHunger] = useState('');
  const [adherenceDifficulty, setAdherenceDifficulty] = useState('');
  const [note, setNote] = useState('');
  const current = useQuery({
    queryKey: ['weekly-check-ins', 'current'],
    queryFn: () => api<WeeklyCheckInCurrent>('/api/v1/check-ins/weekly/current'),
  });
  const history = useQuery({
    queryKey: ['weekly-check-ins', 'history'],
    queryFn: () => api<WeeklyCheckInHistory>('/api/v1/check-ins/weekly?limit=4&offset=0'),
  });
  const mutation = useMutation({
    mutationFn: (payload: WeeklyCheckInSubmit) =>
      api('/api/v1/check-ins/weekly', { method: 'POST', body: payload }),
    onSuccess: async (_result, payload) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['weekly-check-ins'] }),
        queryClient.invalidateQueries({ queryKey: ['notifications'] }),
      ]);
      toast(
        payload.status === 'skipped'
          ? 'Итоги недели отмечены как пропущенные'
          : 'Итоги недели сохранены',
      );
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  if (current.isLoading) return <LoadingState label="Собираем итоги недели…" />;
  if (current.error) {
    return (
      <ErrorState message={(current.error as Error).message} retry={() => void current.refetch()} />
    );
  }
  if (!current.data) return null;

  const { summary, existing } = current.data;
  const weightChange = summary.weight_trend?.change;
  return (
    <Card
      title="Еженедельные итоги"
      description={formatPeriod(current.data.week_start, current.data.week_end)}
    >
      <div className="metric-grid top-gap">
        <div className="metric">
          <span>Тренировки</span>
          <strong>
            {summary.training.completed_workouts} из {summary.training.planned_workouts}
          </strong>
        </div>
        <div className="metric">
          <span>Дней с питанием</span>
          <strong>{summary.nutrition.logged_days}</strong>
        </div>
        <div className="metric">
          <span>Новых рекордов</span>
          <strong>{summary.progression.new_personal_records}</strong>
        </div>
        <div className="metric">
          <span>Изменение веса</span>
          <strong>
            {weightChange == null
              ? 'Мало данных'
              : `${weightChange > 0 ? '+' : ''}${weightChange} кг`}
          </strong>
        </div>
      </div>

      {existing ? (
        <div className="list-row top-gap">
          <div>
            <strong>
              {existing.status === 'skipped' ? 'Неделя пропущена' : 'Итоги сохранены'}
            </strong>
            <p className="muted">{existing.note || 'Самооценки и заметка не обязательны.'}</p>
          </div>
          <Badge>{existing.status === 'skipped' ? 'Пропущено' : 'Готово'}</Badge>
        </div>
      ) : (
        <form
          className="stack top-gap"
          onSubmit={(event) => {
            event.preventDefault();
            mutation.mutate({
              status: 'completed',
              training_load: optionalScore(trainingLoad),
              recovery: optionalScore(recovery),
              hunger: optionalScore(hunger),
              adherence_difficulty: optionalScore(adherenceDifficulty),
              note: note.trim() || null,
            });
          }}
        >
          <p className="muted">
            Оценки необязательны. Шкала от 1 до 5 помогает сравнивать недели между собой.
          </p>
          <div className="form-grid">
            {[
              {
                label: 'Насколько тяжёлой была тренировочная неделя?',
                value: trainingLoad,
                setValue: setTrainingLoad,
                hint: '1 — легко, 5 — очень тяжело',
              },
              {
                label: 'Как вы восстановились?',
                value: recovery,
                setValue: setRecovery,
                hint: '1 — плохо, 5 — отлично',
              },
              {
                label: 'Насколько сильным был голод?',
                value: hunger,
                setValue: setHunger,
                hint: '1 — почти не беспокоил, 5 — очень сильный',
              },
              {
                label: 'Насколько сложно было соблюдать план?',
                value: adherenceDifficulty,
                setValue: setAdherenceDifficulty,
                hint: '1 — легко, 5 — очень сложно',
              },
            ].map((field) => (
              <label className="field" key={field.label}>
                <span>{field.label}</span>
                <select
                  value={field.value}
                  onChange={(event) => field.setValue(event.target.value)}
                >
                  <option value="">Не указывать</option>
                  {scoreOptions.map((score) => (
                    <option key={score} value={score}>
                      {score}
                    </option>
                  ))}
                </select>
                <small>{field.hint}</small>
              </label>
            ))}
          </div>
          <label className="field">
            <span>Заметка о неделе</span>
            <textarea
              value={note}
              maxLength={2000}
              rows={3}
              placeholder="Что помогало или мешало?"
              onChange={(event) => setNote(event.target.value)}
            />
          </label>
          <div className="button-row">
            <button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Сохраняем…' : 'Сохранить итоги'}
            </button>
            <button
              type="button"
              className="secondary"
              disabled={mutation.isPending}
              onClick={async () => {
                if (
                  await confirm({
                    title: 'Пропустить итоги этой недели?',
                    message: 'Это необязательно. Неделя останется в истории без самооценок.',
                    confirmText: 'Пропустить',
                  })
                ) {
                  mutation.mutate({ status: 'skipped' });
                }
              }}
            >
              Пропустить эту неделю
            </button>
          </div>
        </form>
      )}

      {history.data?.items.length ? (
        <details className="top-gap">
          <summary>Предыдущие недели</summary>
          <div className="list-grid top-gap">
            {history.data.items.map((item) => (
              <div className="list-row" key={item.id}>
                <div>
                  <strong>{formatPeriod(item.week_start, item.week_end)}</strong>
                  <p className="muted">
                    {item.summary.training.completed_workouts} из{' '}
                    {item.summary.training.planned_workouts} тренировок
                  </p>
                </div>
                <Badge>{item.status === 'skipped' ? 'Пропущено' : 'Готово'}</Badge>
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </Card>
  );
}
