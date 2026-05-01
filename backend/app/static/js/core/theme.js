export function getTelegramWebApp() {
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

function reportThemeError(error, onError) {
  if (typeof onError === 'function') onError(error);
}

export function hapticImpact(style = 'light') {
  try {
    getTelegramWebApp()?.HapticFeedback?.impactOccurred?.(style);
  } catch {
    /* Telegram haptics may be unavailable outside the mini app. */
  }
}

export function hapticNotification(type = 'success') {
  try {
    getTelegramWebApp()?.HapticFeedback?.notificationOccurred?.(type);
  } catch {
    /* Telegram haptics may be unavailable outside the mini app. */
  }
}

export function applyTelegramTheme({ onError } = {}) {
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
  const accentHover = mixHexColors(
    accentColor,
    colorScheme === 'light' ? '#000000' : '#ffffff',
    colorScheme === 'light' ? 0.14 : 0.1
  );
  const accentSoft = rgbaFromHexColor(accentColor, colorScheme === 'light' ? 0.12 : 0.14);
  const accentLine = rgbaFromHexColor(accentColor, colorScheme === 'light' ? 0.24 : 0.28);
  const accentEnd = mixHexColors(accentColor, '#ffffff', 0.42);

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
    reportThemeError(error, onError);
  }
}

export function initTelegramTheme({ onError, ready = true, expand = true } = {}) {
  const handleThemeChanged = () => applyTelegramTheme({ onError });
  const tg = getTelegramWebApp();

  handleThemeChanged();

  if (!tg) return null;

  try {
    tg.onEvent?.('themeChanged', handleThemeChanged);
    if (ready) tg.ready?.();
    if (expand) tg.expand?.();
  } catch (error) {
    reportThemeError(error, onError);
  }

  return tg;
}
