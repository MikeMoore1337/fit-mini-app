import { API, accessTokenKey, refreshTokenKey, sectionStoragePrefix } from './core/config.js';
import { state } from './core/state.js';
import {
  $,
  log,
  showToast,
  toastError,
  setAppLoading,
  openConfirmDialog,
  bindGlobalNavHandlers,
  expandSectionAndScroll,
} from './core/ui.js';
import { api, clearTokens, sleep } from './core/http.js';

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

function getRoleLabel(user) {
  if (user?.is_admin) return 'Администратор';
  if (user?.is_coach) return 'Тренер';
  return 'Клиент';
}

const builderCoachOptionLabel = 'Для клиента';

const devRolePresets = {
  user: {
    telegram_user_id: 2001,
    full_name: 'Клиент Demo',
  },
  coach: {
    telegram_user_id: 1002,
    full_name: 'Тренер Demo',
  },
  admin: {
    telegram_user_id: 1001,
    full_name: 'Админ Demo',
  },
};

function getUserDisplayName(user) {
  const profile = user?.profile || {};
  return profile.full_name || user?.first_name || user?.username || user?.telegram_user_id || '';
}

function getDevRoleFlags(role) {
  return {
    is_coach: role === 'coach' || role === 'admin',
    is_admin: role === 'admin',
  };
}

function setDevRole(role) {
  const normalizedRole = devRolePresets[role] ? role : 'user';
  const roleInput = $('debugRole');

  if (roleInput) roleInput.value = normalizedRole;

  document.querySelectorAll('[data-dev-role-option]').forEach((button) => {
    button.classList.toggle('is-active', button.dataset.devRoleOption === normalizedRole);
  });
}

function fillDevPreset(role) {
  const normalizedRole = devRolePresets[role] ? role : 'user';
  const preset = devRolePresets[normalizedRole];

  if ($('debugUserId')) $('debugUserId').value = String(preset.telegram_user_id);
  if ($('debugUserName')) $('debugUserName').value = preset.full_name;

  setDevRole(normalizedRole);
}

function renderCurrentAccess(user) {
  const summary = $('authSummary');
  const userLabel = $('authUserLabel');
  const roleLabel = $('authRoleLabel');
  const roleBadge = $('currentRoleBadge');

  if (!user) {
    if (summary) summary.classList.add('hidden');
    if (roleBadge) roleBadge.classList.add('hidden');
    return;
  }

  const displayName = getUserDisplayName(user);
  const role = getRoleLabel(user);

  if (userLabel) userLabel.textContent = displayName;
  if (roleLabel) roleLabel.textContent = role;
  if (summary) summary.classList.remove('hidden');

  if (roleBadge) {
    roleBadge.textContent = role;
    roleBadge.classList.remove('hidden');
  }
}

function escapeHtml(value) {
  const text = value == null ? '' : String(value);
  const replacements = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (char) => replacements[char]);
}

function canDeleteTemplate(template) {
  if (!state.me) return false;
  return Boolean(
    state.me.is_admin ||
      template.owner_user_id === state.me.id ||
      template.created_by_user_id === state.me.id
  );
}

function getEffectiveBuilderMode() {
  const requestedMode = $('builder_mode')?.value || 'self';
  return requestedMode === 'coach' && isCoachOrAdmin() ? 'coach' : 'self';
}

function canEditSelfBuilder() {
  return getEffectiveBuilderMode() === 'self' || isCoachOrAdmin();
}

