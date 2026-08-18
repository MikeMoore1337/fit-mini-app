export type AppColorScheme = 'light' | 'dark';
export type ThemePreference = 'system' | AppColorScheme;
export type ThemeSource = 'web' | 'telegram' | 'telegram-fallback';

export const APP_THEME_STORAGE_KEY = 'app-theme';
export const LEGACY_LANDING_THEME_STORAGE_KEY = 'landing-theme';
export const APP_THEME_CHANGE_EVENT = 'yfc-theme-preference-change';

export const YFC_THEME_COLORS = {
  light: {
    background: '#f1f3ec',
    header: '#f7f9f3',
    bottomBar: '#f7f9f3',
  },
  dark: {
    background: '#0d120f',
    header: '#111813',
    bottomBar: '#111813',
  },
} as const satisfies Record<AppColorScheme, Record<string, string>>;

let runtimeThemePreference: ThemePreference | null = null;

function isThemePreference(value: string | null): value is ThemePreference {
  return value === 'system' || value === 'light' || value === 'dark';
}

export function storedAppThemePreference(): ThemePreference {
  if (runtimeThemePreference) return runtimeThemePreference;
  try {
    const stored = window.localStorage.getItem(APP_THEME_STORAGE_KEY);
    if (isThemePreference(stored)) return stored;

    const legacyLandingTheme = window.localStorage.getItem(LEGACY_LANDING_THEME_STORAGE_KEY);
    return isThemePreference(legacyLandingTheme) ? legacyLandingTheme : 'system';
  } catch {
    return runtimeThemePreference ?? 'system';
  }
}

export function browserAppTheme(
  preference: ThemePreference = storedAppThemePreference(),
): AppColorScheme {
  if (preference !== 'system') return preference;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function saveAppThemePreference(preference: ThemePreference): void {
  runtimeThemePreference = preference;
  try {
    window.localStorage.setItem(APP_THEME_STORAGE_KEY, preference);
    window.localStorage.removeItem(LEGACY_LANDING_THEME_STORAGE_KEY);
    runtimeThemePreference = null;
  } catch {
    // Runtime theme switching still works when browser storage is unavailable.
  }
  window.dispatchEvent(new CustomEvent(APP_THEME_CHANGE_EVENT));
}

export function applyColorScheme(theme: AppColorScheme, source: ThemeSource = 'web'): void {
  const root = document.documentElement;
  root.dataset.colorScheme = theme;
  root.dataset.themeSource = source;
  if (source === 'web') root.dataset.themePreference = storedAppThemePreference();
  else delete root.dataset.themePreference;

  const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (meta) meta.content = YFC_THEME_COLORS[theme].background;
}

export function applyWebTheme(): AppColorScheme {
  const theme = browserAppTheme();
  applyColorScheme(theme, 'web');
  return theme;
}
