import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { BodyMeasurement, BodyMeasurementSave } from '../../shared/api/types';
import { LIVE_DATA_REFETCH_INTERVAL_MS } from '../../shared/sync';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';

export function Diary({
  clientId,
  onSaved,
}: {
  clientId?: number;
  onSaved?: () => void | Promise<void>;
}) {
  const queryClient = useQueryClient();
  const { toast, confirm } = useFeedback();
  const [form, setForm] = useState<BodyMeasurementSave>({
    measured_on: new Date().toISOString().slice(0, 10),
  });
  const base = clientId
    ? `/api/v1/coach/clients/${clientId}/measurements`
    : '/api/v1/workouts/diary';
  const rows = useQuery({
    queryKey: ['measurements', clientId || 'me'],
    queryFn: () => api<BodyMeasurement[]>(base),
    refetchInterval: LIVE_DATA_REFETCH_INTERVAL_MS,
    refetchOnWindowFocus: true,
  });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api(path, { method, body }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['measurements', clientId || 'me'] }),
        ...(!clientId ? [queryClient.invalidateQueries({ queryKey: ['notifications'] })] : []),
      ]);
      await onSaved?.();
      toast('Дневник обновлён');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });
  const numeric = [
    'weight_kg',
    'chest_cm',
    'waist_cm',
    'hips_cm',
    'biceps_cm',
    'thigh_cm',
  ] as const;
  return (
    <Card title="Дневник замеров">
      <form
        className="stack top-gap"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate({ path: base, method: 'POST', body: form });
        }}
      >
        <div className="form-grid diary-form-grid">
          <label className="field">
            <span>Дата</span>
            <input
              type="date"
              value={form.measured_on || ''}
              onChange={(e) => setForm({ ...form, measured_on: e.target.value })}
            />
          </label>
          {numeric.map((key) => (
            <label className="field" key={key}>
              <span>
                {
                  {
                    weight_kg: 'Вес, кг',
                    chest_cm: 'Грудь, см',
                    waist_cm: 'Талия, см',
                    hips_cm: 'Бёдра, см',
                    biceps_cm: 'Бицепс, см',
                    thigh_cm: 'Бедро, см',
                  }[key]
                }
              </span>
              <input
                type="number"
                step="0.1"
                value={form[key] ?? ''}
                onChange={(e) =>
                  setForm({ ...form, [key]: e.target.value === '' ? null : Number(e.target.value) })
                }
              />
            </label>
          ))}
        </div>
        <label className="field">
          <span>Заметка</span>
          <textarea
            value={form.note || ''}
            onChange={(e) => setForm({ ...form, note: e.target.value })}
          />
        </label>
        <button disabled={mutation.isPending}>Сохранить замер</button>
      </form>
      {rows.isLoading ? (
        <LoadingState />
      ) : rows.error ? (
        <ErrorState message={(rows.error as Error).message} />
      ) : !rows.data?.length ? (
        <EmptyState title="Замеров пока нет" />
      ) : (
        <div className="list-grid top-gap">
          {rows.data.map((item) => (
            <article className="list-row" key={item.id}>
              <div className="list-row__main">
                <strong>{item.measured_on}</strong>
                <span>
                  {numeric
                    .filter((key) => item[key] != null)
                    .map(
                      (key) =>
                        `${{ weight_kg: 'Вес', chest_cm: 'Грудь', waist_cm: 'Талия', hips_cm: 'Бёдра', biceps_cm: 'Бицепс', thigh_cm: 'Бедро' }[key]}: ${item[key]}`,
                    )
                    .join(' · ')}
                </span>
                {item.note && <span className="muted">{item.note}</span>}
              </div>
              <button
                className="btn-danger"
                onClick={async () => {
                  if (
                    await confirm({
                      title: 'Удалить замер?',
                      message: item.measured_on,
                      confirmText: 'Удалить',
                    })
                  )
                    mutation.mutate({ path: `${base}/${item.id}`, method: 'DELETE' });
                }}
              >
                Удалить
              </button>
            </article>
          ))}
        </div>
      )}
    </Card>
  );
}