function syncBuilderModeOptions(canAssignClients) {
  const builderMode = $('builder_mode');
  if (!builderMode) return;

  let coachOption = [...builderMode.options].find((option) => option.value === 'coach');

  if (canAssignClients && !coachOption) {
    coachOption = document.createElement('option');
    coachOption.value = 'coach';
    coachOption.textContent = builderCoachOptionLabel;
    builderMode.appendChild(coachOption);
  }

  if (!canAssignClients && coachOption) {
    coachOption.remove();
  }

  if (!canAssignClients) {
    builderMode.value = 'self';
  }
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
  if (adminLink) adminLink.classList.toggle('hidden', !isAdmin());

  const coachFields = $('coachFields');
  const builderMode = $('builder_mode');
  const canAssignClients = isCoachOrAdmin();

  syncBuilderModeOptions(canAssignClients);

  if (coachFields && builderMode) {
    const showCoachFields = builderMode.value === 'coach' && canAssignClients;
    coachFields.classList.toggle('hidden', !showCoachFields);

    if (!showCoachFields) {
      if ($('target_telegram_user_id')) $('target_telegram_user_id').value = '';
      if ($('target_full_name')) $('target_full_name').value = '';
    }
  }

  const clientsCard = $('clientsCard');
  if (clientsCard) clientsCard.classList.toggle('hidden', !isCoachOrAdmin());

  const diagnosticCard = $('diagnosticCard');
  const logCard = $('logCard');
  if (diagnosticCard) diagnosticCard.classList.toggle('hidden', !isAdmin());
  if (logCard) logCard.classList.toggle('hidden', !isAdmin());

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

function getWorkoutTimerStorageKey(workoutId) {
  return `fit_workout_timer_started_${workoutId}`;
}

function saveWorkoutTimerStart(workoutId, startedAtMs) {
  localStorage.setItem(getWorkoutTimerStorageKey(workoutId), String(startedAtMs));
}

function loadWorkoutTimerStart(workoutId) {
  const raw = localStorage.getItem(getWorkoutTimerStorageKey(workoutId));
  if (!raw) return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function clearWorkoutTimerStart(workoutId) {
  localStorage.removeItem(getWorkoutTimerStorageKey(workoutId));
}

async function waitForTelegramInitData(timeoutMs = 4000) {
  const startedAt = Date.now();

  while (Date.now() - startedAt < timeoutMs) {
    const tg = window.Telegram?.WebApp;
    const initData = tg?.initData;

    if (initData && String(initData).trim()) {
      return initData;
    }

    await sleep(150);
  }

  return '';
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
  const role = $('debugRole')?.value || 'user';
  const roleFlags = getDevRoleFlags(role);
  const body = {
    telegram_user_id: Number($('debugUserId')?.value || '1001'),
    full_name: $('debugUserName')?.value || null,
    ...roleFlags,
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

async function telegramLogin({ silent = false } = {}) {
  const tg = window.Telegram?.WebApp;

  if (!silent) {
    setAuthState('Пробуем войти через Telegram...');
  }

  log({
    telegramLoginStarted: true,
    hasTelegram: Boolean(window.Telegram),
    hasWebApp: Boolean(tg),
    initDataPresentImmediately: Boolean(tg?.initData),
    initDataLengthImmediately: tg?.initData?.length || 0,
  });

  const initData = await waitForTelegramInitData(4000);

  log({
    telegramLoginAfterWait: true,
    initDataPresent: Boolean(initData),
    initDataLength: initData?.length || 0,
  });

  if (!initData) {
    setAuthState('Telegram не передал данные авторизации');
    if (!silent) {
      showToast('Telegram не передал initData', 'error');
    }
    return false;
  }

  const data = await api(API.telegramInit, {
    method: 'POST',
    body: JSON.stringify({ init_data: initData }),
  });

  localStorage.setItem(accessTokenKey, data.access_token);
  localStorage.setItem(refreshTokenKey, data.refresh_token);

  setAuthState('Вход через Telegram выполнен');
  if (!silent) {
    showToast('Вход через Telegram выполнен');
  }
  return true;
}

async function reauthenticateViaTelegram() {
  if (state.isReauthInProgress) {
    return false;
  }

  state.isReauthInProgress = true;
  try {
    clearTokens();
    const ok = await telegramLogin({ silent: true });
    if (!ok) {
      setAuthState('Не удалось обновить авторизацию через Telegram');
      return false;
    }
    return true;
  } catch (error) {
    log(`reauthenticateViaTelegram: ${String(error)}`);
    setAuthState('Не удалось обновить авторизацию через Telegram');
    return false;
  } finally {
    state.isReauthInProgress = false;
  }
}

async function tryTelegramAutoLogin() {
  try {
    return await telegramLogin({ silent: false });
  } catch (error) {
    log(`Ошибка Telegram auth: ${String(error)}`);
    setAuthState('Не удалось войти через Telegram');
    showToast('Не удалось войти через Telegram', 'error');
    return false;
  }
}

async function withReauth(action) {
  try {
    return await action();
  } catch (error) {
    if (error?.status === 401) {
      log('Получен 401, пробуем переавторизацию через Telegram');

      const reloginOk = await reauthenticateViaTelegram();
      if (reloginOk) {
        return await action();
      }
    }
    throw error;
  }
}

async function loadMe() {
  state.me = await withReauth(() => api(API.me));
  const profile = state.me.profile || {};

  if ($('full_name')) $('full_name').value = profile.full_name || '';
  if ($('goal')) $('goal').value = profile.goal || '';
  if ($('level')) $('level').value = profile.level || '';
  if ($('height_cm')) $('height_cm').value = profile.height_cm || '';
  if ($('weight_kg')) $('weight_kg').value = profile.weight_kg || '';
  if ($('workouts_per_week')) $('workouts_per_week').value = profile.workouts_per_week || '';

  renderCurrentAccess(state.me);
  setAuthState('Вход выполнен');

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

  await withReauth(() =>
    api(API.meProfile, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  );

  showToast('Профиль сохранён');
  await loadMe();
}

async function loadExercises() {
  state.exercises = await withReauth(() => api(API.exercises));
  renderExerciseCatalog();
}

function renderExerciseCatalog() {
  const list = $('exerciseCatalogList');
  if (!list) return;

  if (!state.exercises.length) {
    list.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__title">Упражнений пока нет</p>
        <p class="empty-state__text muted">
          Добавь своё упражнение ниже или перезагрузи список — стандартный набор подтягивается с сервера.
        </p>
      </div>`;
    return;
  }

  list.innerHTML = state.exercises
    .map(
      (ex) => `
          <div class="item-card">
            <strong>${escapeHtml(ex.title)}</strong>
            <div class="exercise-meta">
              <span class="metric-pill">${escapeHtml(ex.primary_muscle)}</span>
              <span class="metric-pill">${escapeHtml(ex.equipment)}</span>
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
    .join('');

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
        await withReauth(() =>
          api(API.updateExercise(exerciseId), {
            method: 'PATCH',
            body: JSON.stringify({
              title,
              primary_muscle: primaryMuscle,
              equipment,
            }),
          })
        );
        showToast('Упражнение обновлено');
        await loadExercises();
        await loadTemplates();
        await loadTodayWorkout();
      } catch (error) {
        log(`editExercise: ${String(error)}`);
        toastError(error, 'Не удалось обновить упражнение');
      }
    };
  });

  document.querySelectorAll('.delete-exercise-btn').forEach((btn) => {
    btn.onclick = async () => {
      const exerciseId = Number(btn.dataset.exerciseId);
      const ok = await openConfirmDialog({
        title: 'Скрыть упражнение?',
        message: 'Упражнение будет скрыто только в твоём каталоге. Общие данные не затронуты.',
        okText: 'Скрыть',
        danger: true,
      });
      if (!ok) return;

      try {
        await withReauth(() =>
          api(API.deleteExercise(exerciseId), {
            method: 'DELETE',
          })
        );
        showToast('Упражнение скрыто/удалено для текущего пользователя');
        await loadExercises();
        await loadTemplates();
        await loadTodayWorkout();
      } catch (error) {
        log(`deleteExercise: ${String(error)}`);
        toastError(error, 'Не удалось удалить упражнение');
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

  const exercise = await withReauth(() =>
    api(API.createExercise, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  );

  $('newExerciseTitle').value = '';
  $('newExerciseMuscle').value = '';
  $('newExerciseEquipment').value = '';

  showToast(`Упражнение "${exercise.title}" добавлено`);
  await loadExercises();
}

function exerciseTemplate(defaultExerciseId = '', preset = null) {
  const options = state.exercises
    .map(
      (ex) => `<option value="${escapeHtml(ex.id)}" ${String(ex.id) === String(defaultExerciseId) ? 'selected' : ''}>${escapeHtml(ex.title)}</option>`
    )
    .join('');

  return `
    <div class="grid item-card program-ex-row" style="grid-template-columns:2fr 1fr 1fr 1fr auto;">
      <select class="exercise-id">${options}</select>
      <input class="exercise-sets" type="number" min="1" value="${escapeHtml(preset?.prescribed_sets || 3)}" placeholder="Подходы" />
      <input class="exercise-reps" type="text" value="${escapeHtml(preset?.prescribed_reps || '8-10')}" placeholder="Повторы" />
      <input class="exercise-rest" type="number" min="15" value="${escapeHtml(preset?.rest_seconds || 90)}" placeholder="Отдых, сек" />
      <button class="secondary remove-ex-btn" type="button">Удалить</button>
    </div>
  `;
}

function programDayTemplate(index, preset = null) {
  return `
    <div class="item-card day-card" data-day-index="${index}">
      <div class="toolbar wrap">
        <input class="day-title" type="text" placeholder="Название дня" value="${escapeHtml(preset?.title || `День ${index + 1}`)}" />
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
  const mode = getEffectiveBuilderMode();
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
    mode,
    target_telegram_user_id: mode === 'coach' && $('target_telegram_user_id')?.value
      ? Number($('target_telegram_user_id').value)
      : null,
    target_full_name: mode === 'coach' ? $('target_full_name')?.value?.trim() || null : null,
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

  const data = await withReauth(() =>
    api(url, {
      method,
      body: JSON.stringify(payload),
    })
  );

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
}

async function loadTemplateIntoBuilder(templateId) {
  const template = await withReauth(() => api(API.getTemplate(templateId)));

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
  await withReauth(() =>
    api(API.assignTemplateToMe(templateId), {
      method: 'POST',
    })
  );
  showToast('Шаблон загружен в тренировки');
  await loadTodayWorkout();
  await resetHistoryAndReload();
}

async function deleteTemplate(templateId) {
  await withReauth(() =>
    api(API.deleteTemplate(templateId), {
      method: 'DELETE',
    })
  );
  showToast('Шаблон удалён');
  await loadTemplates();
}

function getClientDisplayName(client) {
  return client.full_name || client.username || client.telegram_user_id || 'Клиент';
}

function selectClientForProgram(client) {
  if (!client.telegram_user_id) {
    showToast('Клиент ещё не привязан к Telegram ID', 'error');
    return;
  }

  if ($('builder_mode')) $('builder_mode').value = 'coach';
  if ($('target_telegram_user_id')) {
    $('target_telegram_user_id').value = String(client.telegram_user_id);
  }
  if ($('target_full_name')) {
    $('target_full_name').value = client.full_name || client.username || '';
  }

  toggleCoachUI();
  expandSectionAndScroll('section-builder', 'card-builder');
  showToast(`Клиент выбран: ${getClientDisplayName(client)}`);
}

async function addClient() {
  const telegramIdValue = $('clientTelegramId')?.value?.trim() || '';
  const username = $('clientUsername')?.value?.trim() || '';
  const fullName = $('clientFullName')?.value?.trim() || '';

  if (!telegramIdValue && !username) {
    showToast('Укажи Telegram ID или username клиента', 'error');
    return;
  }

  const client = await withReauth(() =>
    api(API.createClient, {
      method: 'POST',
      body: JSON.stringify({
        telegram_user_id: telegramIdValue ? Number(telegramIdValue) : null,
        username: username || null,
        full_name: fullName || null,
      }),
    })
  );

  if ($('clientTelegramId')) $('clientTelegramId').value = '';
  if ($('clientUsername')) $('clientUsername').value = '';
  if ($('clientFullName')) $('clientFullName').value = '';

  showToast(client.status === 'pending' ? 'Клиент добавлен в ожидание' : 'Клиент добавлен');
  await loadClients();
}

async function loadTemplates() {
  state.templates = await withReauth(() => api(API.myTemplates));
  const list = $('templatesList');
  if (!list) return;

  if (!state.templates.length) {
    list.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__title">Шаблонов пока нет</p>
        <p class="empty-state__text muted">
          Создай программу в конструкторе и сохрани её — или назначь общий шаблон, если он доступен в списке.
        </p>
        <div class="toolbar wrap" style="justify-content: center">
          <button type="button" class="secondary empty-state-goto" data-nav-section="section-builder" data-nav-card="card-builder">
            Открыть конструктор
          </button>
        </div>
      </div>`;
    return;
  }

  list.innerHTML = state.templates
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
            <strong>${escapeHtml(template.title)}</strong><br>
            <span class="muted">${escapeHtml(template.goal)} - ${escapeHtml(template.level)}</span>
            <div class="top-gap">
              ${
                template.days?.length
                  ? template.days
                      .map(
                        (day) => `
                          <div class="top-gap">
                            <strong>${escapeHtml(day.title)}</strong>
                            <div class="muted">${(day.exercises || []).map((ex) => escapeHtml(ex.exercise_title)).join(', ')}</div>
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
    .join('');

  document.querySelectorAll('.assign-template-btn').forEach((btn) => {
    btn.onclick = async () => {
      try {
        await assignTemplateToMe(Number(btn.dataset.templateId));
      } catch (error) {
        log(`assignTemplateToMe: ${String(error)}`);
        toastError(error, 'Не удалось загрузить шаблон в тренировки');
      }
    };
  });

  document.querySelectorAll('.edit-template-btn').forEach((btn) => {
    btn.onclick = async () => {
      try {
        await loadTemplateIntoBuilder(Number(btn.dataset.templateId));
      } catch (error) {
        log(`loadTemplateIntoBuilder: ${String(error)}`);
        toastError(error, 'Не удалось загрузить шаблон в конструктор');
      }
    };
  });

  document.querySelectorAll('.delete-template-btn').forEach((btn) => {
    btn.onclick = async () => {
      const ok = await openConfirmDialog({
        title: 'Удалить шаблон?',
        message: 'Шаблон и связанные данные для тебя будут удалены. Это действие нельзя отменить.',
        okText: 'Удалить',
        danger: true,
      });
      if (!ok) return;
      try {
        await deleteTemplate(Number(btn.dataset.templateId));
      } catch (error) {
        log(`deleteTemplate: ${String(error)}`);
        toastError(error, 'Не удалось удалить шаблон');
      }
    };
  });
}

async function loadClients() {
  const card = $('clientsCard');
  if (card) card.classList.toggle('hidden', !isCoachOrAdmin());

  if (!isCoachOrAdmin()) return;

  const rows = await withReauth(() => api(API.clients));
  const list = $('clientsList');
  if (!list) return;

  list.innerHTML = rows.length
    ? rows
        .map(
          (c) => {
            const isPending = c.status === 'pending';
            return `
          <div class="item-card">
            <strong>${escapeHtml(getClientDisplayName(c))}</strong><br>
            <span class="muted">
              ${isPending ? 'Ожидает входа' : `ID: ${escapeHtml(c.telegram_user_id)}`}
              ${c.username ? ` | @${escapeHtml(c.username)}` : ''}
              ${!isPending ? ` | цель=${escapeHtml(c.goal || '-')} | уровень=${escapeHtml(c.level || '-')}` : ''}
            </span>
            ${
              isPending
                ? ''
                : `<div class="toolbar wrap top-gap">
                    <button
                      class="secondary assign-client-btn"
                      type="button"
                      data-client='${escapeHtml(JSON.stringify(c))}'
                    >
                      Назначить программу
                    </button>
                  </div>`
            }
          </div>`;
          }
        )
        .join('')
    : `<div class="empty-state">
        <p class="empty-state__title">Клиентов пока нет</p>
        <p class="empty-state__text muted">Добавь клиента по Telegram ID или username.</p>
      </div>`;

  document.querySelectorAll('.assign-client-btn').forEach((btn) => {
    btn.onclick = () => {
      try {
        selectClientForProgram(JSON.parse(btn.dataset.client));
      } catch (error) {
        log(`selectClientForProgram: ${String(error)}`);
        showToast('Не удалось выбрать клиента', 'error');
      }
    };
  });
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
  state.currentWorkoutTimerStartedAtMs = null;
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

function startWorkoutTimerFromMs(startedAtMs) {
  clearWorkoutTimer();
  const timerNode = $('workoutTimer');
  if (!timerNode || !startedAtMs) return;

  state.currentWorkoutTimerStartedAtMs = startedAtMs;

  const render = () => {
    timerNode.textContent = `Длительность тренировки: ${formatDurationMs(Date.now() - startedAtMs)}`;
  };

  render();
  state.workoutTimer = setInterval(render, 1000);
}

async function updateSetRow(setId, payload) {
  await withReauth(() =>
    api(API.updateSet(setId), {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  );
}

async function deleteTodayWorkout() {
  if (state.todayWorkout?.id) {
    clearWorkoutTimerStart(state.todayWorkout.id);
  }

  await withReauth(() =>
    api(API.deleteTodayWorkout, {
      method: 'DELETE',
    })
  );

  showToast('Тренировка на сегодня удалена');
  state.todayWorkout = null;
  clearWorkoutTimer();
  renderTodayWorkout(null);
  await resetHistoryAndReload();
}

function renderTodayWorkout(workout) {
  const container = $('todayWorkout');
  if (!container) return;

  if (!workout) {
    container.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__title">На сегодня тренировка не назначена</p>
        <p class="empty-state__text muted">
          Собери программу в конструкторе или назначь шаблон — тогда здесь появится план тренировки.
        </p>
        <div class="toolbar wrap" style="justify-content: center">
          <button type="button" class="secondary empty-state-goto" data-nav-section="section-builder" data-nav-card="card-builder">
            Открыть конструктор
          </button>
          <button type="button" class="secondary empty-state-goto" data-nav-section="section-templates" data-nav-card="card-templates">
            К шаблонам
          </button>
        </div>
      </div>`;
    clearWorkoutTimer();
    return;
  }

  const deleteBtn = `<button id="deleteTodayWorkoutBtn" class="secondary" type="button">Удалить тренировку</button>`;

  const actionButtons =
    workout.status === 'planned'
      ? `<button id="startWorkoutBtn" type="button">Начать тренировку</button>${deleteBtn}`
      : workout.status === 'in_progress'
        ? `<button id="finishWorkoutBtn" type="button">Завершить тренировку</button>${deleteBtn}`
        : deleteBtn;
  const setInputsDisabled = workout.status === 'completed' ? 'disabled' : '';

  container.innerHTML = `
    <div class="item-card">
      <strong>${escapeHtml(workout.title)}</strong><br>
      <span class="muted">Статус: ${statusLabel(workout.status)}</span>
      <div id="workoutTimer" class="top-gap muted"></div>
      <div class="toolbar wrap top-gap">
        ${actionButtons}
      </div>
    </div>

    <div class="stack top-gap">
      ${(workout.exercises || []).map((exercise) => `
        <div class="item-card">
          <strong>${escapeHtml(exercise.exercise_title)}</strong>
          <div class="muted top-gap">
            План: ${escapeHtml(exercise.prescribed_sets)} x ${escapeHtml(exercise.prescribed_reps)}, отдых ${escapeHtml(exercise.rest_seconds)} сек
          </div>

          <div class="stack top-gap">
            ${(exercise.sets || []).map((setRow) => `
              <div class="grid item-card" style="grid-template-columns: 1fr 1fr 1fr auto;">
                <div>Подход ${escapeHtml(setRow.set_number)}</div>
                <input
                  class="set-reps"
                  type="number"
                  min="0"
                  value="${escapeHtml(setRow.actual_reps ?? '')}"
                  data-set-id="${setRow.id}"
                  placeholder="Повторы"
                  ${setInputsDisabled}
                />
                <input
                  class="set-weight"
                  type="number"
                  min="0"
                  step="0.1"
                  value="${escapeHtml(setRow.actual_weight ?? '')}"
                  data-set-id="${setRow.id}"
                  placeholder="Вес"
                  ${setInputsDisabled}
                />
                <label class="checkbox-row">
                  <input
                    class="set-completed"
                    type="checkbox"
                    data-set-id="${setRow.id}"
                    ${setRow.is_completed ? 'checked' : ''}
                    ${setInputsDisabled}
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

  if (workout.status === 'in_progress') {
    let startedAtMs = loadWorkoutTimerStart(workout.id);
    if (!startedAtMs) {
      startedAtMs = Date.now();
      saveWorkoutTimerStart(workout.id, startedAtMs);
    }
    startWorkoutTimerFromMs(startedAtMs);
  } else if (workout.status === 'completed') {
    clearWorkoutTimer();
    const timerNode = $('workoutTimer');
    const startedAtMs = loadWorkoutTimerStart(workout.id);
    if (timerNode && startedAtMs) {
      const finishedAtMs = Date.now();
      timerNode.textContent = `Длительность тренировки: ${formatDurationMs(finishedAtMs - startedAtMs)}`;
    }
  } else {
    clearWorkoutTimer();
    const timerNode = $('workoutTimer');
    if (timerNode) {
      timerNode.textContent = 'Таймер ещё не запущен';
    }
  }

  const deleteBtnNode = $('deleteTodayWorkoutBtn');
  if (deleteBtnNode) {
    deleteBtnNode.onclick = async () => {
      const ok = await openConfirmDialog({
        title: 'Удалить тренировку?',
        message: 'Тренировка на сегодня будет снята с расписания. Это действие нельзя отменить.',
        okText: 'Удалить',
        danger: true,
      });
      if (!ok) return;
      try {
        await deleteTodayWorkout();
      } catch (error) {
        log(`deleteTodayWorkout: ${String(error)}`);
        toastError(error, 'Не удалось удалить тренировку');
      }
    };
  }

  const startBtn = $('startWorkoutBtn');
  if (startBtn) {
    startBtn.onclick = async () => {
      try {
        const localStartMs = Date.now();
        saveWorkoutTimerStart(workout.id, localStartMs);

        state.todayWorkout = await withReauth(() =>
          api(API.startWorkout(workout.id), { method: 'POST' })
        );
        showToast('Тренировка начата');
        renderTodayWorkout(state.todayWorkout);
        await resetHistoryAndReload();
      } catch (error) {
        log(`startWorkout: ${String(error)}`);
        toastError(error, 'Не удалось начать тренировку');
      }
    };
  }

  const finishBtn = $('finishWorkoutBtn');
  if (finishBtn) {
    finishBtn.onclick = async () => {
      try {
        const localStartMs = loadWorkoutTimerStart(workout.id);
        state.todayWorkout = await withReauth(() =>
          api(API.finishWorkout(workout.id), { method: 'POST' })
        );
        showToast('Тренировка завершена');
        renderTodayWorkout(state.todayWorkout);

        const timerNode = $('workoutTimer');
        if (timerNode && localStartMs) {
          timerNode.textContent = `Длительность тренировки: ${formatDurationMs(Date.now() - localStartMs)}`;
        }

        clearWorkoutTimerStart(workout.id);
        clearWorkoutTimer();
        await resetHistoryAndReload();
      } catch (error) {
        log(`finishWorkout: ${String(error)}`);
        toastError(error, 'Не удалось завершить тренировку');
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
        toastError(error, 'Не удалось сохранить подход');
      }
    });
  });
}

async function loadTodayWorkout() {
  try {
    state.todayWorkout = await withReauth(() => api(API.todayWorkout));
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
    container.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__title">История пуста</p>
        <p class="empty-state__text muted">Завершённые тренировки появятся здесь после занятий.</p>
        <div class="toolbar wrap" style="justify-content: center">
          <button type="button" class="secondary empty-state-goto" data-nav-section="section-today-workout" data-nav-card="card-today">
            К тренировке на сегодня
          </button>
        </div>
      </div>`;
    return;
  }

  const html = rows
    .map((item) => `
      <div class="item-card">
        <strong>${escapeHtml(item.title)}</strong><br>
        <span class="muted">${escapeHtml(item.scheduled_date)} - ${statusLabel(item.status)}</span>
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
  const rows = await withReauth(() => api(API.workoutHistory(offset, state.historyLimit)));

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
    state.plans = await withReauth(() => api(API.billingPlans));
    const subscription = await withReauth(() => api(API.billingSubscription));

    if ($('subscriptionInfo')) {
      $('subscriptionInfo').textContent = subscription
        ? `Активна: ${subscription.plan_title} до ${new Date(subscription.ends_at).toLocaleString()}`
        : 'Активной подписки нет';
    }

    const plansList = $('plansList');
    if (!plansList) return;

    plansList.innerHTML = state.plans.length
      ? state.plans
          .map(
            (plan) => `
            <div class="item-card">
              <strong>${escapeHtml(plan.title)}</strong><br>
              <span class="muted">${escapeHtml(plan.price)} ${escapeHtml(plan.currency)} / ${escapeHtml(plan.period_days)} дн.</span>
              <div class="toolbar wrap top-gap">
                <button class="secondary buy-plan-btn" data-plan="${escapeHtml(plan.code)}" type="button">Купить</button>
              </div>
            </div>
          `
          )
          .join('')
      : `<div class="empty-state">
          <p class="empty-state__title">Тарифы недоступны</p>
          <p class="empty-state__text muted">Попробуй обновить раздел позже.</p>
        </div>`;

    document.querySelectorAll('.buy-plan-btn').forEach((btn) => {
      btn.onclick = async () => {
        try {
          const checkout = await withReauth(() =>
            api(API.billingCheckout, {
              method: 'POST',
              body: JSON.stringify({ plan_code: btn.dataset.plan }),
            })
          );

          if (checkout?.checkout_id) {
            await withReauth(() => api(API.billingMockComplete(checkout.checkout_id), { method: 'POST' }));
            showToast('Подписка активирована');
            await loadBilling();
          }
        } catch (error) {
          log(`buyPlan: ${String(error)}`);
          toastError(error, 'Не удалось оформить подписку');
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

  await withReauth(() =>
    api(API.notifications, {
      method: 'POST',
      body: JSON.stringify({
        title,
        body,
        scheduled_for: new Date(dateTime).toISOString(),
      }),
    })
  );

  $('manualNotifTitle').value = '';
  $('manualNotifBody').value = '';
  $('manualNotifDateTime').value = '';

  showToast('Напоминание создано');
  await loadNotifications();
}

async function deleteNotification(notificationId) {
  await withReauth(() =>
    api(API.deleteNotification(notificationId), {
      method: 'DELETE',
    })
  );
  showToast('Напоминание удалено');
  await loadNotifications();
}

async function loadNotifications() {
  try {
    const settings = await withReauth(() => api(API.notificationsSettings));
    const rows = await withReauth(() => api(API.notifications));

    if ($('notifEnabled')) $('notifEnabled').checked = Boolean(settings.workout_reminders_enabled);
    if ($('notifHour')) $('notifHour').value = settings.reminder_hour ?? 9;

    const list = $('notificationsList');
    if (!list) return;

    list.innerHTML =
      (rows || [])
        .map(
          (n) => `
            <div class="item-card">
              <strong>${escapeHtml(n.title)}</strong><br>
              <span class="muted">${escapeHtml(new Date(n.scheduled_for).toLocaleString())} - ${escapeHtml(n.status)}</span>
              <div class="top-gap">${escapeHtml(n.body)}</div>
              <div class="toolbar wrap top-gap">
                <button class="secondary delete-notification-btn" type="button" data-notification-id="${n.id}">
                  Удалить напоминание
                </button>
              </div>
            </div>
          `
        )
        .join('') ||
      `<div class="empty-state">
        <p class="empty-state__title">Нет напоминаний</p>
        <p class="empty-state__text muted">Создай напоминание вручную или включи автоматические в настройках выше.</p>
      </div>`;

    document.querySelectorAll('.delete-notification-btn').forEach((btn) => {
      btn.onclick = async () => {
        const ok = await openConfirmDialog({
          title: 'Удалить напоминание?',
          message: 'Напоминание будет удалено без возможности восстановления.',
          okText: 'Удалить',
          danger: true,
        });
        if (!ok) return;

        try {
          await deleteNotification(Number(btn.dataset.notificationId));
        } catch (error) {
          log(`deleteNotification: ${String(error)}`);
          toastError(error, 'Не удалось удалить напоминание');
        }
      };
    });
  } catch (error) {
    log(`loadNotifications: ${String(error)}`);
  }
}

async function saveNotificationSettings() {
  await withReauth(() =>
    api(API.notificationsSettings, {
      method: 'PATCH',
      body: JSON.stringify({
        workout_reminders_enabled: Boolean($('notifEnabled')?.checked),
        reminder_hour: Number($('notifHour')?.value || '9'),
      }),
    })
  );

  showToast('Настройки уведомлений сохранены');
  await loadNotifications();
}

async function bootstrap() {
  setAppLoading(true);
  try {
    await loadMe();
    await loadExercises();
    await loadTemplates();
    await loadClients();
    await loadTodayWorkout();
    await resetHistoryAndReload();
    await loadNotifications();

    if (!document.querySelector('.day-card')) {
      fillExample();
    }
  } finally {
    setAppLoading(false);
  }
}

function bindUI() {
  if ($('telegramLoginBtn')) {
    $('telegramLoginBtn').onclick = async () => {
      try {
        const ok = await tryTelegramAutoLogin();
        if (ok) {
          await bootstrap();
        }
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
        toastError(error, 'Не удалось выполнить dev-вход');
      }
    };
  }

  document.querySelectorAll('[data-dev-login-role]').forEach((button) => {
    button.onclick = async () => {
      try {
        fillDevPreset(button.dataset.devLoginRole);
        await devLogin();
      } catch (error) {
        log(`quick devLogin: ${String(error)}`);
        toastError(error, 'Не удалось выполнить demo-вход');
      }
    };
  });

  document.querySelectorAll('[data-dev-role-option]').forEach((button) => {
    button.onclick = () => setDevRole(button.dataset.devRoleOption);
  });

  setDevRole($('debugRole')?.value || 'user');

  if ($('saveProfileBtn')) {
    $('saveProfileBtn').onclick = async () => {
      try {
        await saveProfile();
      } catch (error) {
        log(`saveProfile: ${String(error)}`);
        toastError(error, 'Не удалось сохранить профиль');
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
        toastError(error, 'Не удалось сохранить программу');
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

  if ($('addClientBtn')) {
    $('addClientBtn').onclick = async () => {
      try {
        await addClient();
      } catch (error) {
        log(`addClientBtn: ${String(error)}`);
        toastError(error, 'Не удалось добавить клиента');
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
        toastError(error, 'Не удалось добавить упражнение');
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
        toastError(error, 'Не удалось сохранить настройки уведомлений');
      }
    };
  }

  if ($('createNotificationBtn')) {
    $('createNotificationBtn').onclick = async () => {
      try {
        await createManualNotification();
      } catch (error) {
        log(`createNotificationBtn: ${String(error)}`);
        toastError(error, 'Не удалось создать напоминание');
      }
    };
  }

  if ($('loadMoreHistoryBtn')) {
    $('loadMoreHistoryBtn').onclick = async () => {
      try {
        await loadWorkoutHistory(true);
      } catch (error) {
        log(`loadMoreHistoryBtn: ${String(error)}`);
        toastError(error, 'Не удалось загрузить ещё историю');
      }
    };
  }
}

async function init() {
  bindUI();
  bindGlobalNavHandlers();
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

  setAuthState('Проверяем авторизацию через Telegram...');
  renderCurrentAccess(null);

  const token = localStorage.getItem(accessTokenKey);

  if (token) {
    try {
      await bootstrap();
      return;
    } catch (error) {
      log(`bootstrap by saved token: ${String(error)}`);

      if (error?.status === 401) {
        const reloginOk = await reauthenticateViaTelegram();
        if (reloginOk) {
          try {
            await bootstrap();
            return;
          } catch (retryError) {
            log(`bootstrap after reauth: ${String(retryError)}`);
          }
        }
      }

      clearTokens();
    }
  }

  const loginOk = await tryTelegramAutoLogin();
  if (loginOk) {
    try {
      await bootstrap();
      return;
    } catch (error) {
      log(`bootstrap after telegram login: ${String(error)}`);
      toastError(error, 'Не удалось загрузить данные приложения');
      setAuthState('Вход выполнен, но загрузка данных не удалась');
      return;
    }
  }

  setAuthState('Не удалось авторизоваться через Telegram');
}

document.addEventListener('DOMContentLoaded', init);
