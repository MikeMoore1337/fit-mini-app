export type AppColorScheme = 'light' | 'dark';

export const APP_THEME_STORAGE_KEY = 'app-theme';

export function storedAppTheme(): AppColorScheme | null {
  try {
    const stored = window.localStorage.getItem(APP_THEME_STORAGE_KEY);
    return stored === 'light' || stored === 'dark' ? stored : null;
  } catch {
    return null;
  }
}

export function browserAppTheme(): AppColorScheme {
  const stored = storedAppTheme();
  if (stored) return stored;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function saveAppTheme(theme: AppColorScheme): void {
  try {
    window.localStorage.setItem(APP_THEME_STORAGE_KEY, theme);
  } catch {
    // Theme switching still works when browser storage is unavailable.
  }
}

export function applyColorScheme(theme: AppColorScheme, themeColor?: string): void {
  document.documentElement.dataset.colorScheme = theme;
  const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (meta) meta.content = themeColor ?? (theme === 'dark' ? '#0f1115' : '#ffffff');
}
