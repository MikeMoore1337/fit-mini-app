const accessTokenKey = 'fit_access_token';
const refreshTokenKey = 'fit_refresh_token';

const state = {
  me: null,
  exercises: [],
  templates: [],
  todayWorkout: null,
  plans: [],
  publicConfig: null,
};

const $ = (id) => document.getElementById(id);

const log = (msg) => {
  const node = $('log');
  if (!node) return;
  const text = typeof msg === 'string' ? msg : JSON.stringify(msg, null, 2);
  node.textContent = `${new Date().toLocaleTimeString()} - ${text}\n${node.textContent}`;
};

function isCoachOrAdmin() {
  return Boolean(state.me?.is_coach || state.me?.is_admin);
}

function toggleCoachUI() {
  const card = $('exerciseAdminCard');
  if (card) card.classList.toggle('hidden', !isCoachOrAdmin());

  const adminLink = $('adminLink');
  if (adminLink) adminLink.classList.toggle('hidden', !isCoachOrAdmin());

  const coachFields = $('coachFields');
  if (coachFields && $('builder_mode')) {
    coachFields.classList.toggle(
      'hidden',
      $('builder_mode').value !== 'coach' || !isCoachOrAdmin()
    );
  }
}

function authHeaders(extra = {}) {
  const token = localStorage.getItem(accessTokenKey);
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: authHeaders(options.headers || {}),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function loadEnv() {
  try {
    const res = await fetch('/api/v1/public/config');
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    state.publicConfig = data;

    const envBadge = $('env-badge');
    const devLoginBtn = $('devLoginBtn');

    if (data.app_env === 'dev' && envBadge) {
      envBadge.textContent = 'dev';
      envBadge.classList.remove('hidden');
    }

    if (data.enable_dev_auth && devLoginBtn) {
      devLoginBtn.classList.remove('hidden');
    }
  } catch (error) {
    console.warn('env load failed', error);
  }
}

async function devLogin() {
  const body = {
    telegram_user_id: Number($('debugUserId')?.value || '1001'),
    full_name: $('debugUserName')?.value || null,
    is_coach: Boolean($('debugIsCoach')?.checked),
  };

  const response = await fetch('/api/v1/auth/dev-login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }

  const data = await response.json();
  localStorage.setItem(accessTokenKey, data.access_token);
  localStorage.setItem(refreshTokenKey, data.refresh_token);

  const authState = $('authState');
  if (authState) {
    authState.textContent = `Авторизован как ${body.telegram_user_id}`;
  }

  await bootstrap();
}

async function telegramLogin() {
  const tg = window.Telegram?.WebApp;
  const initData = tg?.initData;

  if (!initData) {
    if (state.publicConfig?.enable_dev_auth) {
      log('initData отсутствует. Открой Mini App из Telegram или используй Dev login.');
    } else {
      log('initData отсутствует. Открой Mini App из Telegram.');
    }
    return;
  }

  const response = await fetch('/api/v1/auth/telegram/init', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: initData }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }

  const data = await response.json();
  localStorage.setItem(accessTokenKey, data.access_token);
  localStorage.setItem(refreshTokenKey, data.refresh_token);

  const authState = $('authState');
  if (authState) {
    authState.textContent = 'Telegram auth ok';
  }

  await bootstrap();
}

async function loadMe() {
  state.me = await api('/api/v1/me');

  if ($('full_name')) $('full_name').value = state.me.profile?.full_name || '';
  if ($('goal')) $('goal').value = state.me.profile?.goal || '';
  if ($('level')) $('level').value = state.me.profile?.level || '';
  if ($('height_cm')) $('height_cm').value = state.me.profile?.height_cm || '';
  if ($('weight_kg')) $('weight_kg').value = state.me.profile?.weight_kg || '';
  if ($('workouts_per_week')) $('workouts_per_week').value = state.me.profile?.workouts_per_week || '';

  const authState = $('authState');
  if (authState) {
    authState.textContent =
      `Пользователь: ${state.me.profile?.full_name || state.me.telegram_user_id}` +
      ` | coach=${state.me.is_coach} | admin=${state.me.is_admin}`;
  }

  toggleCoachUI();
}

async function saveProfile() {
  const payload = {
    full_name: $('full_name')?.value || null,
    goal: $('goal')?.value || null,
    level: $('level')?.value || null,
    height_cm: $('height_cm')?.value ? Number($('height_cm').value) : null,
    weight_kg: $('weight_kg')?.value ? Number($('weight_kg').value) : null,
    workouts_per_week: $('workouts_per_week')?.value
      ? Number($('workouts_per_week').value)
      : null,
  };

  await api('/api/v1/me/profile', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });

  log('Профиль сохранён');
  await loadMe();
}

