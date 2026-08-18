import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../../app/AuthProvider';
import { api } from '../../shared/api/client';
import type { ApiSchemas, User, UserProfileUpdate } from '../../shared/api/types';
import { useFeedback } from '../../shared/ui/FeedbackProvider';
import { Card } from '../../shared/ui/common';
import { detectedTimeZone } from '../../shared/dateTime';
import { usePersistentState } from '../../shared/storage';
import { getTimezoneOptions } from './timezones';
import { DateInput } from '../../shared/ui/PickerInput';
import { profileGoals } from './goals';

const emptyProfile: UserProfileUpdate = {
  full_name: '',
  birth_date: null,
  goal: null,
  level: null,
  height_cm: null,
  weight_kg: null,
  workouts_per_week: 3,
  cardio_trainings_per_week: 0,
  resting_heart_rate: null,
  timezone: detectedTimeZone(),
};

const cardioRecommendationDescriptions = {
  fat_loss:
    'Рекомендуемый диапазон для продолжительного кардио с акцентом на расход энергии и сохранение восстановления.',
  recomposition:
    'Умеренное кардио, которое помогает контролировать энергозатраты и поддерживать выносливость без излишней нагрузки на восстановление после силовых тренировок.',
  maintenance:
    'Комфортная умеренная нагрузка для поддержания аэробной формы, здоровья и общей активности.',
  muscle_gain:
    'Лёгкое или умеренное кардио для поддержания выносливости с минимальной дополнительной нагрузкой на восстановление и силовые тренировки.',
} as const;

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
  const validBirthDate = /^\d{4}-\d{2}-\d{2}$/.test(form.birth_date ?? '');
  const validRestingHeartRate =
    form.resting_heart_rate == null ||
    (form.resting_heart_rate >= 30 && form.resting_heart_rate <= 120);
  const heartRatePreview = useQuery({
    queryKey: ['heart-rate-preview', form.birth_date, form.resting_heart_rate, form.goal],
    queryFn: () =>
      api<ApiSchemas['HeartRatePreviewResponse']>('/api/v1/me/profile/heart-rates/preview', {
        method: 'POST',
        body: {
          birth_date: form.birth_date,
          resting_heart_rate: form.resting_heart_rate,
          goal: form.goal,
        },
      }),
    enabled: validBirthDate && validRestingHeartRate,
    retry: false,
  });
  const heartRate = heartRatePreview.data;
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
        <div className="form-grid profile-form-grid">
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
            <DateInput
              controlClassName="profile-birth-date-control"
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
              {profileGoals.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
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
            <span>Средний пульс в покое, уд/мин</span>
            <input
              type="number"
              min="30"
              max="120"
              step="1"
              value={form.resting_heart_rate ?? ''}
              onChange={(e) =>
                setForm({ ...form, resting_heart_rate: numberValue(e.target.value) })
              }
            />
            <small className="field-hint">
              Укажите средний пульс в состоянии покоя. Лучше использовать среднее значение за
              несколько дней. Если не используете часы или браслет, измеряйте пульс утром после
              пробуждения до кофе и физической активности в течение 3–7 дней и укажите среднее
              значение.
            </small>
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
        {heartRatePreview.isError && validBirthDate && validRestingHeartRate && (
          <div className="nutrition-warning" role="alert">
            Проверьте значение пульса в покое. Если оно указано верно и заметно отличается от вашего
            обычного значения, ориентируйтесь на рекомендации врача.
          </div>
        )}
        {heartRate && (
          <section className="auth-notice stack" aria-labelledby="heart-rate-zones-title">
            <div className="metric-grid">
              <div className="metric">
                <span>Максимальный расчётный пульс</span>
                <strong>{heartRate.estimated_max_heart_rate} уд/мин</strong>
                <small>
                  Расчётное значение по возрасту. Реальный максимальный пульс может отличаться.
                </small>
              </div>
              {heartRate.recommended_cardio_range && (
                <div className="metric">
                  <span>Рекомендуемый пульс для кардио</span>
                  <strong>
                    {heartRate.recommended_cardio_range.min_bpm}–
                    {heartRate.recommended_cardio_range.max_bpm} уд/мин
                  </strong>
                  {form.goal && <small>{cardioRecommendationDescriptions[form.goal]}</small>}
                </div>
              )}
            </div>
            {!heartRate.recommended_cardio_range && (
              <p className="muted">
                Укажите средний пульс в покое, чтобы получить более персональный расчёт и
                рекомендуемый диапазон для кардио.
              </p>
            )}
            <div>
              <strong id="heart-rate-zones-title">Пульсовые зоны</strong>
              <p className="muted">
                {heartRate.heart_rate_calculation_method === 'heart_rate_reserve'
                  ? 'Персональный расчёт с учётом пульса в покое.'
                  : 'Базовый расчёт по максимальному пульсу.'}
              </p>
            </div>
            <div className="list-grid">
              {heartRate.heart_rate_zones.map((zone) => (
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
              Пульсовые зоны являются расчётным ориентиром. Индивидуальные физиологические пороги
              могут отличаться.
            </small>
            <small className="muted">
              Смарт-часы и фитнес-браслеты могут измерять пульс с погрешностью. Для расчёта лучше
              использовать среднее значение за несколько дней, а не единичное измерение.
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
