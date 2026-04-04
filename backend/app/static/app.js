const APP_VERSION = 'v7';

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

const API = {
  publicConfig: '/api/v1/public/config',
  telegramInit: '/api/v1/auth/telegram/init',
  devLogin: '/api/v1/auth/dev-login',
  me: '/api/v1/me',
  meProfile: '/api/v1/me/profile',

  exercises: '/api/v1/programs/exercises',
  saveTemplate: '/api/v1/programs/templates',
  myTemplates: '/api/v1/programs/templates/mine',
  clients: '/api/v1/programs/clients',
  assignDemo: '/api/v1/programs/assign-demo',

  todayWorkout: '/api/v1/workouts/today',
  billingPlans: '/api/v1/billing/plans',
  billingSubscription: '/api/v1/billing/subscription',
  billingCheckout: '/api/v1/billing/checkout',
  notificationsSettings: '/api/v1/notifications/settings',
  notifications: '/api/v1/notifications',
};

const $ = (id) => document.getElementById(id);

function log(msg) {
  const node = $('log');
  if (!node) return;
  const text = typeof msg === 'string' ? msg : JSON.stringify(msg, null, 2);
  node.textContent = `${new Date().toLocaleTimeString()} - ${text}\n${node.textContent}`;
}

function showToast(message, type = 'success') {
  const toast = $('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = type === 'error' ? 'toast error' : 'toast';
  setTimeout(() => {
    toast.className = 'toast hidden';
  }, 2500);
}

function setVersion() {
  const node = $('appVersion');
  if (node) {
    node.textContent = `frontend: ${APP_VERSION}`;
  }
}

window.onerror = function (message, source, lineno, colno, error) {
  log({
    type: 'window.onerror',
    message,
    source,
    lineno,
    colno,
    stack: error?.stack || null,
  });
};

window.onunhandledrejection = function (event) {
  log({
    type: 'unhandledrejection',
    reason: String(event.reason),
    stack: event.reason?.stack || null,
  });
};

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

  const text = await response.text();

  if (!response.ok) {
    log({
      apiError: true,
      path,
      status: response.status,
      response: text,
    });
    throw new Error(`${response.status} ${text}`);
  }

  if (response.status === 204) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function setAuthState(text) {
  const node = $('authState');
  if (node) node.textContent = text;
}

function isCoachOrAdmin() {
  return Boolean(state.me?.is_coach || state.me?.is_admin);
}

function toggleCoachUI() {
  const card = $('exerciseAdminCard');
  if (card) card.classList.toggle('hidden', !isCoachOrAdmin());

  const adminLink = $('adminLink');
  if (adminLink) adminLink.classList.toggle('hidden', !isCoachOrAdmin());

  const coachFields = $('coachFields');
  const builderMode = $('builder_mode');

  if (coachFields && builderMode) {
    coachFields.classList.toggle(
      'hidden',
      builderMode.value !== 'coach' || !isCoachOrAdmin()
    );
  }
}

function toggleDevAuthUI() {
  const devBlock = $('devAuthBlock');
  const devBtn = $('devLoginBtn');
  const enabled = Boolean(state.publicConfig?.enable_dev_auth);

  if (devBlock) devBlock.classList.toggle('hidden', !enabled);
  if (devBtn) devBtn.classList.toggle('hidden', !enabled);
}

function renderTelegramDebug() {
  const node = $('tgDebug');
  if (!node) return;

  const tg = window.Telegram?.WebApp;

  node.textContent = JSON.stringify(
    {
      appVersion: APP_VERSION,
      hasTelegramObject: Boolean(window.Telegram),
      hasWebAppObject: Boolean(tg),
      initDataPresent: Boolean(tg?.initData),
      initDataLength: tg?.initData?.length || 0,
      initDataUnsafePresent: Boolean(tg?.initDataUnsafe),
      platform: tg?.platform || null,
      version: tg?.version || null,
      isExpanded: tg?.isExpanded ?? null,
    },
    null,
    2
  );
}

async function loadEnv() {
  state.publicConfig = await api(API.publicConfig);

  const envBadge = $('env-badge');
  if (envBadge && state.publicConfig.app_env === 'dev') {
    envBadge.textContent = 'dev';
    envBadge.classList.remove('hidden');
  }

  toggleDevAuthUI();
}

async function telegramLogin() {
  const tg = window.Telegram?.WebApp;
  const initData = tg?.initData;

  log({
    telegramLogin: true,
    hasTelegram: Boolean(window.Telegram),
    hasWebApp: Boolean(tg),
    initDataPresent: Boolean(initData),
    initDataLength: initData?.length || 0,
  });

  if (!initData) {
    setAuthState('Нет данных Telegram');
    showToast('Telegram не передал initData', 'error');
    return false;
  }

  const data = await api(API.telegramInit, {
    method: 'POST',
    body: JSON.stringify({ init_data: initData }),
  });

  localStorage.setItem(accessTokenKey, data.access_token);
  localStorage.setItem(refreshTokenKey, data.refresh_token);

  setAuthState('Вход через Telegram выполнен');
  showToast('Вход через Telegram выполнен');
  await bootstrap();
  return true;
}

async function tryTelegramAutoLogin() {
  try {
    return await telegramLogin();
  } catch (error) {
    log(`Ошибка Telegram auth: ${String(error)}`);
    setAuthState('Не удалось войти через Telegram');
    showToast('Не удалось войти через Telegram', 'error');
    return false;
  }
}

async function loadMe() {
  state.me = await api(API.me);

  const profile = state.me.profile || {};

  if ($('full_name')) $('full_name').value = profile.full_name || '';
  if ($('goal')) $('goal').value = profile.goal || '';
  if ($('level')) $('level').value = profile.level || '';
  if ($('height_cm')) $('height_cm').value = profile.height_cm || '';
  if ($('weight_kg')) $('weight_kg').value = profile.weight_kg || '';
  if ($('workouts_per_week')) $('workouts_per_week').value = profile.workouts_per_week || '';

  setAuthState(
    `Пользователь: ${profile.full_name || state.me.telegram_user_id} | тренер=${state.me.is_coach} | админ=${state.me.is_admin}`
  );

  toggleCoachUI();
}

async function saveProfile() {
  const payload = {
    full_name: $('full_name')?.value || null,
    goal: $('goal')?.value || null,
    level: $('level')?.value || null,
    height_cm: $('height_cm')?.value ? Number($('height_cm').value) : null,
    weight_kg: $('weight_kg')?.value ? Number($('weight_kg').value) : null,
    workouts_per_week: $('workouts_per_week')?.value ? Number($('workouts_per_week').value) : null,
  };

  await api(API.meProfile, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });

  showToast('Профиль сохранён');
  await loadMe();
}

