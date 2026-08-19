import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type {
  EnergyCalibration,
  EnergyCalibrationHistory,
  NutritionTarget,
} from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { DisclosureIcon } from '../../shared/ui/common';

const statusLabels: Record<EnergyCalibration['status'], string> = {
  insufficient: 'Недостаточно данных',
  limited: 'Данные пока нестабильны',
  no_change: 'Изменение не требуется',
  pending: 'Ожидает решения',
  accepted: 'Принято',
  rejected: 'Отклонено',
  superseded: 'Устарело',
};

function formatPeriod(start: string, end: string): string {
  const formatter = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' });
  return `${formatter.format(new Date(`${start}T12:00:00`))} — ${formatter.format(
    new Date(`${end}T12:00:00`),
  )}`;
}

export function EnergyCalibrationCard({
  target,
  onAccepted,
}: {
  target: NutritionTarget;
  onAccepted?: () => void | Promise<void>;
}) {
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const [result, setResult] = useState<EnergyCalibration | null>(null);
  const history = useQuery({
    queryKey: ['energy-calibration-history'],
    queryFn: () => api<EnergyCalibrationHistory>('/api/v1/nutrition/energy-calibration/history'),
  });
  const preview = useMutation({
    mutationFn: () =>
      api<EnergyCalibration>('/api/v1/nutrition/energy-calibration/preview', {
        method: 'POST',
      }),
    onSuccess: async (response) => {
      setResult(response);
      await queryClient.invalidateQueries({ queryKey: ['energy-calibration-history'] });
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const decision = useMutation({
    mutationFn: ({ id, value }: { id: number; value: 'accept' | 'reject' }) =>
      api<EnergyCalibration>(`/api/v1/nutrition/energy-calibration/${id}/decision`, {
        method: 'POST',
        body: { decision: value },
      }),
    onSuccess: async (response) => {
      setResult(response);
      await queryClient.invalidateQueries({ queryKey: ['energy-calibration-history'] });
      if (response.status === 'accepted') {
        await onAccepted?.();
        toast('Новая калорийность подтверждена');
      } else {
        toast('Предложение отклонено');
      }
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  const active = result ?? history.data?.items.find((item) => item.status === 'pending') ?? null;
  const isBusy = preview.isPending || decision.isPending;

  return (
    <section className="stack energy-calibration" aria-labelledby="energy-calibration-heading">
      <div>
        <h3 id="energy-calibration-heading">Проверка калорийности по истории</h3>
        <p className="muted">
          Сопоставляет заполненный дневник и сглаженный тренд массы за 28 дней.
        </p>
      </div>
      <div className="stack energy-calibration__content">
        <p className="muted">
          Текущая цель: {target.calories} ккал. Оценка не использует смарт-часы и не меняет цель
          автоматически.
        </p>
        <button type="button" disabled={isBusy} onClick={() => preview.mutate()}>
          {preview.isPending ? 'Проверяем…' : 'Проверить по истории'}
        </button>

        {history.isError && (
          <p className="nutrition-warning" role="alert">
            Не удалось загрузить историю проверок. Новую проверку всё равно можно выполнить.
          </p>
        )}

        {active && (
          <section className="energy-calibration__result" aria-live="polite">
            <div className="nutrition-section-heading">
              <div>
                <strong>{statusLabels[active.status]}</strong>
                <p className="muted">{formatPeriod(active.period_start, active.period_end)}</p>
              </div>
            </div>

            {active.estimated_expenditure_kcal !== null &&
              active.estimated_expenditure_kcal !== undefined && (
                <div className="metric-grid nutrition-metrics">
                  <div className="metric">
                    <span>Оценка расхода</span>
                    <strong>{active.estimated_expenditure_kcal} ккал</strong>
                  </div>
                  <div className="metric">
                    <span>Осторожный диапазон</span>
                    <strong>
                      {active.estimate_low_kcal}–{active.estimate_high_kcal} ккал
                    </strong>
                  </div>
                </div>
              )}

            <ul className="energy-calibration__rationale">
              {active.rationale.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            {active.status === 'pending' && active.id && active.proposed_target_calories && (
              <div className="energy-calibration__proposal">
                <p>
                  Предлагаемая цель: <strong>{active.proposed_target_calories} ккал</strong> вместо{' '}
                  {active.current_target_calories} ккал.
                </p>
                <div className="toolbar wrap">
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => decision.mutate({ id: active.id!, value: 'accept' })}
                  >
                    {decision.isPending ? 'Сохраняем…' : 'Подтвердить новую цель'}
                  </button>
                  <button
                    type="button"
                    className="secondary"
                    disabled={isBusy}
                    onClick={() => decision.mutate({ id: active.id!, value: 'reject' })}
                  >
                    Оставить текущую
                  </button>
                </div>
              </div>
            )}
          </section>
        )}

        {history.data && history.data.items.length > 0 && (
          <details className="nutrition-details energy-calibration__history">
            <summary>
              <span>История проверок</span>
              <DisclosureIcon />
            </summary>
            <ul>
              {history.data.items.map((item) => (
                <li key={item.id}>
                  <span>{formatPeriod(item.period_start, item.period_end)}</span>
                  <strong>{statusLabels[item.status]}</strong>
                  {item.proposed_target_calories && (
                    <span>
                      {item.current_target_calories} → {item.proposed_target_calories} ккал
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </section>
  );
}
