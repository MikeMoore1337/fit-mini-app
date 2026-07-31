import { initTelegramTheme } from './core/theme.js?v=50';
import { openConfirmDialog } from './core/ui.js?v=50';

initTelegramTheme({ onError: (error) => console.warn(`Telegram theme: ${String(error)}`) });

const accessTokenKey = 'fit_access_token';
const legacyToken = localStorage.getItem(accessTokenKey);
if (legacyToken && !sessionStorage.getItem(accessTokenKey)) {
  sessionStorage.setItem(accessTokenKey, legacyToken);
}
localStorage.removeItem(accessTokenKey);
localStorage.removeItem('fit_refresh_token');

const state = {
  me: null,
  clients: [],
  selectedClient: null,
  measurements: [],
  exercises: [],
  templates: [],
  daySequence: 0,
};

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
  const text = value == null ? '' : String(value);
  const replacements = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.replace(/[&<>"']/g, (char) => replacements[char]);
}

function log(message) {
  const node = $('coachLog');
  if (!node) return;
  node.textContent = `${new Date().toLocaleTimeString()} · ${String(message)}\n${node.textContent}`;
}

let toastTimer = null;
function showToast(message, type = 'success') {
  const node = $('toast');
  if (!node) return;
  clearTimeout(toastTimer);
  node.textContent = message;
  node.className = `toast ${type === 'error' ? 'error' : ''}`.trim();
  toastTimer = setTimeout(() => { node.className = 'toast hidden'; }, 2800);
}

function authHeaders() {
  const token = sessionStorage.getItem(accessTokenKey);
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
}

async function refreshAccessToken() {
  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: '{}',
  });
  if (!response.ok) return false;
  const data = await response.json();
  sessionStorage.setItem(accessTokenKey, data.access_token);
  return true;
}

async function api(path, options = {}, allowRefresh = true) {
  const response = await fetch(path, {
    ...options,
    credentials: 'same-origin',
    headers: { ...authHeaders(), ...(options.headers || {}) },
  });
  if (response.status === 401 && allowRefresh && await refreshAccessToken()) {
    return api(path, options, false);
  }
  if (!response.ok) {
    let message = `Ошибка ${response.status}`;
    try {
      const data = await response.json();
      message = typeof data.detail === 'string' ? data.detail : message;
    } catch (_) { /* response is not JSON */ }
    throw new Error(message);
  }
  if (response.status === 204) return null;
  return response.json();
}

function displayName(client) {
  return client?.full_name || client?.username || client?.telegram_user_id || 'Клиент';
}

function goalLabel(value) {
  return ({ fat_loss: 'Похудение', muscle_gain: 'Набор мышц', maintenance: 'Поддержание', recomposition: 'Рекомпозиция' }[value] || 'Не указана');
}

function levelLabel(value) {
  return ({ beginner: 'Начальный', intermediate: 'Средний', advanced: 'Продвинутый' }[value] || 'Не указан');
}

