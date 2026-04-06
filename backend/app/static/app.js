const FRONTEND_VERSION = 'v12';

const accessTokenKey = 'fit_access_token';
const refreshTokenKey = 'fit_refresh_token';
const sectionStoragePrefix = 'fit_section_';

const state = {
  me: null,
  exercises: [],
  templates: [],
  todayWorkout: null,
  plans: [],
  publicConfig: null,
  workoutTimer: null,
  historyOffset: 0,
  historyLimit: 4,
  historyHasMore: true,
  editingTemplateId: null,
};

const API = {
  publicConfig: '/api/v1/public/config',
  telegramInit: '/api/v1/auth/telegram/init',
  devLogin: '/api/v1/auth/dev-login',
  me: '/api/v1/me',
  meProfile: '/api/v1/me/profile',

  exercises: '/api/v1/programs/exercises',
  createExercise: '/api/v1/programs/exercises',
  updateExercise: (exerciseId) => `/api/v1/programs/exercises/${exerciseId}`,
  deleteExercise: (exerciseId) => `/api/v1/programs/exercises/${exerciseId}`,

  saveTemplate: '/api/v1/programs/templates',
  myTemplates: '/api/v1/programs/templates/mine',
  getTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  updateTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  assignTemplateToMe: (templateId) => `/api/v1/programs/templates/${templateId}/assign-to-me`,
  deleteTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  clients: '/api/v1/programs/clients',

  todayWorkout: '/api/v1/workouts/today',
  startWorkout: (workoutId) => `/api/v1/workouts/${workoutId}/start`,
  finishWorkout: (workoutId) => `/api/v1/workouts/${workoutId}/finish`,
  updateSet: (setId) => `/api/v1/workouts/sets/${setId}`,
  workoutHistory: (offset, limit) => `/api/v1/workouts/history?offset=${offset}&limit=${limit}`,

  billingPlans: '/api/v1/billing/plans',
  billingSubscription: '/api/v1/billing/subscription',
  billingCheckout: '/api/v1/billing/checkout',
  billingMockComplete: (checkoutId) => `/api/v1/billing/mock/complete/${checkoutId}`,

  notificationsSettings: '/api/v1/notifications/settings',
  notifications: '/api/v1/notifications',
  deleteNotification: (notificationId) => `/api/v1/notifications/${notificationId}`,
};

const $ = (id) => document.getElementById(id);

function log(message) {
  const node = $('log');
  if (!node) return;
  const text = typeof message === 'string' ? message : JSON.stringify(message, null, 2);
  node.textContent = `${new Date().toLocaleTimeString()} - ${text}\n${node.textContent}`;
}

