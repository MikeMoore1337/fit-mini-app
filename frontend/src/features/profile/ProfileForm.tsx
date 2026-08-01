import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { User, UserProfileUpdate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card } from '../../shared/ui/common';

const emptyProfile: UserProfileUpdate = {
  full_name: '',
  goal: 'maintenance',
  level: 'beginner',
  height_cm: null,
  weight_kg: null,
  workouts_per_week: 3,
  cardio_trainings_per_week: 0,
  timezone: 'Europe/Moscow',
};

export function ProfileForm() {
  const { user, reloadUser } = useAuth();
  const { toast } = useFeedback();
  const [form, setForm] = useState<UserProfileUpdate>(() =>
    user?.profile
      ? {
          ...emptyProfile,
          ...user.profile,
          goal: (user.profile.goal as UserProfileUpdate['goal']) ?? null,
          level: (user.profile.level as UserProfileUpdate['level']) ?? null,
        }
      : emptyProfile,
  );

  const mutation = useMutation({
    mutationFn: () => api<User>('/api/v1/me/profile', { method: 'PATCH', body: form }),
    onSuccess: async () => {
      await reloadUser();
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
            <span>Цель</span>
            <select
              value={form.goal ?? 'maintenance'}
              onChange={(e) =>
                setForm({ ...form, goal: e.target.value as UserProfileUpdate['goal'] })
              }
            >
              <option value="fat_loss">Похудение</option>
              <option value="muscle_gain">Набор мышц</option>
              <option value="maintenance">Поддержание</option>
              <option value="recomposition">Рекомпозиция</option>
            </select>
          </label>
          <label className="field">
            <span>Уровень</span>
            <select
              value={form.level ?? 'beginner'}
              onChange={(e) =>
                setForm({ ...form, level: e.target.value as UserProfileUpdate['level'] })
              }
            >
              <option value="beginner">Начальный</option>
              <option value="intermediate">Средний</option>
              <option value="advanced">Продвинутый</option>
            </select>
          </label>
          <label className="field">
            <span>Рост, см</span>
            <input
              type="number"
              min="80"
              max="250"
              value={form.height_cm ?? ''}
              onChange={(e) => setForm({ ...form, height_cm: numberValue(e.target.value) })}
            />
          </label>
          <label className="field">
            <span>Вес, кг</span>
            <input
              type="number"
              min="25"
              max="500"
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
            <input
              value={form.timezone ?? ''}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
              placeholder="Europe/Moscow"
            />
          </label>
        </div>
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Сохраняем…' : 'Сохранить профиль'}
        </button>
      </form>
    </Card>
  );
}