async function loadExercises() {
  state.exercises = await api(API.exercises);
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

function exerciseTemplate(defaultExerciseId = '', preset = null) {
  const options = state.exercises
    .map(
      (ex) =>
        `<option value="${ex.id}" ${String(ex.id) === String(defaultExerciseId) ? 'selected' : ''}>${ex.title}</option>`
    )
    .join('');

  return `
    <div class="grid item-card program-ex-row" style="grid-template-columns:2fr 1fr 1fr 1fr;">
      <select class="exercise-id">${options}</select>
      <input class="exercise-sets" type="number" min="1" value="${preset?.prescribed_sets || 3}" placeholder="Подходы" />
      <input class="exercise-reps" type="text" value="${preset?.prescribed_reps || '8-10'}" placeholder="Повторы" />
      <input class="exercise-rest" type="number" min="15" value="${preset?.rest_seconds || 90}" placeholder="Отдых, сек" />
    </div>
  `;
}

function programDayTemplate(index, preset = null) {
  return `
    <div class="item-card day-card" data-day-index="${index}">
      <div class="toolbar wrap">
        <input class="day-title" type="text" placeholder="Название дня" value="${preset?.title || `День ${index + 1}`}" />
        <button class="secondary add-ex-btn" type="button">+ Упражнение</button>
      </div>
      <div class="stack exercises-list">
        ${(preset?.exercises || []).map((ex) => exerciseTemplate(ex.exercise_id, ex)).join('')}
      </div>
    </div>
  `;
}

function addDay(preset = null) {
  const dayBuilder = $('dayBuilder');
  if (!dayBuilder) {
    log('dayBuilder not found');
    return;
  }

  const idx = dayBuilder.querySelectorAll('.day-card').length;
  const wrapper = document.createElement('div');
  wrapper.innerHTML = programDayTemplate(idx, preset);

  const node = wrapper.firstElementChild;
  dayBuilder.appendChild(node);

  const addExBtn = node.querySelector('.add-ex-btn');
  if (addExBtn) {
    addExBtn.onclick = function () {
      const row = document.createElement('div');
      row.innerHTML = exerciseTemplate();
      const child = row.firstElementChild;
      if (child) {
        node.querySelector('.exercises-list').appendChild(child);
      }
    };
  }

  if (!preset?.exercises?.length && addExBtn) {
    addExBtn.click();
  }

  log(`Добавлен день ${idx + 1}`);
}

function fillExample() {
  const dayBuilder = $('dayBuilder');
  if (!dayBuilder) {
    log('dayBuilder not found in fillExample');
    return;
  }

  dayBuilder.innerHTML = '';

  addDay({
    title: 'Верх тела A',
    exercises: [
      { exercise_id: state.exercises[0]?.id || '', prescribed_sets: 4, prescribed_reps: '6-8', rest_seconds: 120 },
      { exercise_id: state.exercises[1]?.id || '', prescribed_sets: 4, prescribed_reps: '8-10', rest_seconds: 120 },
    ],
  });

  addDay({
    title: 'Низ тела A',
    exercises: [
      { exercise_id: state.exercises[2]?.id || '', prescribed_sets: 4, prescribed_reps: '6-8', rest_seconds: 150 },
      { exercise_id: state.exercises[3]?.id || '', prescribed_sets: 3, prescribed_reps: '8-10', rest_seconds: 120 },
    ],
  });

  log('Заполнен пример программы');
  showToast('Пример заполнен');
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
    title: $('program_title')?.value || 'Моя программа',
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
  log({ saveProgramPayload: payload });

  const data = await api(API.saveTemplate, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if ($('builderResult')) {
    $('builderResult').textContent = `Сохранено: ${data.template.title}, тренировок создано: ${data.workouts_created}`;
  }

  showToast('Программа сохранена');
  await loadTemplates();
  await loadClients();
}

async function loadTemplates() {
  try {
    state.templates = await api(API.myTemplates);
  } catch (error) {
    log(`loadTemplates error: ${String(error)}`);
    return;
  }

  const list = $('templatesList');
  if (!list) return;

  list.innerHTML =
    state.templates
      .map(
        (t) => `
          <div class="item-card">
            <strong>${t.title}</strong><br>
            <span class="muted">${t.goal} - ${t.level}</span>
          </div>
        `
      )
      .join('') || '<p class="muted">Шаблонов пока нет</p>';
}

async function loadClients() {
  try {
    const rows = await api(API.clients);
    const list = $('clientsList');
    if (!list) return;

    list.innerHTML =
      rows
        .map(
          (c) => `
            <div class="item-card">
              <strong>${c.full_name || c.telegram_user_id}</strong><br>
              <span class="muted">цель=${c.goal || '-'} | уровень=${c.level || '-'}</span>
            </div>
          `
        )
        .join('') || '<p class="muted">Клиентов пока нет</p>';
  } catch (error) {
    log(`loadClients error: ${String(error)}`);
  }
}

async function loadTodayWorkout() {
  try {
    const workout = await api(API.todayWorkout);
    const container = $('todayWorkout');
    if (!container) return;

    if (!workout) {
      container.innerHTML = '<p class="muted">На сегодня тренировка не назначена</p>';
      return;
    }

    container.innerHTML = `<p><strong>${workout.title}</strong></p>`;
  } catch (error) {
    log(`loadTodayWorkout error: ${String(error)}`);
  }
}

async function loadBilling() {
  try {
    const plans = await api(API.billingPlans);
    const sub = await api(API.billingSubscription);

    const subNode = $('subscriptionInfo');
    if (subNode) {
      subNode.textContent = sub
        ? `Активна: ${sub.plan_title} до ${new Date(sub.ends_at).toLocaleString()}`
        : 'Активной подписки нет';
    }

    const plansList = $('plansList');
    if (plansList) {
      plansList.innerHTML = (plans || [])
        .map(
          (plan) => `
            <div class="item-card">
              <strong>${plan.title}</strong><br>
              <span class="muted">${plan.price} ${plan.currency} / ${plan.period_days} дн.</span>
              <div class="toolbar wrap top-gap">
                <button data-plan="${plan.code}" class="buy-plan-btn" type="button">Купить</button>
              </div>
            </div>
          `
        )
        .join('') || '<p class="muted">Тарифов пока нет</p>';

      document.querySelectorAll('.buy-plan-btn').forEach((btn) => {
        btn.onclick = async function () {
          try {
            const planCode = this.dataset.plan;
            const checkout = await api(API.billingCheckout, {
              method: 'POST',
              body: JSON.stringify({ plan_code: planCode }),
            });

            await api(`/api/v1/billing/mock/complete/${checkout.checkout_id}`, {
              method: 'POST',
            });

            showToast('Подписка активирована');
            await loadBilling();
          } catch (error) {
            log(`buyPlan error: ${String(error)}`);
            showToast('Не удалось активировать подписку', 'error');
          }
        };
      });
    }
  } catch (error) {
    log(`loadBilling error: ${String(error)}`);
  }
}

async function loadNotifications() {
  try {
    const settings = await api(API.notificationsSettings);
    const rows = await api(API.notifications);

    if ($('notifEnabled')) $('notifEnabled').checked = Boolean(settings.workout_reminders_enabled);
    if ($('notifHour')) $('notifHour').value = settings.reminder_hour ?? 9;

    const list = $('notificationsList');
    if (list) {
      list.innerHTML =
        (rows || [])
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
  } catch (error) {
    log(`loadNotifications error: ${String(error)}`);
  }
}

async function saveNotificationSettings() {
  await api(API.notificationsSettings, {
    method: 'PATCH',
    body: JSON.stringify({
      workout_reminders_enabled: Boolean($('notifEnabled')?.checked),
      reminder_hour: Number($('notifHour')?.value || '9'),
    }),
  });

  showToast('Настройки уведомлений сохранены');
  await loadNotifications();
}

async function createExercise() {
  if (!isCoachOrAdmin()) {
    showToast('Недостаточно прав', 'error');
    return;
  }

  const payload = {
    title: $('newExerciseTitle')?.value?.trim() || '',
    primary_muscle: $('newExerciseMuscle')?.value?.trim() || '',
    equipment: $('newExerciseEquipment')?.value?.trim() || '',
  };

  if (!payload.title || !payload.primary_muscle || !payload.equipment) {
    showToast('Заполни все поля упражнения', 'error');
    return;
  }

  await api(API.exercises, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if ($('newExerciseTitle')) $('newExerciseTitle').value = '';
  if ($('newExerciseMuscle')) $('newExerciseMuscle').value = '';
  if ($('newExerciseEquipment')) $('newExerciseEquipment').value = '';

  showToast('Упражнение добавлено');
  await loadExercises();
}

async function assignDemoProgram() {
  await api(API.assignDemo, { method: 'POST' });
  showToast('Демо-программа назначена');
  await loadTodayWorkout();
}

async function bootstrap() {
  await loadMe();
  await loadExercises();
  await loadTemplates();
  await loadClients();
  await loadTodayWorkout();
  await loadBilling();
  await loadNotifications();

  if (!document.querySelector('.day-card')) {
    fillExample();
  }
}

function bindUI() {
  log('bindUI start');

  if ($('telegramLoginBtn')) {
    $('telegramLoginBtn').onclick = async function () {
      log('click telegramLoginBtn');
      try {
        await telegramLogin();
      } catch (error) {
        log(`telegramLogin button error: ${String(error)}`);
      }
    };
  }

  if ($('saveProfileBtn')) {
    $('saveProfileBtn').onclick = async function () {
      log('click saveProfileBtn');
      try {
        await saveProfile();
      } catch (error) {
        log(`saveProfile error: ${String(error)}`);
      }
    };
  }

  if ($('builder_mode')) {
    $('builder_mode').addEventListener('change', function () {
      log('change builder_mode');
      toggleCoachUI();
    });
  }

  if ($('addDayBtn')) {
    $('addDayBtn').onclick = function () {
      log('click addDayBtn');
      addDay();
    };
  }

  if ($('fillExampleBtn')) {
    $('fillExampleBtn').onclick = function () {
      log('click fillExampleBtn');
      fillExample();
    };
  }

  if ($('saveProgramBtn')) {
    $('saveProgramBtn').onclick = async function () {
      log('click saveProgramBtn');
      try {
        await saveProgram();
      } catch (error) {
        log(`saveProgramBtn error: ${String(error)}`);
        showToast('Не удалось сохранить программу', 'error');
      }
    };
  }

  if ($('reloadTemplatesBtn')) {
    $('reloadTemplatesBtn').onclick = async function () {
      log('click reloadTemplatesBtn');
      await loadTemplates();
    };
  }

  if ($('reloadClientsBtn')) {
    $('reloadClientsBtn').onclick = async function () {
      log('click reloadClientsBtn');
      await loadClients();
    };
  }

  if ($('reloadExercisesBtn')) {
    $('reloadExercisesBtn').onclick = async function () {
      log('click reloadExercisesBtn');
      await loadExercises();
    };
  }

  if ($('assignProgramBtn')) {
    $('assignProgramBtn').onclick = async function () {
      log('click assignProgramBtn');
      try {
        await assignDemoProgram();
      } catch (error) {
        log(`assignProgramBtn error: ${String(error)}`);
      }
    };
  }

  if ($('reloadBillingBtn')) {
    $('reloadBillingBtn').onclick = async function () {
      log('click reloadBillingBtn');
      await loadBilling();
    };
  }

  if ($('reloadNotificationsBtn')) {
    $('reloadNotificationsBtn').onclick = async function () {
      log('click reloadNotificationsBtn');
      await loadNotifications();
    };
  }

  if ($('saveNotifBtn')) {
    $('saveNotifBtn').onclick = async function () {
      log('click saveNotifBtn');
      try {
        await saveNotificationSettings();
      } catch (error) {
        log(`saveNotifBtn error: ${String(error)}`);
      }
    };
  }

  if ($('createExerciseBtn')) {
    $('createExerciseBtn').onclick = async function () {
      log('click createExerciseBtn');
      try {
        await createExercise();
      } catch (error) {
        log(`createExerciseBtn error: ${String(error)}`);
      }
    };
  }

  if ($('devLoginBtn')) {
    $('devLoginBtn').onclick = async function () {
      log('click devLoginBtn');
      try {
        const body = {
          telegram_user_id: Number($('debugUserId')?.value || '1001'),
          full_name: $('debugUserName')?.value || null,
          is_coach: Boolean($('debugIsCoach')?.checked),
        };

        const data = await api(API.devLogin, {
          method: 'POST',
          body: JSON.stringify(body),
        });

        localStorage.setItem(accessTokenKey, data.access_token);
        localStorage.setItem(refreshTokenKey, data.refresh_token);
        setAuthState(`Авторизован как ${body.telegram_user_id}`);
        await bootstrap();
      } catch (error) {
        log(`devLoginBtn error: ${String(error)}`);
      }
    };
  }

  log('bindUI done');
}

async function init() {
  setVersion();
  bindUI();
  renderTelegramDebug();

  try {
    await loadEnv();
  } catch (error) {
    log(`loadEnv error: ${String(error)}`);
  }

  try {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }
  } catch (error) {
    log(`Telegram ready/expand error: ${String(error)}`);
  }

  const token = localStorage.getItem(accessTokenKey);

  if (token) {
    log('found saved token, bootstrap start');
    try {
      await bootstrap();
      log('bootstrap by saved token success');
      return;
    } catch (error) {
      log(`bootstrap by saved token error: ${String(error)}`);
      localStorage.removeItem(accessTokenKey);
      localStorage.removeItem(refreshTokenKey);
    }
  }

  log('no valid saved token, tryTelegramAutoLogin');
  await tryTelegramAutoLogin();
}

document.addEventListener('DOMContentLoaded', init);