function showToast(message, type = 'success') {
  const toast = $('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast${type === 'error' ? ' error' : ''}`;
  setTimeout(() => {
    toast.className = 'toast hidden';
  }, 2500);
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

    const error = new Error(`${response.status} ${text}`);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204 || !text) {
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

function isAdmin() {
  return Boolean(state.me?.is_admin);
}

function canDeleteTemplate(template) {
  if (!state.me) return false;
  return Boolean(
    state.me.is_admin ||
    state.me.is_coach ||
    template.owner_user_id === state.me.id ||
    template.created_by_user_id === state.me.id
  );
}

function canEditSelfBuilder() {
  const mode = $('builder_mode')?.value;
  return mode === 'self' || isCoachOrAdmin();
}

function resetBuilderEditMode() {
  state.editingTemplateId = null;
  const modeInfo = $('builderModeInfo');
  const cancelBtn = $('cancelTemplateEditBtn');
  if (modeInfo) modeInfo.textContent = 'Создание нового шаблона';
  if (cancelBtn) cancelBtn.classList.add('hidden');
}

function setBuilderEditMode(templateId, title) {
  state.editingTemplateId = templateId;
  const modeInfo = $('builderModeInfo');
  const cancelBtn = $('cancelTemplateEditBtn');
  if (modeInfo) modeInfo.textContent = `Редактирование шаблона: ${title}`;
  if (cancelBtn) cancelBtn.classList.remove('hidden');
}

function toggleCoachUI() {
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

  const clientsCard = $('clientsCard');
  if (clientsCard) clientsCard.classList.toggle('hidden', !isCoachOrAdmin());

  const diagnosticCard = $('diagnosticCard');
  const logCard = $('logCard');
  if (diagnosticCard) diagnosticCard.classList.toggle('hidden', !isAdmin());
  if (logCard) logCard.classList.toggle('hidden', !isAdmin());

  const adminMeta = $('adminMeta');
  if (adminMeta) {
    adminMeta.classList.toggle('hidden', !isAdmin());
    if (isAdmin()) {
      adminMeta.textContent = `Режим администратора - frontend ${FRONTEND_VERSION}`;
    }
  }

  refreshBuilderControls();
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

function initSectionToggles() {
  document.querySelectorAll('.section-toggle').forEach((button) => {
    const targetId = button.dataset.target;
    const body = document.getElementById(targetId);
    if (!body) return;

    const storageKey = `${sectionStoragePrefix}${targetId}`;
    const savedState = localStorage.getItem(storageKey);

    if (savedState === 'collapsed') {
      body.classList.add('hidden');
      button.textContent = 'Развернуть';
    } else {
      body.classList.remove('hidden');
      button.textContent = 'Свернуть';
    }

    button.onclick = () => {
      const collapsed = !body.classList.contains('hidden');
      body.classList.toggle('hidden', collapsed);
      button.textContent = collapsed ? 'Развернуть' : 'Свернуть';
      localStorage.setItem(storageKey, collapsed ? 'collapsed' : 'expanded');
    };
  });
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

async function devLogin() {
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

  setAuthState(`Dev-вход выполнен: ${body.telegram_user_id}`);
  showToast('Dev-вход выполнен');
  await bootstrap();
}

async function telegramLogin() {
  const tg = window.Telegram?.WebApp;
  const initData = tg?.initData;

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
              ${ex.is_custom ? '<span class="metric-pill">Личное</span>' : '<span class="metric-pill">Общее</span>'}
              ${ex.is_personalized ? '<span class="metric-pill">Моё изменение</span>' : ''}
            </div>
            <div class="toolbar wrap top-gap">
              <button class="secondary edit-exercise-btn" type="button" data-exercise-id="${ex.edit_target_id}">
                Редактировать
              </button>
              <button class="secondary delete-exercise-btn" type="button" data-exercise-id="${ex.edit_target_id}">
                Удалить
              </button>
            </div>
          </div>
        `
      )
      .join('') || '<p class="muted">Упражнений пока нет</p>';

  document.querySelectorAll('.edit-exercise-btn').forEach((btn) => {
    btn.onclick = async () => {
      const exerciseId = Number(btn.dataset.exerciseId);
      const exercise = state.exercises.find((item) => item.edit_target_id === exerciseId);
      if (!exercise) return;

      const title = prompt('Название упражнения', exercise.title);
      if (title === null) return;

      const primaryMuscle = prompt('Основная мышечная группа', exercise.primary_muscle);
      if (primaryMuscle === null) return;

      const equipment = prompt('Оборудование', exercise.equipment);
      if (equipment === null) return;

      try {
        await api(API.updateExercise(exerciseId), {
          method: 'PATCH',
          body: JSON.stringify({
            title,
            primary_muscle: primaryMuscle,
            equipment,
          }),
        });
        showToast('Упражнение обновлено');
        await loadExercises();
        await loadTemplates();
        await loadTodayWorkout();
      } catch (error) {
        log(`editExercise: ${String(error)}`);
        showToast('Не удалось обновить упражнение', 'error');
      }
    };
  });

  document.querySelectorAll('.delete-exercise-btn').forEach((btn) => {
    btn.onclick = async () => {
      const exerciseId = Number(btn.dataset.exerciseId);
      if (!confirm('Удалить упражнение только у тебя?')) return;

      try {
        await api(API.deleteExercise(exerciseId), {
          method: 'DELETE',
        });
        showToast('Упражнение скрыто/удалено для текущего пользователя');
        await loadExercises();
        await loadTemplates();
        await loadTodayWorkout();
      } catch (error) {
        log(`deleteExercise: ${String(error)}`);
        showToast('Не удалось удалить упражнение', 'error');
      }
    };
  });
}

async function createExercise() {
  const payload = {
    title: $('newExerciseTitle')?.value?.trim() || '',
    primary_muscle: $('newExerciseMuscle')?.value?.trim() || '',
    equipment: $('newExerciseEquipment')?.value?.trim() || '',
  };

  if (!payload.title || !payload.primary_muscle || !payload.equipment) {
    showToast('Заполни все поля упражнения', 'error');
    return;
  }

  const exercise = await api(API.createExercise, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  $('newExerciseTitle').value = '';
  $('newExerciseMuscle').value = '';
  $('newExerciseEquipment').value = '';

  showToast(`Упражнение "${exercise.title}" добавлено`);
  await loadExercises();
}

function exerciseTemplate(defaultExerciseId = '', preset = null) {
  const options = state.exercises
    .map(
      (ex) => `<option value="${ex.id}" ${String(ex.id) === String(defaultExerciseId) ? 'selected' : ''}>${ex.title}</option>`
    )
    .join('');

  return `
    <div class="grid item-card program-ex-row" style="grid-template-columns:2fr 1fr 1fr 1fr auto;">
      <select class="exercise-id">${options}</select>
      <input class="exercise-sets" type="number" min="1" value="${preset?.prescribed_sets || 3}" placeholder="Подходы" />
      <input class="exercise-reps" type="text" value="${preset?.prescribed_reps || '8-10'}" placeholder="Повторы" />
      <input class="exercise-rest" type="number" min="15" value="${preset?.rest_seconds || 90}" placeholder="Отдых, сек" />
      <button class="secondary remove-ex-btn" type="button">Удалить</button>
    </div>
  `;
}

function programDayTemplate(index, preset = null) {
  return `
    <div class="item-card day-card" data-day-index="${index}">
      <div class="toolbar wrap">
        <input class="day-title" type="text" placeholder="Название дня" value="${preset?.title || `День ${index + 1}`}" />
        <button class="secondary add-ex-btn" type="button">+ Упражнение</button>
        <button class="secondary remove-day-btn" type="button">Удалить день</button>
      </div>
      <div class="stack exercises-list">
        ${(preset?.exercises || []).map((ex) => exerciseTemplate(ex.exercise_id, ex)).join('')}
      </div>
    </div>
  `;
}

function bindExerciseRowActions(row) {
  const removeBtn = row.querySelector('.remove-ex-btn');
  if (!removeBtn) return;

  removeBtn.onclick = () => {
    if (!canEditSelfBuilder()) {
      showToast('Удаление элементов доступно только для своей программы, тренеру или админу', 'error');
      return;
    }
    row.remove();
  };
}

function refreshBuilderControls() {
  document.querySelectorAll('.remove-day-btn').forEach((btn) => {
    btn.disabled = !canEditSelfBuilder();
  });

  document.querySelectorAll('.remove-ex-btn').forEach((btn) => {
    btn.disabled = !canEditSelfBuilder();
  });
}

function addDay(preset = null) {
  const dayBuilder = $('dayBuilder');
  if (!dayBuilder) return;

  const idx = dayBuilder.querySelectorAll('.day-card').length;
  const wrapper = document.createElement('div');
  wrapper.innerHTML = programDayTemplate(idx, preset);
  const node = wrapper.firstElementChild;

  dayBuilder.appendChild(node);

  const exercisesList = node.querySelector('.exercises-list');
  const addExBtn = node.querySelector('.add-ex-btn');
  const removeDayBtn = node.querySelector('.remove-day-btn');

  addExBtn.onclick = () => {
    const rowWrapper = document.createElement('div');
    rowWrapper.innerHTML = exerciseTemplate();
    const row = rowWrapper.firstElementChild;
    exercisesList.appendChild(row);
    bindExerciseRowActions(row);
    refreshBuilderControls();
  };

  removeDayBtn.onclick = () => {
    if (!canEditSelfBuilder()) {
      showToast('Удаление дней доступно только для своей программы, тренеру или админу', 'error');
      return;
    }
    node.remove();
    renumberDays();
  };

  node.querySelectorAll('.program-ex-row').forEach(bindExerciseRowActions);

  if (!preset?.exercises?.length) {
    addExBtn.click();
  }

  refreshBuilderControls();
}

function renumberDays() {
  document.querySelectorAll('.day-card').forEach((card, index) => {
    card.dataset.dayIndex = String(index);
    const titleInput = card.querySelector('.day-title');
    if (titleInput && !titleInput.value.trim()) {
      titleInput.value = `День ${index + 1}`;
    }
  });
}

function fillExample() {
  const dayBuilder = $('dayBuilder');
  if (!dayBuilder) return;

  if (!state.exercises.length) {
    showToast('Сначала должны загрузиться упражнения', 'error');
    return;
  }

  dayBuilder.innerHTML = '';

  addDay({
    title: 'Верх тела A',
    exercises: [
      { exercise_id: state.exercises[0]?.id || '', prescribed_sets: 4, prescribed_reps: '6-8', rest_seconds: 120 },
      { exercise_id: state.exercises[1]?.id || state.exercises[0]?.id || '', prescribed_sets: 4, prescribed_reps: '8-10', rest_seconds: 120 },
    ],
  });

  addDay({
    title: 'Низ тела A',
    exercises: [
      { exercise_id: state.exercises[2]?.id || state.exercises[0]?.id || '', prescribed_sets: 4, prescribed_reps: '6-8', rest_seconds: 150 },
      { exercise_id: state.exercises[3]?.id || state.exercises[1]?.id || '', prescribed_sets: 3, prescribed_reps: '8-10', rest_seconds: 120 },
    ],
  });

  showToast('Пример программы заполнен');
}

function collectProgramPayload() {
  const days = [...document.querySelectorAll('.day-card')].map((day) => ({
    title: day.querySelector('.day-title')?.value?.trim() || 'День',
    exercises: [...day.querySelectorAll('.program-ex-row')].map((row) => ({
      exercise_id: Number(row.querySelector('.exercise-id')?.value),
      prescribed_sets: Number(row.querySelector('.exercise-sets')?.value),
      prescribed_reps: row.querySelector('.exercise-reps')?.value?.trim() || '8-10',
      rest_seconds: Number(row.querySelector('.exercise-rest')?.value),
      notes: null,
    })),
  }));

  return {
    title: $('program_title')?.value?.trim() || 'Моя программа',
    goal: $('program_goal')?.value,
    level: $('program_level')?.value,
    mode: $('builder_mode')?.value,
    target_telegram_user_id: $('target_telegram_user_id')?.value
      ? Number($('target_telegram_user_id').value)
      : null,
    target_full_name: $('target_full_name')?.value?.trim() || null,
    days,
    assign_after_create: true,
  };
}

async function saveProgram() {
  const payload = collectProgramPayload();

  if (!payload.days.length) {
    showToast('Добавь хотя бы один день программы', 'error');
    return;
  }

  for (const day of payload.days) {
    if (!day.exercises.length) {
      showToast('В каждом дне должно быть хотя бы одно упражнение', 'error');
      return;
    }
  }

  const isEditing = Boolean(state.editingTemplateId);
  const url = isEditing ? API.updateTemplate(state.editingTemplateId) : API.saveTemplate;
  const method = isEditing ? 'PATCH' : 'POST';

  const data = await api(url, {
    method,
    body: JSON.stringify(payload),
  });

  if ($('builderResult')) {
    const templateTitle = data.template?.title || payload.title;
    $('builderResult').textContent = isEditing
      ? `Шаблон обновлён: ${templateTitle}`
      : `Сохранено: ${templateTitle}, тренировок создано: ${data.workouts_created}`;
  }

  showToast(isEditing ? 'Шаблон обновлён' : 'Программа сохранена');
  resetBuilderEditMode();
  await loadTemplates();
  await loadClients();
  await loadTodayWorkout();
  await resetHistoryAndReload();
  await loadNotifications();
}

async function loadTemplateIntoBuilder(templateId) {
  const template = await api(API.getTemplate(templateId));

  $('program_title').value = template.title || '';
  $('program_goal').value = template.goal || 'muscle_gain';
  $('program_level').value = template.level || 'intermediate';
  $('builder_mode').value = template.owner_user_id ? 'self' : 'coach';

  const dayBuilder = $('dayBuilder');
  dayBuilder.innerHTML = '';

  (template.days || []).forEach((day) => {
    addDay({
      title: day.title,
      exercises: (day.exercises || []).map((ex) => ({
        exercise_id: ex.exercise_id,
        prescribed_sets: ex.prescribed_sets,
        prescribed_reps: ex.prescribed_reps,
        rest_seconds: ex.rest_seconds,
      })),
    });
  });

  toggleCoachUI();
  setBuilderEditMode(template.id, template.title);
  showToast('Шаблон загружен в конструктор');
}

async function assignTemplateToMe(templateId) {
  await api(API.assignTemplateToMe(templateId), {
    method: 'POST',
  });
  showToast('Шаблон загружен в тренировки');
  await loadTodayWorkout();
  await resetHistoryAndReload();
  await loadNotifications();
}

async function deleteTemplate(templateId) {
  await api(API.deleteTemplate(templateId), {
    method: 'DELETE',
  });
  showToast('Шаблон удалён');
  await loadTemplates();
}

async function loadTemplates() {
  state.templates = await api(API.myTemplates);
  const list = $('templatesList');
  if (!list) return;

  list.innerHTML =
    state.templates
      .map((template) => {
        const deleteBtn = canDeleteTemplate(template)
          ? `<button class="secondary delete-template-btn" type="button" data-template-id="${template.id}">Удалить</button>`
          : '';

        const editBtn = canDeleteTemplate(template)
          ? `<button class="secondary edit-template-btn" type="button" data-template-id="${template.id}">Редактировать</button>`
          : '';

        const assignBtn = `<button class="secondary assign-template-btn" type="button" data-template-id="${template.id}">В тренировки</button>`;

        return `
          <div class="item-card">
            <strong>${template.title}</strong><br>
            <span class="muted">${template.goal} - ${template.level}</span>
            <div class="top-gap">
              ${
                template.days?.length
                  ? template.days
                      .map(
                        (day) => `
                          <div class="top-gap">
                            <strong>${day.title}</strong>
                            <div class="muted">${(day.exercises || []).map((ex) => ex.exercise_title).join(', ')}</div>
                          </div>
                        `
                      )
                      .join('')
                  : '<div class="muted top-gap">Дней пока нет</div>'
              }
            </div>
            <div class="toolbar wrap top-gap">
              ${assignBtn}
              ${editBtn}
              ${deleteBtn}
            </div>
          </div>
        `;
      })
      .join('') || '<p class="muted">Шаблонов пока нет</p>';

  document.querySelectorAll('.assign-template-btn').forEach((btn) => {
    btn.onclick = async () => {
      try {
        await assignTemplateToMe(Number(btn.dataset.templateId));
      } catch (error) {
        log(`assignTemplateToMe: ${String(error)}`);
        showToast('Не удалось загрузить шаблон в тренировки', 'error');
      }
    };
  });

  document.querySelectorAll('.edit-template-btn').forEach((btn) => {
    btn.onclick = async () => {
      try {
        await loadTemplateIntoBuilder(Number(btn.dataset.templateId));
      } catch (error) {
        log(`loadTemplateIntoBuilder: ${String(error)}`);
        showToast('Не удалось загрузить шаблон в конструктор', 'error');
      }
    };
  });

  document.querySelectorAll('.delete-template-btn').forEach((btn) => {
    btn.onclick = async () => {
      if (!confirm('Удалить шаблон?')) return;
      try {
        await deleteTemplate(Number(btn.dataset.templateId));
      } catch (error) {
        log(`deleteTemplate: ${String(error)}`);
        showToast('Не удалось удалить шаблон', 'error');
      }
    };
  });
}

async function loadClients() {
  const card = $('clientsCard');
  if (card) card.classList.toggle('hidden', !isCoachOrAdmin());

  if (!isCoachOrAdmin()) return;

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
}

function statusLabel(status) {
  return ({
    planned: 'Запланирована',
    in_progress: 'В процессе',
    completed: 'Завершена',
  }[status] || status);
}

function clearWorkoutTimer() {
  if (state.workoutTimer) {
    clearInterval(state.workoutTimer);
    state.workoutTimer = null;
  }
}

function formatDurationMs(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) {
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function startWorkoutTimer(startedAtIso) {
  clearWorkoutTimer();
  const timerNode = $('workoutTimer');
  if (!timerNode || !startedAtIso) return;

  const startedAt = new Date(startedAtIso).getTime();

  const render = () => {
    timerNode.textContent = `Длительность тренировки: ${formatDurationMs(Date.now() - startedAt)}`;
  };

  render();
  state.workoutTimer = setInterval(render, 1000);
}

async function updateSetRow(setId, payload) {
  await api(API.updateSet(setId), {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

function renderTodayWorkout(workout) {
  const container = $('todayWorkout');
  if (!container) return;

  if (!workout) {
    container.innerHTML = '<p class="muted">На сегодня тренировка не назначена</p>';
    clearWorkoutTimer();
    return;
  }

  const actionButtons =
    workout.status === 'planned'
      ? `<button id="startWorkoutBtn" type="button">Начать тренировку</button>`
      : workout.status === 'in_progress'
        ? `<button id="finishWorkoutBtn" type="button">Завершить тренировку</button>`
        : '';

  container.innerHTML = `
    <div class="item-card">
      <strong>${workout.title}</strong><br>
      <span class="muted">Статус: ${statusLabel(workout.status)}</span>
      <div id="workoutTimer" class="top-gap muted"></div>
      <div class="toolbar wrap top-gap">
        ${actionButtons}
      </div>
    </div>

    <div class="stack top-gap">
      ${(workout.exercises || []).map((exercise) => `
        <div class="item-card">
          <strong>${exercise.exercise_title}</strong>
          <div class="muted top-gap">
            План: ${exercise.prescribed_sets} x ${exercise.prescribed_reps}, отдых ${exercise.rest_seconds} сек
          </div>

          <div class="stack top-gap">
            ${(exercise.sets || []).map((setRow) => `
              <div class="grid item-card" style="grid-template-columns: 1fr 1fr 1fr auto;">
                <div>Подход ${setRow.set_number}</div>
                <input
                  class="set-reps"
                  type="number"
                  min="0"
                  value="${setRow.actual_reps ?? ''}"
                  data-set-id="${setRow.id}"
                  placeholder="Повторы"
                />
                <input
                  class="set-weight"
                  type="number"
                  min="0"
                  step="0.1"
                  value="${setRow.actual_weight ?? ''}"
                  data-set-id="${setRow.id}"
                  placeholder="Вес"
                />
                <label class="checkbox-row">
                  <input
                    class="set-completed"
                    type="checkbox"
                    data-set-id="${setRow.id}"
                    ${setRow.is_completed ? 'checked' : ''}
                  />
                  <span>Готово</span>
                </label>
              </div>
            `).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `;

  if (workout.status === 'in_progress' && workout.started_at) {
    startWorkoutTimer(workout.started_at);
  } else if (workout.status === 'completed' && workout.started_at && workout.completed_at) {
    clearWorkoutTimer();
    const timerNode = $('workoutTimer');
    if (timerNode) {
      timerNode.textContent = `Длительность тренировки: ${formatDurationMs(new Date(workout.completed_at).getTime() - new Date(workout.started_at).getTime())}`;
    }
  } else {
    clearWorkoutTimer();
  }

  const startBtn = $('startWorkoutBtn');
  if (startBtn) {
    startBtn.onclick = async () => {
      try {
        state.todayWorkout = await api(API.startWorkout(workout.id), { method: 'POST' });
        showToast('Тренировка начата');
        renderTodayWorkout(state.todayWorkout);
        resetHistoryAndReload();
      } catch (error) {
        log(`startWorkout: ${String(error)}`);
        showToast('Не удалось начать тренировку', 'error');
      }
    };
  }

  const finishBtn = $('finishWorkoutBtn');
  if (finishBtn) {
    finishBtn.onclick = async () => {
      try {
        state.todayWorkout = await api(API.finishWorkout(workout.id), { method: 'POST' });
        showToast('Тренировка завершена');
        renderTodayWorkout(state.todayWorkout);
        resetHistoryAndReload();
      } catch (error) {
        log(`finishWorkout: ${String(error)}`);
        showToast('Не удалось завершить тренировку', 'error');
      }
    };
  }

  document.querySelectorAll('.set-reps').forEach((input) => {
    input.addEventListener('change', async () => {
      const setId = Number(input.dataset.setId);
      const weightInput = document.querySelector(`.set-weight[data-set-id="${setId}"]`);
      const completedInput = document.querySelector(`.set-completed[data-set-id="${setId}"]`);

      try {
        await updateSetRow(setId, {
          actual_reps: input.value ? Number(input.value) : null,
          actual_weight: weightInput?.value ? Number(weightInput.value) : null,
          is_completed: Boolean(completedInput?.checked),
        });
      } catch (error) {
        log(`update set reps: ${String(error)}`);
      }
    });
  });

  document.querySelectorAll('.set-weight').forEach((input) => {
    input.addEventListener('change', async () => {
      const setId = Number(input.dataset.setId);
      const repsInput = document.querySelector(`.set-reps[data-set-id="${setId}"]`);
      const completedInput = document.querySelector(`.set-completed[data-set-id="${setId}"]`);

      try {
        await updateSetRow(setId, {
          actual_reps: repsInput?.value ? Number(repsInput.value) : null,
          actual_weight: input.value ? Number(input.value) : null,
          is_completed: Boolean(completedInput?.checked),
        });
      } catch (error) {
        log(`update set weight: ${String(error)}`);
      }
    });
  });

  document.querySelectorAll('.set-completed').forEach((input) => {
    input.addEventListener('change', async () => {
      const setId = Number(input.dataset.setId);
      const repsInput = document.querySelector(`.set-reps[data-set-id="${setId}"]`);
      const weightInput = document.querySelector(`.set-weight[data-set-id="${setId}"]`);

      try {
        await updateSetRow(setId, {
          actual_reps: repsInput?.value ? Number(repsInput.value) : null,
          actual_weight: weightInput?.value ? Number(weightInput.value) : null,
          is_completed: input.checked,
        });
        showToast('Подход сохранён');
      } catch (error) {
        log(`update set completed: ${String(error)}`);
        showToast('Не удалось сохранить подход', 'error');
      }
    });
  });
}

async function loadTodayWorkout() {
  try {
    state.todayWorkout = await api(API.todayWorkout);
    renderTodayWorkout(state.todayWorkout);
  } catch (error) {
    if (error.status === 404) {
      state.todayWorkout = null;
      renderTodayWorkout(null);
      return;
    }

    log(`loadTodayWorkout: ${String(error)}`);
    renderTodayWorkout(null);
  }
}

function renderWorkoutHistoryRows(rows, append = false) {
  const container = $('workoutHistory');
  if (!container) return;

  if (!append) {
    container.innerHTML = '';
  }

  if (!rows.length && !append) {
    container.innerHTML = '<p class="muted">История тренировок пока пустая</p>';
    return;
  }

  const html = rows
    .map((item) => `
      <div class="item-card">
        <strong>${item.title}</strong><br>
        <span class="muted">${item.scheduled_date} - ${statusLabel(item.status)}</span>
      </div>
    `)
    .join('');

  container.insertAdjacentHTML('beforeend', html);
}

function updateHistoryLoadMoreVisibility() {
  const btn = $('loadMoreHistoryBtn');
  if (!btn) return;
  btn.classList.toggle('hidden', !state.historyHasMore);
}

async function loadWorkoutHistory(append = false) {
  const offset = append ? state.historyOffset : 0;
  const rows = await api(API.workoutHistory(offset, state.historyLimit));

  if (!append) {
    state.historyOffset = 0;
  }

  renderWorkoutHistoryRows(rows, append);

  state.historyOffset = offset + rows.length;
  state.historyHasMore = rows.length === state.historyLimit;
  updateHistoryLoadMoreVisibility();
}

async function resetHistoryAndReload() {
  state.historyOffset = 0;
  state.historyHasMore = true;
  await loadWorkoutHistory(false);
}

async function loadBilling() {
  try {
    state.plans = await api(API.billingPlans);
    const subscription = await api(API.billingSubscription);

    if ($('subscriptionInfo')) {
      $('subscriptionInfo').textContent = subscription
        ? `Активна: ${subscription.plan_title} до ${new Date(subscription.ends_at).toLocaleString()}`
        : 'Активной подписки нет';
    }

    const plansList = $('plansList');
    if (!plansList) return;

    plansList.innerHTML =
      state.plans
        .map(
          (plan) => `
            <div class="item-card">
              <strong>${plan.title}</strong><br>
              <span class="muted">${plan.price} ${plan.currency} / ${plan.period_days} дн.</span>
              <div class="toolbar wrap top-gap">
                <button class="secondary buy-plan-btn" data-plan="${plan.code}" type="button">Купить</button>
              </div>
            </div>
          `
        )
        .join('') || '<p class="muted">Тарифов пока нет</p>';

    document.querySelectorAll('.buy-plan-btn').forEach((btn) => {
      btn.onclick = async () => {
        try {
          const checkout = await api(API.billingCheckout, {
            method: 'POST',
            body: JSON.stringify({ plan_code: btn.dataset.plan }),
          });

          if (checkout?.checkout_id) {
            await api(API.billingMockComplete(checkout.checkout_id), { method: 'POST' });
            showToast('Подписка активирована');
            await loadBilling();
          }
        } catch (error) {
          log(`buyPlan: ${String(error)}`);
          showToast('Не удалось оформить подписку', 'error');
        }
      };
    });
  } catch (error) {
    log(`loadBilling: ${String(error)}`);
  }
}

async function createManualNotification() {
  const title = $('manualNotifTitle')?.value?.trim() || '';
  const body = $('manualNotifBody')?.value?.trim() || '';
  const dateTime = $('manualNotifDateTime')?.value || '';

  if (!title || !body || !dateTime) {
    showToast('Заполни заголовок, текст и дату/время', 'error');
    return;
  }

  await api(API.notifications, {
    method: 'POST',
    body: JSON.stringify({
      title,
      body,
      scheduled_for: new Date(dateTime).toISOString(),
    }),
  });

  $('manualNotifTitle').value = '';
  $('manualNotifBody').value = '';
  $('manualNotifDateTime').value = '';

  showToast('Напоминание создано');
  await loadNotifications();
}

async function deleteNotification(notificationId) {
  await api(API.deleteNotification(notificationId), {
    method: 'DELETE',
  });
  showToast('Напоминание удалено');
  await loadNotifications();
}

async function loadNotifications() {
  try {
    const settings = await api(API.notificationsSettings);
    const rows = await api(API.notifications);

    if ($('notifEnabled')) $('notifEnabled').checked = Boolean(settings.workout_reminders_enabled);
    if ($('notifHour')) $('notifHour').value = settings.reminder_hour ?? 9;

    const list = $('notificationsList');
    if (!list) return;

    list.innerHTML =
      (rows || [])
        .map(
          (n) => `
            <div class="item-card">
              <strong>${n.title}</strong><br>
              <span class="muted">${new Date(n.scheduled_for).toLocaleString()} - ${n.status}</span>
              <div class="top-gap">${n.body}</div>
              <div class="toolbar wrap top-gap">
                <button class="secondary delete-notification-btn" type="button" data-notification-id="${n.id}">
                  Удалить напоминание
                </button>
              </div>
            </div>
          `
        )
        .join('') || '<p class="muted">Нет напоминаний</p>';

    document.querySelectorAll('.delete-notification-btn').forEach((btn) => {
      btn.onclick = async () => {
        if (!confirm('Удалить напоминание?')) return;

        try {
          await deleteNotification(Number(btn.dataset.notificationId));
        } catch (error) {
          log(`deleteNotification: ${String(error)}`);
          showToast('Не удалось удалить напоминание', 'error');
        }
      };
    });
  } catch (error) {
    log(`loadNotifications: ${String(error)}`);
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

  showToast('Настройки авто-напоминаний сохранены');
  await loadNotifications();
}

async function bootstrap() {
  await loadMe();
  await loadExercises();
  await loadTemplates();
  await loadClients();
  await loadTodayWorkout();
  await resetHistoryAndReload();
  await loadBilling();
  await loadNotifications();

  if (!document.querySelector('.day-card')) {
    fillExample();
  }
}

function bindUI() {
  if ($('telegramLoginBtn')) {
    $('telegramLoginBtn').onclick = async () => {
      try {
        await telegramLogin();
      } catch (error) {
        log(`telegramLogin button: ${String(error)}`);
      }
    };
  }

  if ($('devLoginBtn')) {
    $('devLoginBtn').onclick = async () => {
      try {
        await devLogin();
      } catch (error) {
        log(`devLogin: ${String(error)}`);
        showToast('Не удалось выполнить dev-вход', 'error');
      }
    };
  }

  if ($('saveProfileBtn')) {
    $('saveProfileBtn').onclick = async () => {
      try {
        await saveProfile();
      } catch (error) {
        log(`saveProfile: ${String(error)}`);
        showToast('Не удалось сохранить профиль', 'error');
      }
    };
  }

  if ($('builder_mode')) {
    $('builder_mode').addEventListener('change', toggleCoachUI);
  }

  if ($('addDayBtn')) {
    $('addDayBtn').onclick = () => addDay();
  }

  if ($('fillExampleBtn')) {
    $('fillExampleBtn').onclick = () => fillExample();
  }

  if ($('saveProgramBtn')) {
    $('saveProgramBtn').onclick = async () => {
      try {
        await saveProgram();
      } catch (error) {
        log(`saveProgramBtn: ${String(error)}`);
        showToast('Не удалось сохранить программу', 'error');
      }
    };
  }

  if ($('cancelTemplateEditBtn')) {
    $('cancelTemplateEditBtn').onclick = () => {
      resetBuilderEditMode();
      $('builderResult').textContent = '';
    };
  }

  if ($('reloadTemplatesBtn')) {
    $('reloadTemplatesBtn').onclick = async () => {
      try {
        await loadTemplates();
      } catch (error) {
        log(`reloadTemplates: ${String(error)}`);
      }
    };
  }

  if ($('reloadClientsBtn')) {
    $('reloadClientsBtn').onclick = async () => {
      try {
        await loadClients();
      } catch (error) {
        log(`reloadClients: ${String(error)}`);
      }
    };
  }

  if ($('reloadExercisesBtn')) {
    $('reloadExercisesBtn').onclick = async () => {
      try {
        await loadExercises();
      } catch (error) {
        log(`reloadExercises: ${String(error)}`);
      }
    };
  }

  if ($('createExerciseBtn')) {
    $('createExerciseBtn').onclick = async () => {
      try {
        await createExercise();
      } catch (error) {
        log(`createExerciseBtn: ${String(error)}`);
        showToast('Не удалось добавить упражнение', 'error');
      }
    };
  }

  if ($('reloadBillingBtn')) {
    $('reloadBillingBtn').onclick = async () => {
      try {
        await loadBilling();
      } catch (error) {
        log(`reloadBillingBtn: ${String(error)}`);
      }
    };
  }

  if ($('reloadNotificationsBtn')) {
    $('reloadNotificationsBtn').onclick = async () => {
      try {
        await loadNotifications();
      } catch (error) {
        log(`reloadNotificationsBtn: ${String(error)}`);
      }
    };
  }

  if ($('saveNotifBtn')) {
    $('saveNotifBtn').onclick = async () => {
      try {
        await saveNotificationSettings();
      } catch (error) {
        log(`saveNotifBtn: ${String(error)}`);
        showToast('Не удалось сохранить настройки уведомлений', 'error');
      }
    };
  }

  if ($('createNotificationBtn')) {
    $('createNotificationBtn').onclick = async () => {
      try {
        await createManualNotification();
      } catch (error) {
        log(`createNotificationBtn: ${String(error)}`);
        showToast('Не удалось создать напоминание', 'error');
      }
    };
  }

  if ($('loadMoreHistoryBtn')) {
    $('loadMoreHistoryBtn').onclick = async () => {
      try {
        await loadWorkoutHistory(true);
      } catch (error) {
        log(`loadMoreHistoryBtn: ${String(error)}`);
        showToast('Не удалось загрузить ещё историю', 'error');
      }
    };
  }
}

async function init() {
  bindUI();
  initSectionToggles();
  renderTelegramDebug();

  try {
    await loadEnv();
  } catch (error) {
    log(`loadEnv: ${String(error)}`);
  }

  try {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
    }
  } catch (error) {
    log(`Telegram ready/expand: ${String(error)}`);
  }

  const token = localStorage.getItem(accessTokenKey);

  if (token) {
    try {
      await bootstrap();
      return;
    } catch (error) {
      log(`bootstrap by saved token: ${String(error)}`);
      localStorage.removeItem(accessTokenKey);
      localStorage.removeItem(refreshTokenKey);
    }
  }

  await tryTelegramAutoLogin();
}

document.addEventListener('DOMContentLoaded', init);