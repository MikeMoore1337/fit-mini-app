import { API, FRONTEND_VERSION, accessTokenKey, refreshTokenKey } from './core/config.js?v=39';
import { state } from './core/state.js?v=39';
import {
  $,
  log,
  showToast,
  toastError,
  setAppLoading,
  openConfirmDialog,
  bindGlobalNavHandlers,
  expandSectionAndScroll,
  restoreSectionState,
  setSectionCollapsed,
} from './core/ui.js?v=39';
import { api, clearTokens, sleep } from './core/http.js?v=39';

window.__fitMiniAppBoot = {
  ...(window.__fitMiniAppBoot || {}),
  moduleStarted: true,
  frontendVersion: FRONTEND_VERSION,
  moduleStartedAt: new Date().toISOString(),
};

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

function getCurrentTimezone() {
  return state.me?.profile?.timezone || 'Europe/Moscow';
}

function dateTimeLocalToUserTimezoneIso(value) {
  const normalized = String(value || '').trim();
  if (!normalized) return '';
  return normalized.length === 16 ? `${normalized}:00` : normalized;
}

function formatUserDateTime(value, timezone = getCurrentTimezone()) {
  if (!value) return '';
  const raw = String(value);
  const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/.test(raw);
  if (!hasTimezone) {
    const match = raw.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
    if (match) {
      const [, year, month, day, hour, minute] = match;
      return `${day}.${month}.${year}, ${hour}:${minute}`;
    }
  }

  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;

  return new Intl.DateTimeFormat('ru-RU', {
    timeZone: timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function reportFatalStartupError(error) {
  log({
    type: 'startup-fatal',
    reason: String(error),
    stack: error?.stack || null,
  });
  setAppLoading(false);
  setAuthState(`Ошибка запуска интерфейса: ${error?.message || String(error)}`);
  showToast('Ошибка запуска интерфейса', 'error');
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

const strengthTemplateTypeLabels = {
  split: 'Сплит',
  push_pull_legs: 'Тяни-толкай-ноги',
  upper_lower: 'Верх-низ',
  fullbody: 'Фуллбади',
};

const strengthTemplateDayOptions = {
  split: [3, 4, 5, 6],
  push_pull_legs: [3, 4, 5, 6],
  upper_lower: [2, 3, 4],
  fullbody: [2, 3, 4],
};

const strengthWorkoutDayLibrary = {
  splitChestTriceps: {
    title: 'Грудь и трицепс',
    exercises: [
      ['bench-press', 4, '6-8', 150],
      ['incline-dumbbell-press', 4, '8-10', 120],
      ['machine-chest-press', 3, '10-12', 90],
      ['cable-fly', 3, '12-15', 75],
      ['rope-pushdown', 3, '10-12', 75],
    ],
  },
  splitBackBiceps: {
    title: 'Спина и бицепс',
    exercises: [
      ['pull-up', 4, '6-10', 120],
      ['barbell-row', 4, '6-8', 150],
      ['seated-cable-row', 3, '10-12', 90],
      ['lat-pulldown', 3, '10-12', 90],
      ['barbell-curl', 3, '8-10', 90],
    ],
  },
  splitLegsShoulders: {
    title: 'Ноги и плечи',
    exercises: [
      ['squat', 4, '5-8', 180],
      ['romanian-deadlift', 3, '8-10', 150],
      ['leg-press', 3, '10-12', 120],
      ['overhead-press', 3, '6-8', 150],
      ['dumbbell-lateral-raise', 3, '12-15', 60],
    ],
  },
  splitChest: {
    title: 'Грудь',
    exercises: [
      ['bench-press', 4, '6-8', 150],
      ['incline-dumbbell-press', 4, '8-10', 120],
      ['machine-chest-press', 3, '10-12', 90],
      ['cable-fly', 3, '12-15', 75],
      ['weighted-dip', 3, '8-10', 120],
    ],
  },
  splitBack: {
    title: 'Спина',
    exercises: [
      ['pull-up', 4, '6-10', 120],
      ['barbell-row', 4, '6-8', 150],
      ['seated-cable-row', 3, '10-12', 90],
      ['lat-pulldown', 3, '10-12', 90],
      ['straight-arm-pulldown', 3, '12-15', 75],
    ],
  },
  splitLegs: {
    title: 'Ноги',
    exercises: [
      ['squat', 4, '5-8', 180],
      ['leg-press', 4, '10-12', 150],
      ['romanian-deadlift', 3, '8-10', 150],
      ['leg-curl', 3, '10-12', 90],
      ['standing-calf-raise', 4, '12-15', 60],
    ],
  },
  splitShoulders: {
    title: 'Плечи',
    exercises: [
      ['overhead-press', 4, '6-8', 150],
      ['dumbbell-lateral-raise', 4, '12-15', 60],
      ['reverse-pec-deck', 3, '12-15', 75],
      ['face-pull', 3, '12-15', 75],
      ['dumbbell-shrug', 3, '10-12', 90],
    ],
  },
  splitArms: {
    title: 'Руки',
    exercises: [
      ['close-grip-bench-press', 4, '6-8', 150],
      ['barbell-curl', 4, '8-10', 90],
      ['rope-pushdown', 3, '10-12', 75],
      ['hammer-curl', 3, '10-12', 75],
      ['overhead-triceps-extension', 3, '12-15', 75],
    ],
  },
  splitQuads: {
    title: 'Квадрицепс',
    exercises: [
      ['front-squat', 4, '6-8', 150],
      ['hack-squat', 4, '8-10', 150],
      ['bulgarian-split-squat', 3, '8-10', 120],
      ['leg-extension', 3, '12-15', 75],
      ['standing-calf-raise', 4, '12-15', 60],
    ],
  },
  splitHamstringsGlutes: {
    title: 'Бедра и ягодицы',
    exercises: [
      ['romanian-deadlift', 4, '6-8', 150],
      ['hip-thrust', 4, '8-10', 120],
      ['seated-leg-curl', 3, '10-12', 90],
      ['cable-pull-through', 3, '12-15', 75],
      ['seated-calf-raise', 4, '12-15', 60],
    ],
  },
  pushA: {
    title: 'Толкай A',
    exercises: [
      ['bench-press', 4, '5-8', 150],
      ['incline-dumbbell-press', 3, '8-10', 120],
      ['overhead-press', 3, '6-8', 150],
      ['dumbbell-lateral-raise', 3, '12-15', 60],
      ['rope-pushdown', 3, '10-12', 75],
    ],
  },
  pullA: {
    title: 'Тяни A',
    exercises: [
      ['pull-up', 4, '6-10', 120],
      ['barbell-row', 4, '6-8', 150],
      ['lat-pulldown', 3, '10-12', 90],
      ['face-pull', 3, '12-15', 75],
      ['barbell-curl', 3, '8-10', 90],
    ],
  },
  legsA: {
    title: 'Ноги A',
    exercises: [
      ['squat', 4, '5-8', 180],
      ['leg-press', 3, '10-12', 150],
      ['romanian-deadlift', 3, '8-10', 150],
      ['leg-curl', 3, '10-12', 90],
      ['standing-calf-raise', 4, '12-15', 60],
    ],
  },
  pushB: {
    title: 'Толкай B',
    exercises: [
      ['incline-bench-press', 4, '6-8', 150],
      ['machine-chest-press', 3, '10-12', 90],
      ['seated-dumbbell-press', 3, '8-10', 120],
      ['cable-lateral-raise', 3, '12-15', 60],
      ['overhead-triceps-extension', 3, '10-12', 75],
    ],
  },
  pullB: {
    title: 'Тяни B',
    exercises: [
      ['deadlift', 3, '3-5', 180],
      ['chest-supported-row', 4, '8-10', 120],
      ['close-grip-lat-pulldown', 3, '10-12', 90],
      ['rear-delt-fly', 3, '12-15', 75],
      ['hammer-curl', 3, '10-12', 75],
    ],
  },
  legsB: {
    title: 'Ноги B',
    exercises: [
      ['front-squat', 4, '6-8', 150],
      ['bulgarian-split-squat', 3, '8-10', 120],
      ['hip-thrust', 4, '8-10', 120],
      ['leg-extension', 3, '12-15', 75],
      ['seated-calf-raise', 4, '12-15', 60],
    ],
  },
  pplUpperPump: {
    title: 'Верх добор',
    exercises: [
      ['incline-dumbbell-press', 3, '8-10', 120],
      ['seated-cable-row', 3, '10-12', 90],
      ['machine-shoulder-press', 3, '8-10', 120],
      ['dumbbell-lateral-raise', 3, '12-15', 60],
      ['rope-pushdown', 3, '10-12', 75],
      ['hammer-curl', 3, '10-12', 75],
    ],
  },
  upperA: {
    title: 'Верх A',
    exercises: [
      ['bench-press', 4, '5-8', 150],
      ['barbell-row', 4, '6-8', 150],
      ['overhead-press', 3, '6-8', 120],
      ['lat-pulldown', 3, '10-12', 90],
      ['rope-pushdown', 3, '10-12', 75],
      ['barbell-curl', 3, '10-12', 75],
    ],
  },
  lowerA: {
    title: 'Низ A',
    exercises: [
      ['squat', 4, '5-8', 180],
      ['romanian-deadlift', 4, '8-10', 150],
      ['leg-press', 3, '10-12', 120],
      ['leg-curl', 3, '10-12', 90],
      ['standing-calf-raise', 4, '12-15', 60],
    ],
  },
  upperB: {
    title: 'Верх B',
    exercises: [
      ['incline-dumbbell-press', 4, '8-10', 120],
      ['pull-up', 4, '6-10', 120],
      ['seated-dumbbell-press', 3, '8-10', 120],
      ['seated-cable-row', 3, '10-12', 90],
      ['dumbbell-lateral-raise', 3, '12-15', 60],
      ['face-pull', 3, '12-15', 60],
    ],
  },
  lowerB: {
    title: 'Низ B',
    exercises: [
      ['front-squat', 4, '6-8', 150],
      ['hip-thrust', 4, '8-10', 120],
      ['bulgarian-split-squat', 3, '8-10', 120],
      ['seated-leg-curl', 3, '10-12', 90],
      ['seated-calf-raise', 4, '12-15', 60],
    ],
  },
  fullbodyA: {
    title: 'Фуллбади A',
    exercises: [
      ['squat', 4, '6-8', 150],
      ['bench-press', 4, '6-8', 150],
      ['seated-cable-row', 3, '10-12', 90],
      ['romanian-deadlift', 3, '8-10', 120],
      ['plank', 3, '30-60 сек', 60],
    ],
  },
  fullbodyB: {
    title: 'Фуллбади B',
    exercises: [
      ['deadlift', 3, '3-5', 180],
      ['overhead-press', 4, '6-8', 150],
      ['lat-pulldown', 3, '10-12', 90],
      ['leg-press', 3, '10-12', 120],
      ['hanging-leg-raise', 3, '10-15', 60],
    ],
  },
  fullbodyC: {
    title: 'Фуллбади C',
    exercises: [
      ['front-squat', 4, '6-8', 150],
      ['incline-dumbbell-press', 3, '8-10', 120],
      ['barbell-row', 4, '6-8', 150],
      ['hip-thrust', 3, '8-10', 120],
      ['face-pull', 3, '12-15', 60],
    ],
  },
  fullbodyD: {
    title: 'Фуллбади D',
    exercises: [
      ['leg-press', 3, '10-12', 120],
      ['machine-chest-press', 3, '10-12', 90],
      ['chest-supported-row', 3, '10-12', 90],
      ['dumbbell-lateral-raise', 3, '12-15', 60],
      ['cable-crunch', 3, '12-15', 60],
    ],
  },
};

const strengthTemplateSequences = {
  split: {
    3: ['splitChestTriceps', 'splitBackBiceps', 'splitLegsShoulders'],
    4: ['splitChest', 'splitBack', 'splitLegs', 'splitShoulders'],
    5: ['splitChest', 'splitBack', 'splitLegs', 'splitShoulders', 'splitArms'],
    6: ['splitChest', 'splitBack', 'splitQuads', 'splitShoulders', 'splitHamstringsGlutes', 'splitArms'],
  },
  push_pull_legs: {
    3: ['pushA', 'pullA', 'legsA'],
    4: ['pushA', 'pullA', 'legsA', 'pplUpperPump'],
    5: ['pushA', 'pullA', 'legsA', 'pushB', 'pullB'],
    6: ['pushA', 'pullA', 'legsA', 'pushB', 'pullB', 'legsB'],
  },
  upper_lower: {
    2: ['upperA', 'lowerA'],
    3: ['upperA', 'lowerA', 'upperB'],
    4: ['upperA', 'lowerA', 'upperB', 'lowerB'],
  },
  fullbody: {
    2: ['fullbodyA', 'fullbodyB'],
    3: ['fullbodyA', 'fullbodyB', 'fullbodyC'],
    4: ['fullbodyA', 'fullbodyB', 'fullbodyC', 'fullbodyD'],
  },
};

const devRolePresets = {
  user: {
    telegram_user_id: 2001,
    full_name: 'Клиент Демо',
  },
  coach: {
    telegram_user_id: 1002,
    full_name: 'Тренер Демо',
  },
  admin: {
    telegram_user_id: 1001,
    full_name: 'Админ Демо',
  },
};

function getTelegramWebApp() {
  return window.Telegram?.WebApp || null;
}

function getPreferredColorScheme(tg) {
  const scheme = tg?.colorScheme;
  if (scheme === 'light' || scheme === 'dark') return scheme;
  return window.matchMedia?.('(prefers-color-scheme: light)')?.matches ? 'light' : 'dark';
}

function normalizeHexColor(value) {
  const raw = String(value || '').trim();
  if (!raw.startsWith('#')) return null;
  const hex = raw.slice(1);
  if (/^[0-9a-f]{3}$/i.test(hex)) {
    return `#${hex
      .split('')
      .map((char) => `${char}${char}`)
      .join('')}`;
  }
  if (/^[0-9a-f]{6}$/i.test(hex)) return raw;
  return null;
}

function hexToRgb(value) {
  const hex = normalizeHexColor(value);
  if (!hex) return null;
  return {
    r: parseInt(hex.slice(1, 3), 16),
    g: parseInt(hex.slice(3, 5), 16),
    b: parseInt(hex.slice(5, 7), 16),
  };
}

function rgbToHex({ r, g, b }) {
  return `#${[r, g, b]
    .map((channel) => Math.max(0, Math.min(255, Math.round(channel))).toString(16).padStart(2, '0'))
    .join('')}`;
}

function mixHexColors(base, overlay, overlayWeight) {
  const baseRgb = hexToRgb(base);
  const overlayRgb = hexToRgb(overlay);
  if (!baseRgb || !overlayRgb) return '';

  const baseWeight = 1 - overlayWeight;
  return rgbToHex({
    r: baseRgb.r * baseWeight + overlayRgb.r * overlayWeight,
    g: baseRgb.g * baseWeight + overlayRgb.g * overlayWeight,
    b: baseRgb.b * baseWeight + overlayRgb.b * overlayWeight,
  });
}

function rgbaFromHexColor(value, alpha) {
  const rgb = hexToRgb(value);
  if (!rgb) return '';
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
}

function setThemeVar(root, name, value) {
  if (value) root.style.setProperty(name, value);
}

function updateThemeMetaColor(color) {
  if (!color) return;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', color);
}

function hapticImpact(style = 'light') {
  try {
    getTelegramWebApp()?.HapticFeedback?.impactOccurred?.(style);
  } catch {
    /* Виброотклик Telegram может быть недоступен. */
  }
}

function hapticNotification(type = 'success') {
  try {
    getTelegramWebApp()?.HapticFeedback?.notificationOccurred?.(type);
  } catch {
    /* Виброотклик Telegram может быть недоступен. */
  }
}

function applyTelegramTheme() {
  const tg = getTelegramWebApp();
  const params = tg?.themeParams || {};
  const root = document.documentElement;
  const colorScheme = getPreferredColorScheme(tg);
  root.dataset.colorScheme = colorScheme;

  const computedStyle = getComputedStyle(root);
  const fallbackVar = (name) => computedStyle.getPropertyValue(name).trim();
  if (!params || !Object.keys(params).length) {
    updateThemeMetaColor(fallbackVar('--bg'));
    return;
  }

  const bgColor = params.bg_color || fallbackVar('--bg');
  const secondaryBgColor = params.secondary_bg_color || params.section_bg_color || fallbackVar('--bg-elev');
  const cardColor = params.section_bg_color || params.secondary_bg_color || params.bg_color || fallbackVar('--card');
  const textColor = params.text_color || fallbackVar('--text');
  const hintColor = params.hint_color || params.subtitle_text_color || fallbackVar('--muted');
  const accentColor = params.button_color || params.accent_text_color || params.link_color || fallbackVar('--accent');
  const linkColor = params.link_color || params.accent_text_color || accentColor;
  const accentHover = mixHexColors(accentColor, colorScheme === 'light' ? '#000000' : '#ffffff', colorScheme === 'light' ? 0.14 : 0.1);
  const accentSoft = rgbaFromHexColor(accentColor, colorScheme === 'light' ? 0.12 : 0.14);
  const accentLine = rgbaFromHexColor(accentColor, colorScheme === 'light' ? 0.24 : 0.28);
  const accentEnd = mixHexColors(accentColor, colorScheme === 'light' ? '#ffffff' : '#ffffff', 0.42);

  setThemeVar(root, '--bg', bgColor);
  setThemeVar(root, '--bg-elev', secondaryBgColor);
  setThemeVar(root, '--bg-soft', secondaryBgColor);
  setThemeVar(root, '--page-bg', bgColor);
  setThemeVar(root, '--card', cardColor);
  setThemeVar(root, '--card-bg', cardColor);
  setThemeVar(root, '--text', textColor);
  setThemeVar(root, '--muted', hintColor);
  setThemeVar(root, '--field-label', params.section_header_text_color || textColor);
  setThemeVar(root, '--placeholder', hintColor);
  setThemeVar(root, '--accent', accentColor);
  setThemeVar(root, '--accent-hover', accentHover);
  setThemeVar(root, '--accent-soft', accentSoft);
  setThemeVar(root, '--accent-line', accentLine);
  setThemeVar(root, '--accent-strong', linkColor);
  setThemeVar(root, '--accent-end', accentEnd);
  setThemeVar(root, '--accent-alt', linkColor);
  setThemeVar(root, '--accent-alt-soft', rgbaFromHexColor(linkColor, colorScheme === 'light' ? 0.12 : 0.14));
  setThemeVar(root, '--accent-alt-line', rgbaFromHexColor(linkColor, colorScheme === 'light' ? 0.24 : 0.28));
  setThemeVar(root, '--button-text', params.button_text_color || '#ffffff');
  setThemeVar(root, '--link-color', linkColor);
  setThemeVar(root, '--secondary-bg', secondaryBgColor);
  setThemeVar(root, '--segment-bg', secondaryBgColor);
  setThemeVar(root, '--log-bg', secondaryBgColor);
  setThemeVar(root, '--nav-bg', params.bottom_bar_bg_color || secondaryBgColor || bgColor);

  if (params.destructive_text_color) {
    setThemeVar(root, '--danger', params.destructive_text_color);
    setThemeVar(root, '--danger-line', rgbaFromHexColor(params.destructive_text_color, 0.35));
  }

  updateThemeMetaColor(params.header_bg_color || bgColor);

  try {
    tg?.setHeaderColor?.(params.header_bg_color || bgColor);
    tg?.setBackgroundColor?.(bgColor);
    tg?.setBottomBarColor?.(params.bottom_bar_bg_color || secondaryBgColor || bgColor);
  } catch (error) {
    log(`applyTelegramTheme chrome: ${String(error)}`);
  }
}

function setActiveBottomNav(cardId) {
  document.querySelectorAll('.app-bottom-nav__btn').forEach((btn) => {
    btn.classList.toggle('is-active', btn.getAttribute('data-nav-card') === cardId);
  });
}

function navigateToSection(sectionId, cardId) {
  state.currentNavCard = cardId;
  expandSectionAndScroll(sectionId, cardId);
  setActiveBottomNav(cardId);
  syncTelegramChrome();
}

function getMainTelegramButtonTarget() {
  if (state.currentNavCard !== 'card-today' || !state.todayWorkout) return null;
  if (state.todayWorkout.status === 'planned') {
    return { text: 'Начать тренировку', targetId: 'startWorkoutBtn' };
  }
  if (state.todayWorkout.status === 'in_progress') {
    return { text: 'Завершить тренировку', targetId: 'finishWorkoutBtn' };
  }
  return null;
}

function onTelegramMainButtonClick() {
  if (!state.telegramMainButtonTargetId) return;
  document.getElementById(state.telegramMainButtonTargetId)?.click();
}

function syncTelegramChrome() {
  const tg = getTelegramWebApp();
  if (!tg) return;

  const mainButton = tg.MainButton;
  if (mainButton) {
    const target = getMainTelegramButtonTarget();
    if (!state.telegramMainButtonBound) {
      mainButton.onClick(onTelegramMainButtonClick);
      state.telegramMainButtonBound = true;
    }
    if (target) {
      state.telegramMainButtonTargetId = target.targetId;
      mainButton.setText(target.text);
      mainButton.show();
    } else {
      state.telegramMainButtonTargetId = null;
      mainButton.hide();
    }
  }

  const backButton = tg.BackButton;
  if (backButton) {
    if (!state.telegramBackButtonBound) {
      backButton.onClick(() => navigateToSection('section-today-workout', 'card-today'));
      state.telegramBackButtonBound = true;
    }
    if (state.currentNavCard && state.currentNavCard !== 'card-today') {
      backButton.show();
    } else {
      backButton.hide();
    }
  }
}

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

function getTrainerDisplayName(trainer) {
  if (!trainer) return '';
  const username = trainer.username ? `@${trainer.username}` : '';
  const name = trainer.full_name || '';
  return [username, name].filter(Boolean).join(' / ') || `№ ${trainer.telegram_user_id}`;
}

function renderTrainerInfo(trainer) {
  const node = $('trainerInfo');
  if (!node) return;

  if (!trainer) {
    node.classList.add('hidden');
    node.innerHTML = '';
    return;
  }

  const trainerLabel = escapeHtml(getTrainerDisplayName(trainer));
  const chatControl = trainer.can_open_chat && trainer.chat_url
    ? `<a class="button-link" href="${escapeHtml(trainer.chat_url)}" target="_blank" rel="noopener noreferrer">Написать тренеру</a>`
    : `<span class="muted">${escapeHtml(trainer.chat_unavailable_reason || 'Чат с тренером недоступен')}</span>`;

  node.innerHTML = `
    <strong>Ваш тренер: ${trainerLabel}</strong>
    <div class="toolbar wrap top-gap">
      ${chatControl}
      <button id="detachTrainerBtn" class="secondary" type="button">Открепиться</button>
    </div>
  `;
  node.classList.remove('hidden');

  const detachBtn = $('detachTrainerBtn');
  if (detachBtn) {
    detachBtn.onclick = async () => {
      const ok = await openConfirmDialog({
        title: 'Открепиться от тренера?',
        message: 'Тренер больше не сможет видеть и редактировать твои программы и упражнения.',
        okText: 'Открепиться',
        danger: true,
      });
      if (!ok) return;

      try {
        await withReauth(() => api(API.detachTrainer, { method: 'DELETE' }));
        showToast('Тренер откреплён');
        await loadMe();
        await loadExercises();
        await loadTemplates();
      } catch (error) {
        log(`detachTrainer: ${String(error)}`);
        toastError(error, 'Не удалось открепиться от тренера');
      }
    };
  }
}

function getKbjuGoalLabel(goal) {
  return ({
    fat_loss: 'Похудение',
    muscle_gain: 'Набор',
    maintenance: 'Поддержание',
    recomposition: 'Рекомпозиция',
  }[goal] || goal || '-');
}

function getLevelLabel(level) {
  return ({
    beginner: 'Начальный',
    intermediate: 'Средний',
    advanced: 'Продвинутый',
  }[level] || level || '-');
}

function getClientStatusLabel(status) {
  return ({
    pending: 'Ожидает входа',
    active: 'Активен',
  }[status] || status || '-');
}

function getNotificationStatusLabel(status) {
  return ({
    queued: 'Ожидает',
    sent: 'Отправлено',
    failed: 'Ошибка',
  }[status] || status || '-');
}

function getKbjuSexLabel(sex) {
  return sex === 'female' ? 'Женский' : 'Мужской';
}

function getAssignedByLabel(assignedBy) {
  if (!assignedBy) return '';
  const username = assignedBy.username ? `@${assignedBy.username}` : '';
  const name = assignedBy.full_name || '';
  return [username, name].filter(Boolean).join(' / ') || `№ ${assignedBy.telegram_user_id}`;
}

function renderProfileKbju(kbju) {
  const node = $('profileKbju');
  if (!node) return;

  if (!kbju) {
    node.classList.add('hidden');
    node.innerHTML = '';
    return;
  }

  const assignedByLabel = getAssignedByLabel(kbju.assigned_by);
  const savedAt = kbju.saved_at ? `${formatUserDateTime(kbju.saved_at)} ${getCurrentTimezone()}` : '';

  node.innerHTML = `
    <div class="profile-kbju__head">
      <strong>Сохранённый КБЖУ</strong>
      <span class="muted">${escapeHtml(savedAt)}</span>
    </div>
    <div class="kbju-result-grid top-gap">
      <div>
        <span class="muted">Калории</span>
        <strong>${escapeHtml(kbju.calories)} ккал</strong>
      </div>
      <div>
        <span class="muted">Белки</span>
        <strong>${escapeHtml(kbju.protein_g)} г</strong>
      </div>
      <div>
        <span class="muted">Жиры</span>
        <strong>${escapeHtml(kbju.fat_g)} г</strong>
      </div>
      <div>
        <span class="muted">Углеводы</span>
        <strong>${escapeHtml(kbju.carbs_g)} г</strong>
      </div>
      <div>
        <span class="muted">Цель</span>
        <strong>${escapeHtml(getKbjuGoalLabel(kbju.goal))}</strong>
      </div>
    </div>
    <div class="muted top-gap">
      ${escapeHtml(getKbjuSexLabel(kbju.sex))}, ${escapeHtml(kbju.weight_kg)} кг,
      ${escapeHtml(kbju.height_cm)} см, ${escapeHtml(kbju.age)} лет,
      силовые ${escapeHtml(kbju.strength_trainings_per_week)} / кардио ${escapeHtml(kbju.cardio_trainings_per_week)}
      ${assignedByLabel ? ` · назначил ${escapeHtml(assignedByLabel)}` : ''}
    </div>
  `;
  node.classList.remove('hidden');
}

function isProfileReady(profile = {}) {
  return Boolean(
    profile.full_name &&
      profile.goal &&
      profile.level &&
      profile.height_cm &&
      profile.weight_kg &&
      profile.workouts_per_week
  );
}

function getWorkoutSetProgress(workout) {
  const sets = (workout?.exercises || []).flatMap((exercise) => exercise.sets || []);
  const completed = sets.filter((setRow) => setRow.is_completed).length;
  return {
    completed,
    total: sets.length,
    percent: sets.length ? Math.round((completed / sets.length) * 100) : 0,
  };
}

function updateWorkoutProgressFromDom() {
  const inputs = [...document.querySelectorAll('.set-completed')];
  if (!inputs.length) return;
  const completed = inputs.filter((input) => input.checked).length;
  const percent = Math.round((completed / inputs.length) * 100);
  const fill = $('workoutProgressFill');
  const text = $('workoutProgressText');
  if (fill) fill.style.width = `${percent}%`;
  if (text) text.textContent = `Выполнено подходов: ${completed}/${inputs.length}`;
}

function getHistoryStats() {
  const rows = state.historyRows || [];
  const completedThisWeek = rows.filter((item) => isDateInCurrentWeek(item.scheduled_date)).length;
  const totalSets = rows.reduce((sum, item) => sum + Number(item.completed_sets || 0), 0);
  const volume = rows.reduce((sum, item) => sum + Number(item.volume_kg || 0), 0);

  return {
    completedThisWeek,
    totalSets,
    volume,
  };
}

function isDateInCurrentWeek(value) {
  if (!value) return false;
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) return false;
  const now = new Date();
  const day = (now.getDay() + 6) % 7;
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  start.setDate(now.getDate() - day);
  const end = new Date(start);
  end.setDate(start.getDate() + 7);
  return date >= start && date < end;
}

function renderOnboarding() {
  const root = $('onboardingChecklist');
  const card = $('card-onboarding');
  if (!root || !card) return;

  const profile = state.me?.profile || {};
  const steps = [
    {
      done: isProfileReady(profile),
      title: 'Заполнить профиль',
      text: 'Цель, уровень, рост, вес и частота тренировок.',
      section: 'section-profile',
      card: 'card-profile',
      action: 'Открыть профиль',
    },
    {
      done: Boolean(profile.kbju),
      title: 'Рассчитать КБЖУ',
      text: 'Получить целевые калории и макросы.',
      section: 'section-kbju',
      card: 'card-kbju',
      action: 'К расчёту',
    },
    {
      done: Boolean((state.templates || []).length),
      title: 'Создать программу',
      text: 'Собрать шаблон или взять готовый.',
      section: 'section-builder',
      card: 'card-builder',
      action: 'К программе',
    },
    {
      done: Boolean(state.todayWorkout),
      title: 'Назначить тренировку',
      text: 'Тренировка появится на экране «Сегодня».',
      section: 'section-templates',
      card: 'card-templates',
      action: 'К шаблонам',
    },
    {
      done: Boolean((state.historyRows || []).length),
      title: 'Завершить первую тренировку',
      text: 'После завершения здесь появится прогресс.',
      section: 'section-today-workout',
      card: 'card-today',
      action: 'К тренировке',
    },
  ];

  const pending = steps.filter((step) => !step.done);
  if (!pending.length) {
    root.innerHTML = '';
    card.classList.add('hidden');
    return;
  }

  card.classList.remove('hidden');
  root.innerHTML = steps
    .map(
      (step, index) => `
        <div class="onboarding-step ${step.done ? 'is-done' : ''}">
          <span class="onboarding-step__mark">${step.done ? '✓' : index + 1}</span>
          <div>
            <span class="onboarding-step__title">${escapeHtml(step.title)}</span>
            <span class="onboarding-step__text">${escapeHtml(step.text)}</span>
          </div>
          <button
            class="secondary empty-state-goto"
            type="button"
            data-nav-section="${escapeHtml(step.section)}"
            data-nav-card="${escapeHtml(step.card)}"
            ${step.done ? 'disabled' : ''}
          >
            ${step.done ? 'Готово' : escapeHtml(step.action)}
          </button>
        </div>
      `
    )
    .join('');
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

  const coachLink = $('coachLink');
  if (coachLink) coachLink.classList.toggle('hidden', !isCoachOrAdmin());

  const coachFields = $('coachFields');
  const builderMode = $('builder_mode');
  const canAssignClients = isCoachOrAdmin();

  syncBuilderModeOptions(canAssignClients);
  refreshProgramExerciseOptions();

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

  const coachModeBanner = $('coachModeBanner');
  if (coachModeBanner) coachModeBanner.classList.toggle('hidden', !isCoachOrAdmin());

  const diagnosticCard = $('diagnosticCard');
  const logCard = $('logCard');
  if (diagnosticCard) diagnosticCard.classList.toggle('hidden', !isAdmin());
  if (logCard) logCard.classList.toggle('hidden', !isAdmin());

  syncExerciseOwnerOptions();
  syncKbjuTargetOptions();
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
      'Объект Telegram найден': Boolean(window.Telegram),
      'Объект приложения найден': Boolean(tg),
      'Данные входа есть': Boolean(tg?.initData),
      'Длина данных входа': tg?.initData?.length || 0,
      'Небезопасные данные есть': Boolean(tg?.initDataUnsafe),
      'Платформа': tg?.platform || null,
      'Версия': tg?.version || null,
      'Развёрнуто': tg?.isExpanded ?? null,
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

    restoreSectionState(targetId);

    button.onclick = () => {
      const collapsed = !body.classList.contains('hidden');
      setSectionCollapsed(targetId, collapsed);
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
  state.publicConfig = await api(API.publicConfig, { timeoutMs: 4000 });
  const envBadge = $('env-badge');

  if (envBadge && state.publicConfig.app_env === 'dev') {
    envBadge.textContent = 'тест';
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

  setAuthState(`Вход в режиме разработки выполнен: ${body.telegram_user_id}`);
  showToast('Вход в режиме разработки выполнен');
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
      showToast('Telegram не передал данные входа', 'error');
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
    const message = error?.message
      ? `Не удалось войти через Telegram: ${error.message}`
      : 'Не удалось войти через Telegram';
    setAuthState(message);
    showToast(error?.message || 'Не удалось войти через Telegram', 'error');
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

function fillKbjuFormFromUser(user) {
  const profile = user?.profile || {};
  const kbju = profile.kbju || user?.kbju || null;

  if ($('kbjuSex')) $('kbjuSex').value = kbju?.sex || 'male';
  if ($('kbjuWeight')) $('kbjuWeight').value = kbju?.weight_kg ?? profile.weight_kg ?? '';
  if ($('kbjuHeight')) $('kbjuHeight').value = kbju?.height_cm ?? profile.height_cm ?? '';
  if ($('kbjuAge')) $('kbjuAge').value = kbju?.age ?? '';
  if ($('kbjuGoal')) $('kbjuGoal').value = kbju?.goal || profile.goal || 'maintenance';
  if ($('kbjuStrength')) {
    $('kbjuStrength').value =
      kbju?.strength_trainings_per_week ?? profile.workouts_per_week ?? '';
  }
  if ($('kbjuCardio')) $('kbjuCardio').value = kbju?.cardio_trainings_per_week ?? '';

  calculateKbju({ silent: true });
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

  renderProfileKbju(profile.kbju);
  if (!$('kbjuTarget')?.value) {
    fillKbjuFormFromUser(state.me);
  } else {
    calculateKbju({ silent: true });
  }

  renderCurrentAccess(state.me);
  renderTrainerInfo(state.me.trainer);
  setAuthState('Вход выполнен');

  toggleCoachUI();
  syncKbjuTargetOptions();
  renderOnboarding();
  syncTelegramChrome();
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
  renderOnboarding();
}

function parseDecimalInput(value) {
  const normalized = String(value || '').trim().replace(',', '.');
  if (!normalized) return null;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function parseTrainingCount(value) {
  const normalized = String(value || '').trim();
  if (!normalized) return 0;
  const parsed = Number(normalized);
  if (!Number.isInteger(parsed) || parsed < 0) return null;
  return parsed;
}

function roundNumber(value) {
  return Math.max(0, Math.round(value));
}

function getActivityFactor(strengthSessions, cardioSessions) {
  const sessions = strengthSessions + cardioSessions;
  if (sessions <= 0) return 1.2;
  if (sessions <= 2) return 1.375;
  if (sessions <= 4) return 1.55;
  if (sessions <= 6) return 1.725;
  return 1.9;
}

function getGoalCalories(tdee, goal) {
  return roundNumber(tdee * ({
    fat_loss: 0.85,
    muscle_gain: 1.1,
    maintenance: 1,
    recomposition: 0.95,
  }[goal] || 1));
}

function calculateMacros(weightKg, targetCalories, goal) {
  const proteinPerKg = ({
    fat_loss: 2,
    muscle_gain: 1.8,
    maintenance: 1.6,
    recomposition: 2,
  }[goal] || 1.6);
  const fatPerKg = goal === 'muscle_gain' ? 0.9 : 0.8;
  const protein = roundNumber(weightKg * proteinPerKg);
  const fat = roundNumber(weightKg * fatPerKg);
  const carbs = roundNumber((targetCalories - protein * 4 - fat * 9) / 4);

  return { protein, fat, carbs };
}

function calculateKbju({ silent = false } = {}) {
  const result = $('kbjuResult');
  if (!result) return;

  const sex = $('kbjuSex')?.value || 'male';
  const weight = parseDecimalInput($('kbjuWeight')?.value);
  const height = parseDecimalInput($('kbjuHeight')?.value);
  const age = parseDecimalInput($('kbjuAge')?.value);
  const strength = parseTrainingCount($('kbjuStrength')?.value);
  const cardio = parseTrainingCount($('kbjuCardio')?.value);
  const goal = $('kbjuGoal')?.value || 'maintenance';

  if (!weight || !height || !age || strength == null || cardio == null) {
    state.currentKbjuResult = null;
    if (!silent) {
      result.classList.remove('hidden');
      result.innerHTML = '<div class="item-card muted">Заполни вес, рост, возраст и тренировки.</div>';
    } else {
      result.classList.add('hidden');
      result.innerHTML = '';
    }
    return null;
  }

  const sexConstant = sex === 'female' ? -161 : 5;
  const bmr = 10 * weight + 6.25 * height - 5 * age + sexConstant;
  const tdee = bmr * getActivityFactor(strength, cardio);
  const targetCalories = getGoalCalories(tdee, goal);
  const macros = calculateMacros(weight, targetCalories, goal);
  const calculation = {
    sex,
    weight_kg: weight,
    height_cm: height,
    age,
    strength_trainings_per_week: strength,
    cardio_trainings_per_week: cardio,
    goal,
    bmr: roundNumber(bmr),
    tdee: roundNumber(tdee),
    calories: targetCalories,
    protein_g: macros.protein,
    fat_g: macros.fat,
    carbs_g: macros.carbs,
  };

  state.currentKbjuResult = calculation;

  result.classList.remove('hidden');
  result.innerHTML = `
    <div class="kbju-result-grid">
      <div class="item-card">
        <span class="muted">Целевые калории</span>
        <strong>${targetCalories} ккал</strong>
      </div>
      <div class="item-card">
        <span class="muted">Белки</span>
        <strong>${macros.protein} г</strong>
      </div>
      <div class="item-card">
        <span class="muted">Жиры</span>
        <strong>${macros.fat} г</strong>
      </div>
      <div class="item-card">
        <span class="muted">Углеводы</span>
        <strong>${macros.carbs} г</strong>
      </div>
    </div>
    <details class="nutrition-details top-gap">
      <summary>Подробнее о расчёте</summary>
      <div class="muted top-gap">
        Основной обмен: ${roundNumber(bmr)} ккал. Активность и цель уже учтены в целевых калориях.
      </div>
    </details>
  `;
  return calculation;
}

function buildKbjuSavePayload() {
  const calculation = calculateKbju({ silent: false });
  if (!calculation) return null;

  const targetTelegramUserId = $('kbjuTarget')?.value || '';
  return {
    target_telegram_user_id: targetTelegramUserId ? Number(targetTelegramUserId) : null,
    sex: calculation.sex,
    weight_kg: calculation.weight_kg,
    height_cm: calculation.height_cm,
    age: calculation.age,
    strength_trainings_per_week: calculation.strength_trainings_per_week,
    cardio_trainings_per_week: calculation.cardio_trainings_per_week,
    goal: calculation.goal,
  };
}

async function saveKbju() {
  const payload = buildKbjuSavePayload();
  if (!payload) return;

  await withReauth(() =>
    api(API.saveNutritionTarget, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  );

  showToast(payload.target_telegram_user_id ? 'КБЖУ назначен клиенту' : 'КБЖУ сохранён');
  if (payload.target_telegram_user_id) {
    await loadClients();
  } else {
    await loadMe();
  }
}

async function loadExercises() {
  state.exercises = await withReauth(() => api(API.exercises));
  renderExerciseCatalog();
  refreshProgramExerciseOptions();
}

function normalizeCatalogSearch(value) {
  return String(value || '').trim().toLowerCase().replace(/ё/g, 'е');
}

function getExerciseCatalogBadgeLabel(exercise) {
  if (!exercise.is_custom) return 'Общее';
  if (exercise.created_by_user_id === state.me?.id) return 'Моё упражнение';

  const client = getActiveClients().find((item) => item.id === exercise.created_by_user_id);
  if (client) return 'Упражнение клиента';

  return 'Личное упражнение';
}

function getExerciseSearchText(exercise) {
  return normalizeCatalogSearch(
    [
      exercise.title,
      exercise.primary_muscle,
      exercise.equipment,
      getExerciseOwnerLabel(exercise),
      getExerciseCatalogBadgeLabel(exercise),
      exercise.is_custom ? 'личное' : '',
      exercise.is_personalized ? 'моё изменение' : '',
    ].join(' ')
  );
}

function getFilteredExerciseCatalogRows() {
  const query = normalizeCatalogSearch($('exerciseSearch')?.value);
  if (!query) return state.exercises;

  const terms = query.split(/\s+/).filter(Boolean);
  return state.exercises.filter((exercise) => {
    const searchable = getExerciseSearchText(exercise);
    return terms.every((term) => searchable.includes(term));
  });
}

function renderExerciseCatalog() {
  const list = $('exerciseCatalogList');
  if (!list) return;
  const summary = $('exerciseSearchSummary');
  const query = normalizeCatalogSearch($('exerciseSearch')?.value);

  if (!state.exercises.length) {
    if (summary) summary.textContent = '';
    list.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__title">Упражнений пока нет</p>
        <p class="empty-state__text muted">
          Добавь своё упражнение ниже или перезагрузи список — стандартный набор подтягивается с сервера.
        </p>
      </div>`;
    return;
  }

  const rows = getFilteredExerciseCatalogRows();
  if (summary) {
    summary.textContent = query
      ? `Найдено: ${rows.length} из ${state.exercises.length}`
      : `Всего упражнений: ${state.exercises.length}`;
  }

  if (!rows.length) {
    list.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__title">Ничего не найдено</p>
        <p class="empty-state__text muted">
          Попробуй другое название, мышечную группу или оборудование.
        </p>
      </div>`;
    return;
  }

  list.innerHTML = rows
    .map((ex) => {
      const metadata = [
        ex.primary_muscle ? `<span class="metric-pill">${escapeHtml(ex.primary_muscle)}</span>` : '',
        ex.equipment ? `<span class="metric-pill">${escapeHtml(ex.equipment)}</span>` : '',
        `<span class="metric-pill">${escapeHtml(getExerciseOwnerLabel(ex))}</span>`,
        `<span class="metric-pill">${escapeHtml(getExerciseCatalogBadgeLabel(ex))}</span>`,
        ex.is_personalized ? '<span class="metric-pill">Моё изменение</span>' : '',
      ].join('');

      return `
          <div class="item-card">
            <strong>${escapeHtml(ex.title)}</strong>
            <div class="exercise-meta">
              ${metadata}
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
        `;
    })
    .join('');

  document.querySelectorAll('.edit-exercise-btn').forEach((btn) => {
    btn.onclick = async () => {
      const exerciseId = Number(btn.dataset.exerciseId);
      const exercise = state.exercises.find((item) => item.edit_target_id === exerciseId);
      if (!exercise) return;

      const title = prompt('Название упражнения', exercise.title);
      if (title === null) return;

      const primaryMuscle = prompt('Основная мышечная группа', exercise.primary_muscle || '');
      if (primaryMuscle === null) return;

      const equipment = prompt('Оборудование', exercise.equipment || '');
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
      const exercise = state.exercises.find((item) => item.edit_target_id === exerciseId);
      const deletesGlobalExercise = Boolean(
        isAdmin() && exercise && !exercise.created_by_user_id && !exercise.source_exercise_id
      );
      const ok = await openConfirmDialog({
        title: 'Скрыть упражнение?',
        message: deletesGlobalExercise
          ? 'Общее упражнение будет скрыто для всех пользователей.'
          : 'Упражнение будет скрыто только в твоём каталоге. Общие данные не затронуты.',
        okText: deletesGlobalExercise ? 'Скрыть для всех' : 'Скрыть',
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
  const ownerValue = $('exerciseOwner')?.value || '';
  const payload = {
    title: $('newExerciseTitle')?.value?.trim() || '',
    primary_muscle: $('newExerciseMuscle')?.value?.trim() || '',
    equipment: $('newExerciseEquipment')?.value?.trim() || '',
    target_telegram_user_id: ownerValue ? Number(ownerValue) : null,
  };

  if (!payload.title) {
    showToast('Укажи название упражнения', 'error');
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
  if ($('addExerciseDetails')) $('addExerciseDetails').open = false;

  showToast(`Упражнение "${exercise.title}" добавлено`);
  await loadExercises();
}

function getClientByTelegramId(telegramUserId) {
  return getActiveClients().find(
    (client) => String(client.telegram_user_id) === String(telegramUserId)
  );
}

function getBuilderExerciseRows() {
  const mode = getEffectiveBuilderMode();
  if (mode !== 'coach') {
    return state.exercises.filter(
      (exercise) => !exercise.created_by_user_id || exercise.created_by_user_id === state.me?.id
    );
  }

  const targetTelegramId = $('target_telegram_user_id')?.value || '';
  const targetClient = getClientByTelegramId(targetTelegramId);
  return state.exercises.filter(
    (exercise) =>
      !exercise.created_by_user_id ||
      (targetClient && exercise.created_by_user_id === targetClient.id)
  );
}

function exerciseOptions(defaultExerciseId = '') {
  return getBuilderExerciseRows()
    .map(
      (ex) => `<option value="${escapeHtml(ex.id)}" ${String(ex.id) === String(defaultExerciseId) ? 'selected' : ''}>${escapeHtml(ex.title)}</option>`
    )
    .join('');
}

function refreshProgramExerciseOptions() {
  document.querySelectorAll('.exercise-id').forEach((select) => {
    const selectedValue = select.value;
    select.innerHTML = exerciseOptions(selectedValue);
  });
}

function formatDayCountLabel(count) {
  if (count === 1) return '1 день';
  if (count >= 2 && count <= 4) return `${count} дня`;
  return `${count} дней`;
}

function syncStrengthTemplateDayOptions() {
  const typeSelect = $('strengthTemplateType');
  const daysSelect = $('strengthTemplateDays');
  if (!typeSelect || !daysSelect) return;

  const type = typeSelect.value || 'upper_lower';
  const options = strengthTemplateDayOptions[type] || strengthTemplateDayOptions.upper_lower;
  const current = Number(daysSelect.value || options[options.length - 1]);

  daysSelect.innerHTML = options
    .map((count) => `<option value="${count}">${formatDayCountLabel(count)}</option>`)
    .join('');

  daysSelect.value = String(options.includes(current) ? current : options[options.length - 1]);
}

function resolvePresetExerciseId(slug) {
  const rows = getBuilderExerciseRows();
  return rows.find((exercise) => exercise.slug === slug)?.id || null;
}

function buildStrengthTemplatePreset(type, dayCount) {
  const normalizedType = strengthTemplateSequences[type] ? type : 'upper_lower';
  const options = strengthTemplateDayOptions[normalizedType] || strengthTemplateDayOptions.upper_lower;
  const normalizedDayCount = options.includes(dayCount) ? dayCount : options[options.length - 1];
  const sequence = strengthTemplateSequences[normalizedType]?.[normalizedDayCount] || [];
  const label = strengthTemplateTypeLabels[normalizedType] || strengthTemplateTypeLabels.upper_lower;

  return {
    title: `${label} ${formatDayCountLabel(normalizedDayCount)}`,
    days: sequence
      .map((key) => strengthWorkoutDayLibrary[key])
      .filter(Boolean)
      .map((day) => ({
        title: day.title,
        exercises: day.exercises
          .map(([slug, prescribed_sets, prescribed_reps, rest_seconds]) => {
            const exerciseId = resolvePresetExerciseId(slug);
            if (!exerciseId) return null;
            return {
              exercise_id: exerciseId,
              prescribed_sets,
              prescribed_reps,
              rest_seconds,
            };
          })
          .filter(Boolean),
      }))
      .filter((day) => day.exercises.length),
  };
}

function loadStrengthTemplate(type = null, dayCount = null) {
  const dayBuilder = $('dayBuilder');
  if (!dayBuilder) return;

  if (!state.exercises.length) {
    showToast('Сначала должны загрузиться упражнения', 'error');
    return;
  }

  const templateType = type || $('strengthTemplateType')?.value || 'upper_lower';
  const templateDays = Number(dayCount || $('strengthTemplateDays')?.value || 4);
  const preset = buildStrengthTemplatePreset(templateType, templateDays);

  if (!preset.days.length) {
    showToast('Не удалось собрать шаблон из доступных упражнений', 'error');
    return;
  }

  resetBuilderEditMode();
  if ($('program_title')) $('program_title').value = preset.title;
  if ($('program_goal')) $('program_goal').value = 'muscle_gain';
  if ($('program_level')) $('program_level').value = templateType === 'fullbody' ? 'beginner' : 'intermediate';

  dayBuilder.innerHTML = '';
  preset.days.forEach((day) => addDay(day));
  showToast('Силовой шаблон загружен');
}

function exerciseTemplate(defaultExerciseId = '', preset = null) {
  const options = exerciseOptions(defaultExerciseId);
  return `
    <div class="grid item-card program-ex-row" style="grid-template-columns:2fr 1fr 1fr 1fr auto;">
      <label class="field">
        <span>Упражнение</span>
        <select class="exercise-id">${options}</select>
      </label>
      <label class="field">
        <span>Подходы</span>
        <input class="exercise-sets" type="number" min="1" value="${escapeHtml(preset?.prescribed_sets || 3)}" placeholder="3" />
      </label>
      <label class="field">
        <span>Повторы</span>
        <input class="exercise-reps" type="text" value="${escapeHtml(preset?.prescribed_reps || '8-10')}" placeholder="8-10" />
      </label>
      <label class="field">
        <span>Отдых, сек.</span>
        <input class="exercise-rest" type="number" min="15" value="${escapeHtml(preset?.rest_seconds || 90)}" placeholder="90" />
      </label>
      <button class="secondary remove-ex-btn" type="button">Удалить</button>
    </div>
  `;
}

function programDayTemplate(index, preset = null) {
  return `
    <div class="item-card day-card" data-day-index="${index}">
      <div class="toolbar wrap">
        <label class="field day-title-field">
          <span>Название дня</span>
          <input class="day-title" type="text" placeholder="Например, Верх тела" value="${escapeHtml(preset?.title || `День ${index + 1}`)}" />
        </label>
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
  loadStrengthTemplate('upper_lower', 4);
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
  $('builder_mode').value = template.is_public || template.owner_user_id ? 'self' : 'coach';
  if (
    template.owner_user_id &&
    template.owner_user_id !== state.me?.id &&
    template.owner_telegram_user_id
  ) {
    $('builder_mode').value = 'coach';
    if ($('target_telegram_user_id')) {
      $('target_telegram_user_id').value = String(template.owner_telegram_user_id);
    }
    if ($('target_full_name')) {
      $('target_full_name').value = template.owner_full_name || '';
    }
  }

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

function getActiveClients() {
  return (state.clients || []).filter((client) => client.status !== 'pending' && client.telegram_user_id);
}

function getExerciseOwnerLabel(exercise) {
  if (!exercise.created_by_user_id) return 'Для всех';
  if (exercise.created_by_user_id === state.me?.id) return 'Для себя';

  const client = getActiveClients().find((item) => item.id === exercise.created_by_user_id);
  if (client) return `Клиент: ${getClientDisplayName(client)}`;

  return 'Личное';
}

function syncExerciseOwnerOptions() {
  const select = $('exerciseOwner');
  const field = $('exerciseOwnerField');
  if (!select) return;

  if (isAdmin()) {
    select.innerHTML = '<option value="">Для всех</option>';
    select.value = '';
    field?.classList.add('hidden');
    return;
  }

  const clients = getActiveClients();
  select.innerHTML = [
    '<option value="">Для себя</option>',
    ...clients.map(
      (client) =>
        `<option value="${escapeHtml(client.telegram_user_id)}">Клиент: ${escapeHtml(getClientDisplayName(client))}</option>`
    ),
  ].join('');
  field?.classList.toggle('hidden', !isCoachOrAdmin() || !clients.length);
}

function getSelectedKbjuClient() {
  const selectedTelegramId = $('kbjuTarget')?.value || '';
  if (!selectedTelegramId) return null;
  return getActiveClients().find((client) => String(client.telegram_user_id) === selectedTelegramId) || null;
}

function updateSaveKbjuButton() {
  const button = $('saveKbjuBtn');
  if (!button) return;
  button.textContent = getSelectedKbjuClient() ? 'Назначить клиенту' : 'Сохранить КБЖУ';
}

function syncKbjuTargetOptions() {
  const select = $('kbjuTarget');
  const field = $('kbjuTargetField');
  if (!select) return;

  const clients = getActiveClients();
  const currentValue = select.value || '';
  select.innerHTML = [
    '<option value="">Для себя</option>',
    ...clients.map(
      (client) =>
        `<option value="${escapeHtml(client.telegram_user_id)}">Клиент: ${escapeHtml(getClientDisplayName(client))}</option>`
    ),
  ].join('');

  const hasCurrentValue = [...select.options].some((option) => option.value === currentValue);
  select.value = hasCurrentValue ? currentValue : '';
  field?.classList.toggle('hidden', !isCoachOrAdmin() || !clients.length);

  if (currentValue && !hasCurrentValue) {
    fillKbjuFormFromUser(state.me);
  }

  updateSaveKbjuButton();
}

function fillKbjuFormFromSelectedTarget() {
  const selectedClient = getSelectedKbjuClient();
  if (!selectedClient) {
    fillKbjuFormFromUser(state.me);
    updateSaveKbjuButton();
    return;
  }

  fillKbjuFormFromUser({
    profile: {
      kbju: selectedClient.kbju,
      goal: selectedClient.goal,
      height_cm: selectedClient.height_cm,
      weight_kg: selectedClient.weight_kg,
      workouts_per_week: selectedClient.workouts_per_week,
    },
  });
  updateSaveKbjuButton();
}

function selectClientForKbju(client) {
  if (!client.telegram_user_id) {
    showToast('Клиент ещё не привязан к идентификатору Telegram', 'error');
    return;
  }

  syncKbjuTargetOptions();
  if ($('kbjuTarget')) {
    $('kbjuTarget').value = String(client.telegram_user_id);
  }
  fillKbjuFormFromSelectedTarget();
  expandSectionAndScroll('section-kbju', 'card-kbju');
  showToast(`Клиент выбран: ${getClientDisplayName(client)}`);
}

function selectClientForProgram(client) {
  if (!client.telegram_user_id) {
    showToast('Клиент ещё не привязан к идентификатору Telegram', 'error');
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
    showToast('Укажи идентификатор Telegram или имя пользователя клиента', 'error');
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
  renderOnboarding();

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
            <span class="muted">${escapeHtml(getKbjuGoalLabel(template.goal))} · ${escapeHtml(getLevelLabel(template.level))}</span>
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

  if (!isCoachOrAdmin()) {
    state.clients = [];
    syncExerciseOwnerOptions();
    syncKbjuTargetOptions();
    return;
  }

  const rows = await withReauth(() => api(API.clients));
  state.clients = rows;
  syncExerciseOwnerOptions();
  syncKbjuTargetOptions();
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
              ${escapeHtml(getClientStatusLabel(c.status))}${isPending ? '' : ` · № ${escapeHtml(c.telegram_user_id)}`}
              ${c.username ? ` | @${escapeHtml(c.username)}` : ''}
              ${!isPending ? ` | цель: ${escapeHtml(getKbjuGoalLabel(c.goal))} | уровень: ${escapeHtml(getLevelLabel(c.level))}` : ''}
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
                    <button
                      class="secondary assign-kbju-client-btn"
                      type="button"
                      data-client='${escapeHtml(JSON.stringify(c))}'
                    >
                      Назначить КБЖУ
                    </button>
                  </div>`
            }
          </div>`;
          }
        )
        .join('')
    : `<div class="empty-state">
        <p class="empty-state__title">Клиентов пока нет</p>
        <p class="empty-state__text muted">Добавь клиента по идентификатору Telegram или имени пользователя.</p>
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

  document.querySelectorAll('.assign-kbju-client-btn').forEach((btn) => {
    btn.onclick = () => {
      try {
        selectClientForKbju(JSON.parse(btn.dataset.client));
      } catch (error) {
        log(`selectClientForKbju: ${String(error)}`);
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

function clearRestTimer() {
  if (state.restTimer) {
    clearInterval(state.restTimer);
    state.restTimer = null;
  }
  state.restTimerEndsAtMs = null;
  const timerNode = $('restTimer');
  if (timerNode) {
    timerNode.classList.add('hidden');
    timerNode.textContent = '';
  }
}

function startRestTimer(seconds) {
  const durationMs = Math.max(0, Number(seconds || 0)) * 1000;
  const timerNode = $('restTimer');
  if (!timerNode || !durationMs) return;

  clearRestTimer();
  state.restTimerEndsAtMs = Date.now() + durationMs;
  timerNode.classList.remove('hidden');

  const render = () => {
    const remainingMs = Math.max(0, state.restTimerEndsAtMs - Date.now());
    timerNode.textContent = remainingMs
      ? `Отдых: ${formatDurationMs(remainingMs)}`
      : 'Отдых завершён';
    if (!remainingMs) {
      clearInterval(state.restTimer);
      state.restTimer = null;
      hapticNotification('success');
    }
  };

  render();
  state.restTimer = setInterval(render, 1000);
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
    clearRestTimer();
    syncTelegramChrome();
    return;
  }

  const progress = getWorkoutSetProgress(workout);
  const totalExercises = (workout.exercises || []).length;
  const deleteBtn = `<button id="deleteTodayWorkoutBtn" class="secondary" type="button">Удалить тренировку</button>`;

  const actionButtons =
    workout.status === 'planned'
      ? `<button id="startWorkoutBtn" type="button">Начать тренировку</button>${deleteBtn}`
      : workout.status === 'in_progress'
        ? `<button id="finishWorkoutBtn" type="button">Завершить тренировку</button>${deleteBtn}`
        : deleteBtn;
  const setInputsDisabled = workout.status === 'completed' ? 'disabled' : '';

  container.innerHTML = `
    <div class="item-card today-workout-card">
      <div class="workout-hero">
        <div class="workout-hero__top">
          <div>
            <div class="workout-title">${escapeHtml(workout.title)}</div>
            <div class="muted top-gap">День ${escapeHtml(workout.day_number)} · упражнений: ${escapeHtml(totalExercises)}</div>
          </div>
          <span class="workout-status">${escapeHtml(statusLabel(workout.status))}</span>
        </div>
        <div class="workout-progress">
          <div class="workout-progress__bar">
            <div id="workoutProgressFill" class="workout-progress__fill" style="width: ${progress.percent}%"></div>
          </div>
          <div id="workoutProgressText" class="muted">Выполнено подходов: ${progress.completed}/${progress.total}</div>
        </div>
        <div class="workout-telemetry">
          <span id="workoutTimer" class="metric-pill"></span>
          <span id="restTimer" class="rest-timer hidden"></span>
        </div>
      </div>
      <div class="toolbar wrap top-gap">
        ${actionButtons}
      </div>
    </div>

    <div class="stack top-gap">
      ${(workout.exercises || []).map((exercise) => `
        <div class="item-card exercise-workout-card">
          <div class="exercise-workout-card__head">
            <div>
              <div class="exercise-workout-card__title">${escapeHtml(exercise.exercise_title)}</div>
              <div class="muted top-gap">
                План: ${escapeHtml(exercise.prescribed_sets)} × ${escapeHtml(exercise.prescribed_reps)}, отдых ${escapeHtml(exercise.rest_seconds)} сек.
              </div>
            </div>
            <span class="metric-pill">
              ${(exercise.sets || []).filter((setRow) => setRow.is_completed).length}/${(exercise.sets || []).length}
            </span>
          </div>

          <div class="stack top-gap">
            ${(exercise.sets || []).map((setRow) => `
              <div class="set-row ${setRow.is_completed ? 'is-completed' : ''}">
                <div class="set-row__number">Подход ${escapeHtml(setRow.set_number)}</div>
                <label class="field">
                  <span>Повторы</span>
                  <input
                    class="set-reps"
                    type="number"
                    min="0"
                    value="${escapeHtml(setRow.actual_reps ?? '')}"
                    data-set-id="${setRow.id}"
                    placeholder="0"
                    ${setInputsDisabled}
                  />
                </label>
                <label class="field">
                  <span>Вес, кг</span>
                  <input
                    class="set-weight"
                    type="number"
                    min="0"
                    step="0.1"
                    value="${escapeHtml(setRow.actual_weight ?? '')}"
                    data-set-id="${setRow.id}"
                    placeholder="0"
                    ${setInputsDisabled}
                  />
                </label>
                <label class="checkbox-row set-done-label">
                  <input
                    class="set-completed"
                    type="checkbox"
                    data-set-id="${setRow.id}"
                    data-rest-seconds="${escapeHtml(exercise.rest_seconds)}"
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
        hapticNotification('success');
        renderTodayWorkout(state.todayWorkout);
        syncTelegramChrome();
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
        hapticNotification('success');
        renderTodayWorkout(state.todayWorkout);

        const timerNode = $('workoutTimer');
        if (timerNode && localStartMs) {
          timerNode.textContent = `Длительность тренировки: ${formatDurationMs(Date.now() - localStartMs)}`;
        }

        clearWorkoutTimerStart(workout.id);
        clearWorkoutTimer();
        clearRestTimer();
        syncTelegramChrome();
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
        input.closest('.set-row')?.classList.toggle('is-completed', input.checked);
        updateWorkoutProgressFromDom();
        if (input.checked) {
          hapticImpact('medium');
          startRestTimer(input.dataset.restSeconds);
        }
        showToast('Подход сохранён');
      } catch (error) {
        log(`update set completed: ${String(error)}`);
        toastError(error, 'Не удалось сохранить подход');
      }
    });
  });

  syncTelegramChrome();
}

async function loadTodayWorkout() {
  try {
    state.todayWorkout = await withReauth(() => api(API.todayWorkout));
    renderTodayWorkout(state.todayWorkout);
    renderOnboarding();
  } catch (error) {
    if (error.status === 404) {
      state.todayWorkout = null;
    renderTodayWorkout(null);
    renderOnboarding();
    return;
  }

    log(`loadTodayWorkout: ${String(error)}`);
    renderTodayWorkout(null);
    renderOnboarding();
  }
}

function renderWorkoutHistoryRows(rows, append = false) {
  const container = $('workoutHistory');
  if (!container) return;

  container.innerHTML = '';

  if (!rows.length) {
    updateHistoryClearVisibility(false);
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

  updateHistoryClearVisibility(true);
  const stats = getHistoryStats();
  const statsHtml = `
    <div class="progress-overview">
      <div class="progress-card">
        <span>На этой неделе</span>
        <strong>${escapeHtml(stats.completedThisWeek)}</strong>
      </div>
      <div class="progress-card">
        <span>Подходов в истории</span>
        <strong>${escapeHtml(stats.totalSets)}</strong>
      </div>
      <div class="progress-card">
        <span>Общий объём</span>
        <strong>${escapeHtml(Math.round(stats.volume))} кг</strong>
      </div>
    </div>`;

  const html = rows
    .map((item) => `
      <div class="item-card">
        <strong>${escapeHtml(item.title)}</strong><br>
        <span class="muted">${escapeHtml(item.scheduled_date)} · ${statusLabel(item.status)}</span>
        <div class="exercise-meta">
          <span class="metric-pill">Подходов: ${escapeHtml(item.completed_sets || 0)}</span>
          <span class="metric-pill">Объём: ${escapeHtml(Math.round(Number(item.volume_kg || 0)))} кг</span>
        </div>
      </div>
    `)
    .join('');

  container.innerHTML = statsHtml + html;
}

function updateHistoryClearVisibility(visible) {
  const btn = $('clearHistoryBtn');
  if (!btn) return;
  btn.classList.toggle('hidden', !visible);
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
    state.historyRows = rows;
  } else {
    state.historyRows = [...(state.historyRows || []), ...rows];
  }

  renderWorkoutHistoryRows(state.historyRows, false);

  state.historyOffset = offset + rows.length;
  state.historyHasMore = rows.length === state.historyLimit;
  updateHistoryLoadMoreVisibility();
  renderOnboarding();
}

async function resetHistoryAndReload() {
  state.historyOffset = 0;
  state.historyHasMore = true;
  await loadWorkoutHistory(false);
}

async function clearWorkoutHistory() {
  const ok = await openConfirmDialog({
    title: 'Очистить историю?',
    message: 'Будут удалены завершённые тренировки и сохранённые подходы. Текущая незавершённая тренировка останется.',
    okText: 'Очистить',
    danger: true,
  });
  if (!ok) return;

  await withReauth(() =>
    api(API.clearWorkoutHistory, {
      method: 'DELETE',
    })
  );

  showToast('История тренировок очищена');
  await loadTodayWorkout();
  await resetHistoryAndReload();
}

async function loadBilling() {
  try {
    state.plans = await withReauth(() => api(API.billingPlans));
    const subscription = await withReauth(() => api(API.billingSubscription));

    if ($('subscriptionInfo')) {
      $('subscriptionInfo').textContent = subscription
        ? `Активна: ${subscription.plan_title} до ${formatUserDateTime(subscription.ends_at)} ${getCurrentTimezone()}`
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
        scheduled_for: dateTimeLocalToUserTimezoneIso(dateTime),
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
              <span class="muted">${escapeHtml(formatUserDateTime(n.scheduled_for))} ${escapeHtml(getCurrentTimezone())} · ${escapeHtml(getNotificationStatusLabel(n.status))}</span>
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
    await loadClients();
    await loadExercises();
    await loadTemplates();
    await loadTodayWorkout();
    await resetHistoryAndReload();
    await loadNotifications();

    if (!document.querySelector('.day-card')) {
      fillExample();
    }
    renderOnboarding();
    syncTelegramChrome();
    if (!state.initialSectionOpened) {
      state.initialSectionOpened = true;
      requestAnimationFrame(() => navigateToSection('section-today-workout', 'card-today'));
    }
  } finally {
    setAppLoading(false);
  }
}

function bindUI() {
  document.addEventListener('fit:navigation', (event) => {
    const card = event.detail?.card;
    if (!card) return;
    state.currentNavCard = card;
    setActiveBottomNav(card);
    syncTelegramChrome();
  });

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
        toastError(error, 'Не удалось войти в режиме разработки');
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
        toastError(error, 'Не удалось выполнить демо-вход');
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

  if ($('saveKbjuBtn')) {
    $('saveKbjuBtn').onclick = async () => {
      try {
        await saveKbju();
      } catch (error) {
        log(`saveKbju: ${String(error)}`);
        toastError(error, 'Не удалось сохранить КБЖУ');
      }
    };
  }

  if ($('kbjuTarget')) {
    $('kbjuTarget').addEventListener('change', fillKbjuFormFromSelectedTarget);
  }

  [
    'kbjuSex',
    'kbjuWeight',
    'kbjuHeight',
    'kbjuAge',
    'kbjuStrength',
    'kbjuCardio',
    'kbjuGoal',
  ].forEach((id) => {
    const node = $(id);
    if (node) node.addEventListener('input', () => calculateKbju({ silent: true }));
    if (node) node.addEventListener('change', () => calculateKbju({ silent: true }));
  });

  if ($('builder_mode')) {
    $('builder_mode').addEventListener('change', toggleCoachUI);
  }

  if ($('strengthTemplateType')) {
    $('strengthTemplateType').addEventListener('change', syncStrengthTemplateDayOptions);
  }

  if ($('loadStrengthTemplateBtn')) {
    $('loadStrengthTemplateBtn').onclick = () => loadStrengthTemplate();
  }

  syncStrengthTemplateDayOptions();

  if ($('target_telegram_user_id')) {
    $('target_telegram_user_id').addEventListener('input', refreshProgramExerciseOptions);
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

  if ($('exerciseSearch')) {
    $('exerciseSearch').addEventListener('input', renderExerciseCatalog);
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

  if ($('clearHistoryBtn')) {
    $('clearHistoryBtn').onclick = async () => {
      try {
        await clearWorkoutHistory();
      } catch (error) {
        log(`clearHistoryBtn: ${String(error)}`);
        toastError(error, 'Не удалось очистить историю');
      }
    };
  }
}

async function init() {
  window.__fitMiniAppBoot = {
    ...(window.__fitMiniAppBoot || {}),
    initStarted: true,
    initStartedAt: new Date().toISOString(),
  };

  setAuthState('Запускаем интерфейс...');
  bindUI();
  bindGlobalNavHandlers();
  initSectionToggles();
  renderTelegramDebug();

  try {
    setAuthState('Загружаем настройки приложения...');
    await loadEnv();
  } catch (error) {
    log(`loadEnv: ${String(error)}`);
  }

  try {
    const tg = window.Telegram?.WebApp;
    applyTelegramTheme();
    if (tg) {
      tg.onEvent?.('themeChanged', applyTelegramTheme);
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

let initStarted = false;

function startInit() {
  if (initStarted) return;
  initStarted = true;
  init().catch(reportFatalStartupError);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startInit, { once: true });
} else {
  startInit();
}