function decimalValue(id) {
  const raw = $(id)?.value?.trim().replace(',', '.');
  if (!raw) return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function todayIso() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

async function ensureCoachAccess() {
  state.me = await api('/api/v1/me');
  if (!state.me.is_coach && !state.me.is_admin) throw new Error('Недостаточно прав тренера');
}

function renderClients() {
  const query = $('clientSearch').value.trim().toLowerCase();
  const visible = state.clients.filter((client) => {
    const text = [client.full_name, client.username, client.telegram_user_id].filter(Boolean).join(' ').toLowerCase();
    return !query || text.includes(query);
  });
  const active = state.clients.filter((client) => client.status === 'active');
  const previous = String(state.selectedClient?.id || '');
  $('clientSelect').innerHTML = [
    '<option value="">Выберите клиента</option>',
    ...active.map((client) => `<option value="${client.id}">${escapeHtml(displayName(client))}</option>`),
  ].join('');
  if (active.some((client) => String(client.id) === previous)) $('clientSelect').value = previous;

  $('coachClientsList').innerHTML = visible.length ? visible.map((client) => {
    const pending = client.status === 'pending';
    return `<div class="item-card">
      <strong>${escapeHtml(displayName(client))}</strong><br>
      <span class="muted">${pending ? 'Ожидает подтверждения' : `Telegram ID: ${escapeHtml(client.telegram_user_id)}`}${client.username ? ` · @${escapeHtml(client.username)}` : ''}</span>
      <div class="toolbar wrap top-gap">
        ${pending ? '' : `<button type="button" data-open-client="${client.id}">Открыть карточку</button>`}
        <button class="btn-danger" type="button" data-remove-client="${client.id || ''}" data-invite-id="${client.invite_id || ''}" data-pending="${pending}" data-username="${escapeHtml(client.username || '')}">Удалить</button>
      </div>
    </div>`;
  }).join('') : '<p class="muted">Клиенты не найдены.</p>';
}

async function loadClients() {
  state.clients = await api('/api/v1/coach/clients');
  if (state.selectedClient) {
    state.selectedClient = state.clients.find((item) => item.id === state.selectedClient.id) || null;
  }
  renderClients();
  if (state.selectedClient) fillClientDetail();
}

async function addClient() {
  const telegramId = $('clientTelegramId').value.trim();
  const username = $('clientUsername').value.trim();
  if (!telegramId && !username) throw new Error('Укажите Telegram ID или @username клиента');
  const client = await api('/api/v1/coach/clients', {
    method: 'POST',
    body: JSON.stringify({
      telegram_user_id: telegramId ? Number(telegramId) : null,
      username: username || null,
      full_name: $('clientFullName').value.trim() || null,
    }),
  });
  ['clientTelegramId', 'clientUsername', 'clientFullName'].forEach((id) => { $(id).value = ''; });
  showToast(client.status === 'pending' ? 'Приглашение клиенту создано' : 'Клиент добавлен');
  await loadClients();
}

function renderOverview() {
  const client = state.selectedClient;
  const kbju = client?.kbju;
  $('clientOverview').innerHTML = `
    <div class="progress-card"><span>Цель</span><strong>${escapeHtml(goalLabel(client.goal))}</strong></div>
    <div class="progress-card"><span>Уровень</span><strong>${escapeHtml(levelLabel(client.level))}</strong></div>
    <div class="progress-card"><span>Вес</span><strong>${client.weight_kg ? `${escapeHtml(client.weight_kg)} кг` : '—'}</strong></div>
    <div class="progress-card"><span>КБЖУ</span><strong>${kbju ? `${escapeHtml(kbju.calories)} ккал` : 'Не назначен'}</strong></div>`;
}

function fillKbju(client) {
  const kbju = client.kbju;
  $('kbjuSex').value = kbju?.sex || 'male';
  $('kbjuWeight').value = kbju?.weight_kg ?? client.weight_kg ?? '';
  $('kbjuHeight').value = kbju?.height_cm ?? client.height_cm ?? '';
  $('kbjuAge').value = kbju?.age ?? '';
  $('kbjuDailyActivity').value = kbju?.daily_activity_level || 'sedentary';
  $('kbjuStrength').value = kbju?.strength_trainings_per_week ?? client.workouts_per_week ?? '';
  $('kbjuStrengthDuration').value = kbju?.strength_training_duration_minutes ?? 60;
  $('kbjuCardio').value = kbju?.cardio_trainings_per_week ?? client.cardio_trainings_per_week ?? 0;
  $('kbjuCardioDuration').value = kbju?.cardio_training_duration_minutes ?? 30;
  $('kbjuCardioIntensity').value = kbju?.cardio_intensity || 'moderate';
  $('kbjuGoal').value = kbju?.goal || client.goal || 'maintenance';
  updateNutritionPreview();
}

function visibleExercisesForClient() {
  const clientId = state.selectedClient?.id;
  return state.exercises.filter((exercise) => !exercise.created_by_user_id || exercise.created_by_user_id === clientId);
}

function exerciseOptions(selected = '') {
  const rows = visibleExercisesForClient();
  return ['<option value="">Выберите упражнение</option>', ...rows.map((exercise) =>
    `<option value="${exercise.id}" ${String(exercise.id) === String(selected) ? 'selected' : ''}>${escapeHtml(exercise.title)}</option>`
  )].join('');
}

function refreshExerciseSelects() {
  document.querySelectorAll('.coach-exercise-id').forEach((select) => {
    const value = select.value;
    select.innerHTML = exerciseOptions(value);
  });
}

function syncTemplateOptions() {
  const client = state.selectedClient;
  const rows = state.templates.filter((template) => template.is_public || template.owner_user_id === client?.id || template.owner_user_id === state.me?.id);
  $('templateSelect').innerHTML = rows.length
    ? ['<option value="">Выберите шаблон</option>', ...rows.map((template) => `<option value="${template.id}">${escapeHtml(template.title)} · ${escapeHtml(goalLabel(template.goal))}</option>`)].join('')
    : '<option value="">Нет доступных шаблонов</option>';
}

function fillClientDetail() {
  const client = state.selectedClient;
  if (!client) return;
  $('detailClientName').textContent = displayName(client);
  $('detailClientMeta').textContent = `Telegram ID: ${client.telegram_user_id}${client.username ? ` · @${client.username}` : ''}`;
  $('profileFullName').value = client.full_name || '';
  $('profileGoal').value = client.goal || '';
  $('profileLevel').value = client.level || '';
  $('profileHeight').value = client.height_cm || '';
  $('profileWeight').value = client.weight_kg || '';
  $('profileWorkouts').value = client.workouts_per_week ?? '';
  $('profileCardio').value = client.cardio_trainings_per_week ?? '';
  $('programGoal').value = client.goal || 'maintenance';
  $('programLevel').value = client.level || 'beginner';
  fillKbju(client);
  renderOverview();
  syncTemplateOptions();
  refreshExerciseSelects();
  $('coachClientDetail').classList.remove('hidden');
}

async function openClient(clientId) {
  const client = state.clients.find((item) => item.id === Number(clientId) && item.status === 'active');
  if (!client) throw new Error('Клиент не найден');
  state.selectedClient = client;
  $('clientSelect').value = String(client.id);
  fillClientDetail();
  await loadMeasurements();
  if (!$('programDays').children.length) addProgramDay();
  $('coachClientDetail').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function saveProfile() {
  const client = state.selectedClient;
  const updated = await api(`/api/v1/coach/clients/${client.id}/profile`, {
    method: 'PATCH',
    body: JSON.stringify({
      full_name: $('profileFullName').value.trim() || null,
      goal: $('profileGoal').value || null,
      level: $('profileLevel').value || null,
      height_cm: $('profileHeight').value ? Number($('profileHeight').value) : null,
      weight_kg: $('profileWeight').value ? Number($('profileWeight').value) : null,
      workouts_per_week: $('profileWorkouts').value ? Number($('profileWorkouts').value) : null,
      cardio_trainings_per_week: $('profileCardio').value
        ? Number($('profileCardio').value)
        : null,
    }),
  });
  state.selectedClient = updated;
  state.clients = state.clients.map((item) => item.id === updated.id ? updated : item);
  renderClients();
  fillClientDetail();
  showToast('Анкета клиента сохранена');
}

function measurementLabel(row) {
  return [
    row.weight_kg != null ? `вес ${row.weight_kg} кг` : '', row.chest_cm != null ? `грудь ${row.chest_cm}` : '',
    row.waist_cm != null ? `талия ${row.waist_cm}` : '', row.hips_cm != null ? `бёдра ${row.hips_cm}` : '',
    row.biceps_cm != null ? `бицепс ${row.biceps_cm}` : '', row.thigh_cm != null ? `бедро ${row.thigh_cm}` : '',
  ].filter(Boolean).join(' · ');
}

function renderMeasurements() {
  $('clientMeasurements').innerHTML = state.measurements.length ? state.measurements.map((row) => `
    <div class="item-card"><strong>${escapeHtml(row.measured_on)}</strong>
      <p class="muted top-gap">${escapeHtml(measurementLabel(row) || 'Без числовых замеров')}</p>
      ${row.note ? `<p class="top-gap">${escapeHtml(row.note)}</p>` : ''}
      <div class="toolbar top-gap"><button class="btn-danger" type="button" data-delete-measurement="${row.id}">Удалить</button></div>
    </div>`).join('') : '<p class="muted">Замеров пока нет.</p>';
}

async function loadMeasurements() {
  state.measurements = await api(`/api/v1/coach/clients/${state.selectedClient.id}/measurements`);
  renderMeasurements();
}

async function saveMeasurement() {
  const map = {
    weight_kg: 'measurementWeight', chest_cm: 'measurementChest', waist_cm: 'measurementWaist',
    hips_cm: 'measurementHips', biceps_cm: 'measurementBiceps', thigh_cm: 'measurementThigh',
  };
  const body = { measured_on: $('measurementDate').value || null, note: $('measurementNote').value.trim() || null };
  Object.entries(map).forEach(([key, id]) => { body[key] = decimalValue(id); });
  await api(`/api/v1/coach/clients/${state.selectedClient.id}/measurements`, { method: 'POST', body: JSON.stringify(body) });
  Object.values(map).forEach((id) => { $(id).value = ''; });
  $('measurementNote').value = '';
  showToast('Замер сохранён');
  await loadMeasurements();
}

function nutritionPayload() {
  const strengthCountRaw = $('kbjuStrength').value.trim();
  const cardioCountRaw = $('kbjuCardio').value.trim();
  const strengthCount = Number(strengthCountRaw);
  const cardioCount = Number(cardioCountRaw);
  const strengthDuration = Number($('kbjuStrengthDuration').value);
  const cardioDuration = Number($('kbjuCardioDuration').value);
  const payload = {
    target_telegram_user_id: state.selectedClient.telegram_user_id,
    sex: $('kbjuSex').value,
    weight_kg: decimalValue('kbjuWeight'), height_cm: decimalValue('kbjuHeight'), age: decimalValue('kbjuAge'),
    daily_activity_level: $('kbjuDailyActivity').value,
    strength_trainings_per_week: strengthCount,
    strength_training_duration_minutes: strengthDuration,
    cardio_trainings_per_week: cardioCount,
    cardio_training_duration_minutes: cardioDuration,
    cardio_intensity: $('kbjuCardioIntensity').value,
    goal: $('kbjuGoal').value,
  };
  if (!payload.weight_kg || payload.weight_kg < 20 || payload.weight_kg > 500
    || !payload.height_cm || payload.height_cm < 50 || payload.height_cm > 280
    || !payload.age || payload.age < 12 || payload.age > 120) {
    throw new Error('Проверьте вес (20–500 кг), рост (50–280 см) и возраст (12–120 лет)');
  }
  if (!strengthCountRaw || !cardioCountRaw
    || !Number.isInteger(strengthCount) || strengthCount < 0 || strengthCount > 14
    || !Number.isInteger(cardioCount) || cardioCount < 0 || cardioCount > 14) {
    throw new Error('Количество тренировок должно быть целым числом от 0 до 14');
  }
  if (!Number.isFinite(strengthDuration) || strengthDuration < 10 || strengthDuration > 300
    || !Number.isFinite(cardioDuration) || cardioDuration < 10 || cardioDuration > 300) {
    throw new Error('Продолжительность тренировки должна быть от 10 до 300 минут');
  }
  return payload;
}

function calculateNutrition() {
  const payload = nutritionPayload();
  const activityCoefficient = ({ sedentary: 1.2, low: 1.3, moderate: 1.4, high: 1.5 })[payload.daily_activity_level];
  const cardioMet = ({ low: 4, moderate: 6, high: 8 })[payload.cardio_intensity];
  const bmr = 10 * payload.weight_kg + 6.25 * payload.height_cm - 5 * payload.age + (payload.sex === 'female' ? -161 : 5);
  const baseTdee = bmr * activityCoefficient;
  const strengthDaily = 5 * payload.weight_kg * (payload.strength_training_duration_minutes / 60) * payload.strength_trainings_per_week / 7;
  const cardioDaily = cardioMet * payload.weight_kg * (payload.cardio_training_duration_minutes / 60) * payload.cardio_trainings_per_week / 7;
  const maintenanceCalories = baseTdee + strengthDaily + cardioDaily;
  const calories = Math.round(maintenanceCalories * ({ fat_loss: .85, muscle_gain: 1.05, maintenance: 1, recomposition: .95 }[payload.goal] || 1) / 10) * 10;
  const protein = Math.round(payload.weight_kg * ({ fat_loss: 2, muscle_gain: 1.8, maintenance: 1.6, recomposition: 2 }[payload.goal] || 1.6));
  const fat = Math.round(payload.weight_kg * (payload.goal === 'muscle_gain' ? .9 : .8));
  const remainingCalories = calories - protein * 4 - fat * 9;
  const carbs = Math.max(0, Math.round(remainingCalories / 4));
  const round = (value) => Math.max(0, Math.round(value));
  const goalDetails = ({
    fat_loss: 'Цель «Снижение веса»: дефицит 15%.', recomposition: 'Цель «Рекомпозиция»: дефицит 5%.',
    maintenance: 'Цель «Поддержание»: без поправки.', muscle_gain: 'Цель «Набор мышечной массы»: профицит 5%.',
  })[payload.goal];
  $('kbjuResult').innerHTML = `<div class="kbju-result-grid">
    <div class="item-card"><span>Калории</span><strong>${calories} ккал</strong></div><div class="item-card"><span>Белки</span><strong>${protein} г</strong></div>
    <div class="item-card"><span>Жиры</span><strong>${fat} г</strong></div><div class="item-card"><span>Углеводы</span><strong>${carbs} г</strong></div></div>
    ${remainingCalories < 0 ? '<div class="nutrition-warning top-gap">Выбранная калорийность слишком мала для установленных норм белка и жиров. Углеводы показаны как 0 г.</div>' : ''}
    <details class="nutrition-details top-gap"><summary>Подробнее о расчёте</summary><div class="muted top-gap">
      <p>Основной обмен: ${round(bmr)} ккал.</p><p>Коэффициент повседневной активности: ×${activityCoefficient}.</p>
      <p>Расход без тренировок: ${round(baseTdee)} ккал.</p><p>Силовые тренировки: в среднем ${round(strengthDaily)} ккал в день.</p>
      <p>Кардио: в среднем ${round(cardioDaily)} ккал в день.</p><p>Поддерживающая калорийность: ${round(maintenanceCalories)} ккал.</p>
      <p>${goalDetails}</p><p>Целевая калорийность: ${calories} ккал.</p>
    </div></details>`;
  $('kbjuResult').classList.remove('hidden');
  return payload;
}

function updateNutritionPreview() {
  try {
    calculateNutrition();
  } catch (error) {
    $('kbjuResult').innerHTML = `<div class="nutrition-warning">${escapeHtml(error.message)}</div>`;
    $('kbjuResult').classList.remove('hidden');
  }
}

async function saveNutrition() {
  const payload = calculateNutrition();
  const saved = await api('/api/v1/nutrition/targets', { method: 'POST', body: JSON.stringify(payload) });
  state.selectedClient.kbju = saved;
  state.clients = state.clients.map((item) => item.id === state.selectedClient.id ? state.selectedClient : item);
  renderOverview();
  showToast('КБЖУ рассчитан и назначен клиенту');
}

function addExerciseRow(container, preset = {}) {
  const row = document.createElement('div');
  row.className = 'grid grid-4 coach-program-exercise';
  row.innerHTML = `
    <label class="field"><span>Упражнение</span><select class="coach-exercise-id">${exerciseOptions(preset.exercise_id)}</select></label>
    <label class="field"><span>Подходы</span><input class="coach-exercise-sets" type="number" min="1" max="12" value="${preset.prescribed_sets || 3}" /></label>
    <label class="field"><span>Повторы</span><input class="coach-exercise-reps" maxlength="32" value="${escapeHtml(preset.prescribed_reps || '8–12')}" /></label>
    <label class="field"><span>Отдых, сек</span><input class="coach-exercise-rest" type="number" min="15" max="600" value="${preset.rest_seconds || 90}" /></label>
    <button class="btn-danger remove-program-exercise" type="button">Убрать упражнение</button>`;
  container.appendChild(row);
}

function addProgramDay() {
  const day = document.createElement('div');
  day.className = 'item-card coach-program-day';
  day.dataset.dayKey = String(++state.daySequence);
  day.innerHTML = `<div class="section-head compact"><label class="field"><span>Название дня</span><input class="coach-day-title" maxlength="128" value="День ${$('programDays').children.length + 1}" /></label>
    <button class="btn-danger remove-program-day" type="button">Удалить день</button></div>
    <div class="stack coach-day-exercises"></div><div class="toolbar top-gap"><button class="secondary add-program-exercise" type="button">Добавить упражнение</button></div>`;
  $('programDays').appendChild(day);
  addExerciseRow(day.querySelector('.coach-day-exercises'));
}

function collectProgram() {
  const days = [...document.querySelectorAll('.coach-program-day')].map((day) => ({
    title: day.querySelector('.coach-day-title').value.trim() || 'День',
    exercises: [...day.querySelectorAll('.coach-program-exercise')].map((row) => ({
      exercise_id: Number(row.querySelector('.coach-exercise-id').value),
      prescribed_sets: Number(row.querySelector('.coach-exercise-sets').value),
      prescribed_reps: row.querySelector('.coach-exercise-reps').value.trim(),
      rest_seconds: Number(row.querySelector('.coach-exercise-rest').value), notes: null,
    })),
  }));
  if (!days.length || days.some((day) => !day.exercises.length || day.exercises.some((exercise) => !exercise.exercise_id))) {
    throw new Error('Добавьте день и выберите упражнение в каждой строке');
  }
  return {
    title: $('programTitle').value.trim() || 'Персональная программа', goal: $('programGoal').value,
    level: $('programLevel').value, mode: 'coach', target_telegram_user_id: state.selectedClient.telegram_user_id,
    target_full_name: displayName(state.selectedClient), days, assign_after_create: true,
  };
}

async function saveProgram() {
  const result = await api('/api/v1/programs/templates', { method: 'POST', body: JSON.stringify(collectProgram()) });
  showToast(`Программа назначена: создано тренировок — ${result.workouts_created}`);
  state.templates = await api('/api/v1/programs/templates/mine');
  syncTemplateOptions();
}

async function createClientExercise() {
  const title = $('customExerciseTitle').value.trim();
  if (!title) throw new Error('Укажите название упражнения');
  await api('/api/v1/programs/exercises', { method: 'POST', body: JSON.stringify({
    title, primary_muscle: $('customExerciseMuscle').value.trim() || null,
    equipment: $('customExerciseEquipment').value.trim() || null,
    target_telegram_user_id: state.selectedClient.telegram_user_id,
  }) });
  ['customExerciseTitle', 'customExerciseMuscle', 'customExerciseEquipment'].forEach((id) => { $(id).value = ''; });
  state.exercises = await api('/api/v1/programs/exercises');
  refreshExerciseSelects();
  showToast('Персональное упражнение добавлено клиенту');
}

async function assignTemplate() {
  const templateId = Number($('templateSelect').value);
  if (!templateId) throw new Error('Выберите шаблон программы');
  const result = await api(`/api/v1/coach/clients/${state.selectedClient.id}/templates/${templateId}/assign`, {
    method: 'POST', body: JSON.stringify({ start_date: $('templateStartDate').value || null }),
  });
  showToast(`Шаблон назначен: создано тренировок — ${result.workouts_created}`);
}

async function run(action, fallback) {
  try { await action(); } catch (error) { log(error); showToast(error.message || fallback, 'error'); }
}

$('addClientBtn').onclick = () => run(addClient, 'Не удалось добавить клиента');
$('reloadClientsBtn').onclick = () => run(loadClients, 'Не удалось загрузить клиентов');
$('clientSearch').oninput = renderClients;
$('clientSelect').onchange = () => $('clientSelect').value && run(() => openClient($('clientSelect').value), 'Не удалось открыть клиента');
$('closeClientDetailBtn').onclick = () => $('coachClientDetail').classList.add('hidden');
$('saveClientProfileBtn').onclick = () => run(saveProfile, 'Не удалось сохранить анкету');
$('saveMeasurementBtn').onclick = () => run(saveMeasurement, 'Не удалось сохранить замер');
$('calculateKbjuBtn').onclick = () => run(async () => { calculateNutrition(); }, 'Не удалось рассчитать КБЖУ');
$('saveKbjuBtn').onclick = () => run(saveNutrition, 'Не удалось назначить КБЖУ');
[
  'kbjuSex', 'kbjuWeight', 'kbjuHeight', 'kbjuAge', 'kbjuDailyActivity', 'kbjuStrength',
  'kbjuStrengthDuration', 'kbjuCardio', 'kbjuCardioDuration', 'kbjuCardioIntensity', 'kbjuGoal',
].forEach((id) => {
  $(id).addEventListener('input', updateNutritionPreview);
  $(id).addEventListener('change', updateNutritionPreview);
});
$('addProgramDayBtn').onclick = addProgramDay;
$('saveClientProgramBtn').onclick = () => run(saveProgram, 'Не удалось назначить программу');
$('createClientExerciseBtn').onclick = () => run(createClientExercise, 'Не удалось добавить упражнение');
$('assignTemplateBtn').onclick = () => run(assignTemplate, 'Не удалось назначить шаблон');

$('coachClientsList').onclick = (event) => {
  const open = event.target.closest('[data-open-client]');
  if (open) return run(() => openClient(open.dataset.openClient), 'Не удалось открыть клиента');
  const remove = event.target.closest('[data-remove-client]');
  if (!remove) return;
  run(async () => {
    const confirmed = await openConfirmDialog({ title: 'Удалить клиента?', message: 'Аккаунт, программа и история тренировок сохранятся.', okText: 'Удалить', danger: true });
    if (!confirmed) return;
    const path = remove.dataset.pending === 'true'
      ? `/api/v1/coach/client-invites/id/${remove.dataset.inviteId}`
      : `/api/v1/coach/clients/${remove.dataset.removeClient}`;
    await api(path, { method: 'DELETE' });
    if (state.selectedClient?.id === Number(remove.dataset.removeClient)) {
      state.selectedClient = null; $('coachClientDetail').classList.add('hidden');
    }
    await loadClients(); showToast('Клиент удалён из списка');
  }, 'Не удалось удалить клиента');
};

$('clientMeasurements').onclick = (event) => {
  const button = event.target.closest('[data-delete-measurement]');
  if (!button) return;
  run(async () => {
    const confirmed = await openConfirmDialog({ title: 'Удалить замер?', message: 'Эту запись нельзя будет восстановить.', okText: 'Удалить', danger: true });
    if (!confirmed) return;
    await api(`/api/v1/coach/clients/${state.selectedClient.id}/measurements/${button.dataset.deleteMeasurement}`, { method: 'DELETE' });
    await loadMeasurements(); showToast('Замер удалён');
  }, 'Не удалось удалить замер');
};

$('programDays').onclick = (event) => {
  const add = event.target.closest('.add-program-exercise');
  if (add) return addExerciseRow(add.closest('.coach-program-day').querySelector('.coach-day-exercises'));
  const removeExercise = event.target.closest('.remove-program-exercise');
  if (removeExercise) return removeExercise.closest('.coach-program-exercise').remove();
  const removeDay = event.target.closest('.remove-program-day');
  if (removeDay) removeDay.closest('.coach-program-day').remove();
};

if (new URLSearchParams(location.search).get('debug') === '1') $('coachDiagnosticCard').classList.remove('hidden');
$('measurementDate').value = todayIso();
$('templateStartDate').value = todayIso();

run(async () => {
  await ensureCoachAccess();
  [state.exercises, state.templates, state.clients] = await Promise.all([
    api('/api/v1/programs/exercises'), api('/api/v1/programs/templates/mine'), api('/api/v1/coach/clients'),
  ]);
  renderClients();
  addProgramDay();
}, 'Не удалось загрузить кабинет тренера');
