import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import type { BodyMeasurement, BodyMeasurementSave } from '../../shared/api/types';
import { LIVE_DATA_REFETCH_INTERVAL_MS } from '../../shared/sync';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card, EmptyState, ErrorState, LoadingState } from '../../shared/ui/common';
import { useAuth } from '../../app/AuthProvider';
import { dateInputValue, detectedTimeZone } from '../../shared/dateTime';
import { usePersistentState } from '../../shared/storage';
import { measurementDraftStorageKey } from '../../shared/userScopedStorage';
import { DateInput } from '../../shared/ui/PickerInput';
import { invalidateMeasurementMutation, queryKeys } from '../../shared/queryKeys';

export function Diary({
  clientId,
  timeZone: clientTimeZone,
  onSaved,
}: {
  clientId?: number;
  timeZone?: string | null;
  onSaved?: () => void | Promise<void>;
}) {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const { toast, confirm } = useFeedback();
  const timeZone = clientId
    ? clientTimeZone || detectedTimeZone()
    : user?.profile?.timezone || detectedTimeZone();
  const today = dateInputValue(new Date(), timeZone);
  const [form, setForm, clearDraft] = usePersistentState<BodyMeasurementSave>(
    measurementDraftStorageKey(clientId ? `client_${clientId}` : `user_${user?.id ?? 'me'}`),
    { measured_on: dateInputValue(new Date(), timeZone) },
  );
  const base = clientId
    ? `/api/v1/coach/clients/${clientId}/measurements`
    : '/api/v1/workouts/diary';
  const rows = useQuery({
    queryKey: queryKeys.measurements.subject(clientId),
    queryFn: () => api<BodyMeasurement[]>(base),
    refetchInterval: LIVE_DATA_REFETCH_INTERVAL_MS,
    refetchOnWindowFocus: true,
  });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body?: unknown }) =>
      api(path, { method, body }),
    onSuccess: async () => {
      clearDraft({ measured_on: today });
      await invalidateMeasurementMutation(queryClient, clientId);
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
  const numericLimits: Record<(typeof numeric)[number], { min: number; max: number }> = {
    weight_kg: { min: 20, max: 350 },
    chest_cm: { min: 0.1, max: 300 },
    waist_cm: { min: 0.1, max: 300 },
    hips_cm: { min: 0.1, max: 300 },
    biceps_cm: { min: 0.1, max: 150 },
    thigh_cm: { min: 0.1, max: 200 },
  };
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
            <DateInput
              controlClassName="diary-date-control"
              value={form.measured_on || ''}
              max={today}
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
                    biceps_cm: 'Плечо (окружность), см',
                    thigh_cm: 'Бедро (окружность), см',
                  }[key]
                }
              </span>
              <input
                type="number"
                step="0.1"
                min={numericLimits[key].min}
                max={numericLimits[key].max}
                value={form[key] ?? ''}
                onChange={(e) =>
                  setForm({ ...form, [key]: e.target.value === '' ? null : Number(e.target.value) })
                }
              />
            </label>
          ))}
        </div>
        <div className="auth-notice stack" aria-label="Как делать замеры">
          <strong>Как сравнивать замеры</strong>
          <span>
            Снимайте их в похожее время суток, в одинаковых условиях и накладывайте ленту в одном
            месте. Оценивайте несколько замеров, а не единичное колебание.
          </span>
          <small className="muted">
            Окружность плеча не показывает отдельно размер бицепса, а окружность бедра — размер
            квадрицепса. Эти значения описывают участок тела целиком.
          </small>
        </div>
        <label className="field">
          <span>Заметка</span>
          <textarea
            value={form.note || ''}
            maxLength={500}
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
                        `${{ weight_kg: 'Вес', chest_cm: 'Грудь', waist_cm: 'Талия', hips_cm: 'Бёдра', biceps_cm: 'Окружность плеча', thigh_cm: 'Окружность бедра' }[key]}: ${item[key]}`,
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
