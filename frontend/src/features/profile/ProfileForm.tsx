import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { User, UserProfileUpdate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card } from '../../shared/ui/common';
import { detectedTimeZone } from '../../shared/dateTime';
import { usePersistentState } from '../../shared/storage';
import { getTimezoneOptions } from './timezones';
import { calculateTanakaZones } from './heartRateZones';

const emptyProfile: UserProfileUpdate = {
  full_name: '',
  birth_date: null,
  goal: null,
  level: null,
  height_cm: null,
  weight_kg: null,
  workouts_per_week: 3,
  cardio_trainings_per_week: 0,
  timezone: detectedTimeZone(),
};

export function ProfileForm() {
  const { user, reloadUser } = useAuth();
  const { toast } = useFeedback();
  const queryClient = useQueryClient();
  const [form, setForm, clearDraft] = usePersistentState<UserProfileUpdate>(
    `fit_profile_draft_${user?.id ?? 'anonymous'}`,
    () =>
      user?.profile
        ? {
            ...emptyProfile,
            ...user.profile,
            goal: (user.profile.goal as UserProfileUpdate['goal']) ?? null,
            level: (user.profile.level as UserProfileUpdate['level']) ?? null,
          }
        : emptyProfile,
  );
  const timezoneOptions = getTimezoneOptions(form.timezone);
  const heartRate = calculateTanakaZones(form.birth_date);
  const latestBirthDate = new Date();
  latestBirthDate.setFullYear(latestBirthDate.getFullYear() - 10);

  const mutation = useMutation({
    mutationFn: () => api<User>('/api/v1/me/profile', { method: 'PATCH', body: form }),
    onSuccess: async () => {
      clearDraft();
      await reloadUser();
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['workout'] }),
        queryClient.invalidateQueries({ queryKey: ['notifications'] }),
      ]);
      toast('Профиль сохранён');
    },
    onError: (reason) => toast((reason as Error).message, 'error'),
  });

  const numberValue = (value: string) => (value === '' ? null : Number(value));
  return (
    <Card
      title="Профиль"
      description="Эти параметры используются при составлении программы и расчёте питания."
    >
      <form
        className="stack top-gap"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="form-grid">
          <label className="field">
            <span>Имя</span>
            <input
              value={form.full_name ?? ''}
              maxLength={128}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
            />
          </label>
          <label className="field">
            <span>Дата рождения</span>
            <input
              type="date"
              max={latestBirthDate.toISOString().slice(0, 10)}
              value={form.birth_date ?? ''}
              onChange={(event) => setForm({ ...form, birth_date: event.target.value || null })}
            />
            <small className="field-hint">Нужна для расчёта пульсовых зон по Танаки.</small>
          </label>
          <label className="field">
            <span>Цель</span>
            <select
              value={form.goal ?? ''}
              required
              onChange={(e) =>
                setForm({ ...form, goal: e.target.value as UserProfileUpdate['goal'] })
              }
            >
              <option value="" disabled>
                Выберите цель
              </option>
              <option value="fat_loss">Похудение</option>
              <option value="muscle_gain">Набор мышц</option>
              <option value="maintenance">Поддержание</option>
              <option value="recomposition">Рекомпозиция</option>
            </select>
          </label>
          <label className="field">
            <span>Уровень</span>
            <select
              value={form.level ?? ''}
              required
              onChange={(e) =>
                setForm({ ...form, level: e.target.value as UserProfileUpdate['level'] })
              }
            >
              <option value="" disabled>
                Выберите уровень
              </option>
              <option value="beginner">Начальный</option>
              <option value="intermediate">Средний</option>
              <option value="advanced">Продвинутый</option>
            </select>
          </label>
          <label className="field">
            <span>Рост, см</span>
            <input
              type="number"
              min="100"
              max="250"
              value={form.height_cm ?? ''}
              onChange={(e) => setForm({ ...form, height_cm: numberValue(e.target.value) })}
            />
          </label>
          <label className="field">
            <span>Вес, кг</span>
            <input
              type="number"
              min="20"
              max="350"
              step="0.1"
              value={form.weight_kg ?? ''}
              onChange={(e) => setForm({ ...form, weight_kg: numberValue(e.target.value) })}
            />
          </label>
          <label className="field">
            <span>Силовых в неделю</span>
            <input
              type="number"
              min="0"
              max="14"
              value={form.workouts_per_week ?? ''}
              onChange={(e) => setForm({ ...form, workouts_per_week: numberValue(e.target.value) })}
            />
          </label>
          <label className="field">
            <span>Кардио в неделю</span>
            <input
              type="number"
              min="0"
              max="14"
              value={form.cardio_trainings_per_week ?? ''}
              onChange={(e) =>
                setForm({ ...form, cardio_trainings_per_week: numberValue(e.target.value) })
              }
            />
          </label>
          <label className="field">
            <span>Часовой пояс</span>
            <select
              value={form.timezone ?? ''}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
            >
              {timezoneOptions.map((timezone) => (
                <option value={timezone} key={timezone}>
                  {timezone}
                </option>
              ))}
            </select>
            <small className="field-hint">
              Даты тренировок и время уведомлений рассчитываются в этом часовом поясе.
            </small>
          </label>
        </div>
        {heartRate && (
          <section className="auth-notice stack" aria-labelledby="heart-rate-zones-title">
            <div>
              <strong id="heart-rate-zones-title">Пульсовые зоны по формуле Танаки</strong>
              <p className="muted">
                Возраст: {heartRate.age} · расчётный максимальный пульс: {heartRate.maximum} уд/мин
              </p>
            </div>
            <div className="list-grid">
              {heartRate.zones.map((zone) => (
                <div className="list-row" key={zone.zone}>
                  <span>
                    Зона {zone.zone}. {zone.title}
                  </span>
                  <strong>
                    {zone.min_bpm}–{zone.max_bpm} уд/мин
                  </strong>
                </div>
              ))}
            </div>
            <small className="muted">
              Это ориентировочный расчёт для планирования кардио, а не медицинская рекомендация.
            </small>
          </section>
        )}
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Сохраняем…' : 'Сохранить профиль'}
        </button>
      </form>
    </Card>
  );
}