async function loadExercises() {
  state.exercises = await api('/api/v1/programs/exercises');
  renderExerciseCatalog();
}

function renderExerciseCatalog() {
  const list = $('exerciseCatalogList');
  if (!list) return;

  list.innerHTML =
    state.exercises
      .map(
        (ex) => `
        <div class="item-card">
          <strong>${ex.title}</strong>
          <div class="exercise-meta">
            <span class="metric-pill">${ex.primary_muscle}</span>
            <span class="metric-pill">${ex.equipment}</span>
          </div>
        </div>
      `
      )
      .join('') || '<p class="muted">Упражнений пока нет</p>';
}

async function createExercise() {
  if (!isCoachOrAdmin()) {
    log('Добавлять упражнения могут только тренер и админ');
    return;
  }

  const payload = {
    title: $('newExerciseTitle')?.value.trim(),
    primary_muscle: $('newExerciseMuscle')?.value.trim(),
    equipment: $('newExerciseEquipment')?.value.trim(),
  };

  if (!payload.title || !payload.primary_muscle || !payload.equipment) {
    log('Заполни название, мышечную группу и оборудование');
    return;
  }

  const created = await api('/api/v1/programs/exercises', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if ($('newExerciseTitle')) $('newExerciseTitle').value = '';
  if ($('newExerciseMuscle')) $('newExerciseMuscle').value = '';
  if ($('newExerciseEquipment')) $('newExerciseEquipment').value = '';

  log(`Добавлено упражнение: ${created.title}`);
  await loadExercises();
}

function exerciseTemplate(defaultExerciseId = '', preset = null) {
  const options = state.exercises
    .map(
      (ex) => `
        <option value="${ex.id}" ${String(ex.id) === String(defaultExerciseId) ? 'selected' : ''}>
          ${ex.title}
        </option>
      `
    )
    .join('');

  return `
    <div class="grid item-card program-ex-row" style="grid-template-columns:2fr 1fr 1fr 1fr;">
      <select class="exercise-id">${options}</select>
      <input class="exercise-sets" type="number" min="1" value="${preset?.prescribed_sets || 3}" placeholder="Подходы" />
      <input class="exercise-reps" value="${preset?.prescribed_reps || '8-10'}" placeholder="Повторы" />
      <input class="exercise-rest" type="number" min="15" value="${preset?.rest_seconds || 90}" placeholder="Отдых" />
    </div>
  `;
}

function programDayTemplate(index, preset = null) {
  return `
    <div class="item-card day-card" data-day-index="${index}">
      <div class="toolbar wrap">
        <input class="day-title" placeholder="Название дня" value="${preset?.title || `День ${index + 1}`}" />
        <button class="secondary add-ex-btn" type="button">+ Упражнение</button>
      </div>
      <div class="stack exercises-list">
        ${(preset?.exercises || []).map((ex) => exerciseTemplate(ex.exercise_id, ex)).join('')}
      </div>
    </div>
  `;
}

function addDay(preset = null) {
  const idx = document.querySelectorAll('.day-card').length;
  const wrapper = document.createElement('div');
  wrapper.innerHTML = programDayTemplate(idx, preset);

  const node = wrapper.firstElementChild;
  $('dayBuilder')?.appendChild(node);

  const addExerciseBtn = node.querySelector('.add-ex-btn');
  if (addExerciseBtn) {
    addExerciseBtn.onclick = () => {
      const row = document.createElement('div');
      row.innerHTML = exerciseTemplate();
      const exerciseNode = row.firstElementChild;
      node.querySelector('.exercises-list')?.appendChild(exerciseNode);
    };
  }

  if (!preset?.exercises?.length) {
    addExerciseBtn?.click();
  }
}

function fillExample() {
  const dayBuilder = $('dayBuilder');
  if (!dayBuilder) return;

  dayBuilder.innerHTML = '';

  addDay({
    title: 'Верх тела A',
    exercises: [
      { exercise_id: 1, prescribed_sets: 4, prescribed_reps: '6-8', rest_seconds: 120 },
      { exercise_id: 2, prescribed_sets: 4, prescribed_reps: '8-10', rest_seconds: 120 },
    ],
  });

  addDay({
    title: 'Низ тела A',
    exercises: [
      { exercise_id: 3, prescribed_sets: 4, prescribed_reps: '6-8', rest_seconds: 150 },
      { exercise_id: 4, prescribed_sets: 3, prescribed_reps: '8-10', rest_seconds: 120 },
    ],
  });
}

function collectProgramPayload() {
  const days = [...document.querySelectorAll('.day-card')].map((day) => ({
    title: day.querySelector('.day-title')?.value || 'День',
    exercises: [...day.querySelectorAll('.program-ex-row')].map((row) => ({
      exercise_id: Number(row.querySelector('.exercise-id')?.value),
      prescribed_sets: Number(row.querySelector('.exercise-sets')?.value),
      prescribed_reps: row.querySelector('.exercise-reps')?.value,
      rest_seconds: Number(row.querySelector('.exercise-rest')?.value),
    })),
  }));

  return {
    title: $('program_title')?.value,
    goal: $('program_goal')?.value,
    level: $('program_level')?.value,
    mode: $('builder_mode')?.value,
    target_telegram_user_id: $('target_telegram_user_id')?.value
      ? Number($('target_telegram_user_id').value)
      : null,
    target_full_name: $('target_full_name')?.value || null,
    days,
    assign_after_create: true,
  };
}

async function saveProgram() {
  const payload = collectProgramPayload();
  const data = await api('/api/v1/programs/templates', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if ($('builderResult')) {
    $('builderResult').textContent =
      `Сохранено: ${data.template.title}, тренировок создано: ${data.workouts_created}`;
  }

  log(data);
  await loadTemplates();
  await loadClients();
  await loadTodayWorkout();
  await loadNotifications();
}

async function loadTemplates() {
  state.templates = await api('/api/v1/programs/templates/mine');

  const list = $('templatesList');
  if (!list) return;

  list.innerHTML =
    state.templates
      .map(
        (t) => `
        <div class="item-card">
          <strong>${t.title}</strong><br>
          <span class="muted">${t.goal} - ${t.level}</span>
          <div>
            ${t.days
              .map(
                (d) => `
                  <div><b>${d.title}</b>: ${d.exercises.map((e) => e.exercise_title).join(', ')}</div>
                `
              )
              .join('')}
          </div>
        </div>
      `
      )
      .join('') || '<p class="muted">Шаблонов пока нет</p>';
}

async function loadClients() {
  const rows = await api('/api/v1/programs/clients');

  const list = $('clientsList');
  if (!list) return;

  list.innerHTML =
    rows
      .map(
        (c) => `
        <div class="item-card">
          <strong>${c.full_name || c.telegram_user_id}</strong><br>
          <span class="muted">goal=${c.goal || '-'} | level=${c.level || '-'}</span>
        </div>
      `
      )
      .join('') || '<p class="muted">Клиентов пока нет</p>';
}

function statusLabel(status) {
  return {
    planned: 'Запланирована',
    in_progress: 'В процессе',
    completed: 'Завершена',
  }[status] || status;
}

function formatSetValue(set) {
  const reps = set?.actual_reps ?? '-';
  const weight = set?.actual_weight ?? '-';
  return `${reps}×${weight}`;
}

function formatDelta(value, unit = '') {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return 'без изменений';
  }

  const numberValue = Number(value);
  if (numberValue === 0) {
    return 'без изменений';
  }

  const sign = numberValue > 0 ? '+' : '';
  return `${sign}${numberValue.toFixed(0)}${unit}`;
}

function renderLoggedSets(exercise) {
  const loggedMap = new Map(
    (exercise.logged_sets || []).map((set) => [set.set_number, set])
  );

  return Array.from({ length: exercise.prescribed_sets })
    .map((_, i) => {
      const setNumber = i + 1;
      const set = loggedMap.get(setNumber);

      if (set) {
        return `<span class="set-chip done" title="Подход ${setNumber}">${formatSetValue(set)}</span>`;
      }

      return `<span class="set-chip empty" title="Подход ${setNumber}">${setNumber}</span>`;
    })
    .join('');
}

function renderPreviousSets(exercise) {
  if (!exercise.previous_logged_sets?.length) {
    return '<span class="muted">Нет предыдущих данных</span>';
  }

  return exercise.previous_logged_sets
    .map(
      (set) =>
        `<span class="set-chip previous" title="Прошлый подход ${set.set_number}">${formatSetValue(set)}</span>`
    )
    .join('');
}

function renderProgress(exercise) {
  if (!exercise.progress) {
    return '<div class="muted progress-line">Прошлой тренировки по этому упражнению пока нет</div>';
  }

  const dateLabel = exercise.progress.previous_workout_date
    ? new Date(exercise.progress.previous_workout_date).toLocaleDateString()
    : '';

  return `
    <div class="progress-box">
      <div class="progress-head">
        Прошлый раз: ${exercise.progress.previous_workout_title || 'Тренировка'}
        ${dateLabel ? ` - ${dateLabel}` : ''}
      </div>
      <div class="set-badges previous-row">${renderPreviousSets(exercise)}</div>
      <div class="progress-metrics">
        <span class="metric-pill">Тоннаж: ${formatDelta(exercise.progress.volume_delta, ' кг')}</span>
        <span class="metric-pill">Топ вес: ${formatDelta(exercise.progress.top_weight_delta, ' кг')}</span>
      </div>
    </div>
  `;
}

async function loadTodayWorkout() {
  const workout = await api('/api/v1/workouts/today');
  state.todayWorkout = workout;

  const container = $('todayWorkout');
  if (!container) return;

  if (!workout) {
    container.innerHTML = '<p class="muted">На сегодня тренировка не назначена</p>';
    return;
  }

  container.innerHTML = `
    <div>
      <p><strong>${workout.title}</strong> - статус: ${statusLabel(workout.status)}</p>
      <div class="toolbar wrap">
        <button id="startWorkoutBtn" ${!workout.can_start ? 'disabled' : ''}>Начать</button>
        <button id="completeWorkoutBtn" class="secondary" ${!workout.can_complete ? 'disabled' : ''}>Завершить</button>
      </div>
      <div class="stack">
        ${workout.exercises
          .map(
            (exercise) => `
            <div class="item-card">
              <strong>${exercise.title}</strong><br>
              <span class="muted">${exercise.prescribed_sets} подходов x ${exercise.prescribed_reps}, отдых ${exercise.rest_seconds} сек</span>
              <div class="set-badges current-row">${renderLoggedSets(exercise)}</div>
              ${renderProgress(exercise)}
              <div class="set-actions">
                <input type="number" id="reps-${exercise.id}" placeholder="Повт" ${!workout.can_log_sets ? 'disabled' : ''} />
                <input type="number" id="weight-${exercise.id}" placeholder="Вес" ${!workout.can_log_sets ? 'disabled' : ''} />
                <button data-ex-id="${exercise.id}" class="log-set-btn" ${!workout.can_log_sets ? 'disabled' : ''}>+ Подход</button>
                <button data-ex-id="${exercise.id}" class="secondary undo-set-btn" ${!workout.can_log_sets ? 'disabled' : ''}>Отменить</button>
              </div>
            </div>
          `
          )
          .join('')}
      </div>
    </div>
  `;

  const startBtn = $('startWorkoutBtn');
  if (startBtn) {
    startBtn.onclick = async () => {
      await api(`/api/v1/workouts/${workout.id}/start`, { method: 'POST' });
      await loadTodayWorkout();
    };
  }

  const completeBtn = $('completeWorkoutBtn');
  if (completeBtn) {
    completeBtn.onclick = async () => {
      await api(`/api/v1/workouts/${workout.id}/complete`, { method: 'POST' });
      await loadTodayWorkout();
    };
  }

  document.querySelectorAll('.log-set-btn').forEach((btn) => {
    btn.onclick = async (event) => {
      const exId = Number(event.target.dataset.exId);
      const exercise = workout.exercises.find((x) => x.id === exId);

      const payload = {
        workout_exercise_id: exId,
        set_number: exercise.completed_sets + 1,
        actual_reps: Number($(`reps-${exId}`)?.value || '0') || null,
        actual_weight: Number($(`weight-${exId}`)?.value || '0') || null,
        is_completed: true,
      };

      await api(`/api/v1/workouts/${workout.id}/sets`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      await loadTodayWorkout();
    };
  });

  document.querySelectorAll('.undo-set-btn').forEach((btn) => {
    btn.onclick = async (event) => {
      const exId = Number(event.target.dataset.exId);

      await api(`/api/v1/workouts/${workout.id}/exercises/${exId}/last-set`, {
        method: 'DELETE',
      });

      await loadTodayWorkout();
    };
  });
}

async function assignDemoProgram() {
  await api('/api/v1/programs/assign-demo', { method: 'POST' });
  await loadTodayWorkout();
  await loadNotifications();
}

async function loadBilling() {
  state.plans = await api('/api/v1/billing/plans');
  const subscription = await api('/api/v1/billing/subscription');

  if ($('subscriptionInfo')) {
    $('subscriptionInfo').textContent = subscription
      ? `Активна: ${subscription.plan_title} до ${new Date(subscription.ends_at).toLocaleString()}`
      : 'Активной подписки нет';
  }

  const plansList = $('plansList');
  if (!plansList) return;

  plansList.innerHTML = state.plans
    .map(
      (plan) => `
      <div class="item-card">
        <strong>${plan.title}</strong><br>
        <span class="muted">${plan.price} ${plan.currency} / ${plan.period_days} дн.</span>
        <div class="toolbar wrap">
          <button data-plan="${plan.code}" class="buy-plan-btn">Купить</button>
        </div>
      </div>
    `
    )
    .join('');

  document.querySelectorAll('.buy-plan-btn').forEach((btn) => {
    btn.onclick = async (event) => {
      const planCode = event.target.dataset.plan;

      const checkout = await api('/api/v1/billing/checkout', {
        method: 'POST',
        body: JSON.stringify({ plan_code: planCode }),
      });

      await api(`/api/v1/billing/mock/complete/${checkout.checkout_id}`, {
        method: 'POST',
      });

      log(`Подписка ${planCode} активирована через mock payment`);
      await loadBilling();
    };
  });
}

async function loadNotifications() {
  const settings = await api('/api/v1/notifications/settings');

  if ($('notifEnabled')) $('notifEnabled').checked = settings.workout_reminders_enabled;
  if ($('notifHour')) $('notifHour').value = settings.reminder_hour;

  const rows = await api('/api/v1/notifications');
  const list = $('notificationsList');
  if (!list) return;

  list.innerHTML =
    rows
      .map(
        (n) => `
        <div class="item-card">
          <strong>${n.title}</strong><br>
          <span class="muted">${new Date(n.scheduled_for).toLocaleString()} - ${n.status}</span>
          <div>${n.body}</div>
        </div>
      `
      )
      .join('') || '<p class="muted">Нет уведомлений</p>';
}

async function saveNotificationSettings() {
  await api('/api/v1/notifications/settings', {
    method: 'PATCH',
    body: JSON.stringify({
      workout_reminders_enabled: Boolean($('notifEnabled')?.checked),
      reminder_hour: Number($('notifHour')?.value || '9'),
    }),
  });

  await loadNotifications();
}

function bindBuilder() {
  if ($('builder_mode') && $('coachFields')) {
    $('builder_mode').addEventListener('change', () => {
      $('coachFields').classList.toggle(
        'hidden',
        $('builder_mode').value !== 'coach' || !isCoachOrAdmin()
      );
    });
  }

  if ($('addDayBtn')) $('addDayBtn').onclick = () => addDay();
  if ($('fillExampleBtn')) $('fillExampleBtn').onclick = fillExample;
  if ($('saveProgramBtn')) $('saveProgramBtn').onclick = saveProgram;
}

async function bootstrap() {
  try {
    await loadMe();
    await loadExercises();

    if (!document.querySelector('.day-card')) {
      fillExample();
    }

    await Promise.all([
      loadTemplates(),
      loadClients(),
      loadTodayWorkout(),
      loadBilling(),
      loadNotifications(),
    ]);
  } catch (error) {
    log(String(error));
  }
}

async function init() {
  await loadEnv();

  if ($('devLoginBtn')) {
    $('devLoginBtn').onclick = async () => {
      try {
        await devLogin();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('telegramLoginBtn')) {
    $('telegramLoginBtn').onclick = async () => {
      try {
        await telegramLogin();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('saveProfileBtn')) {
    $('saveProfileBtn').onclick = async () => {
      try {
        await saveProfile();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('assignProgramBtn')) {
    $('assignProgramBtn').onclick = async () => {
      try {
        await assignDemoProgram();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('reloadTemplatesBtn')) {
    $('reloadTemplatesBtn').onclick = async () => {
      try {
        await loadTemplates();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('reloadExercisesBtn')) {
    $('reloadExercisesBtn').onclick = async () => {
      try {
        await loadExercises();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('createExerciseBtn')) {
    $('createExerciseBtn').onclick = async () => {
      try {
        await createExercise();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('reloadClientsBtn')) {
    $('reloadClientsBtn').onclick = async () => {
      try {
        await loadClients();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('reloadBillingBtn')) {
    $('reloadBillingBtn').onclick = async () => {
      try {
        await loadBilling();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('reloadNotificationsBtn')) {
    $('reloadNotificationsBtn').onclick = async () => {
      try {
        await loadNotifications();
      } catch (error) {
        log(String(error));
      }
    };
  }

  if ($('saveNotifBtn')) {
    $('saveNotifBtn').onclick = async () => {
      try {
        await saveNotificationSettings();
      } catch (error) {
        log(String(error));
      }
    };
  }

  bindBuilder();

  if (localStorage.getItem(accessTokenKey)) {
    await bootstrap();
  }
}

init();