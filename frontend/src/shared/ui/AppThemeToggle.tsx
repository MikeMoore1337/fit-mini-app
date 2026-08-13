import { useEffect, useState } from 'react';
import {
  APP_THEME_STORAGE_KEY,
  applyColorScheme,
  browserAppTheme,
  saveAppTheme,
  type AppColorScheme,
} from '../theme';
import { ThemeIcon } from './ThemeIcon';

export function AppThemeToggle({ navigation = false }: { navigation?: boolean }) {
  const [theme, setTheme] = useState<AppColorScheme>(browserAppTheme);
  const isTelegramMiniApp = Boolean(window.Telegram?.WebApp?.initData);

  useEffect(() => {
    if (isTelegramMiniApp) return;

    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    const syncTheme = () => {
      const nextTheme = browserAppTheme();
      setTheme(nextTheme);
      applyColorScheme(nextTheme);
    };
    const onStorage = (event: StorageEvent) => {
      if (event.key === APP_THEME_STORAGE_KEY) syncTheme();
    };

    syncTheme();
    media?.addEventListener?.('change', syncTheme);
    window.addEventListener('storage', onStorage);
    return () => {
      media?.removeEventListener?.('change', syncTheme);
      window.removeEventListener('storage', onStorage);
    };
  }, [isTelegramMiniApp]);

  if (isTelegramMiniApp) return null;

  const toggleTheme = () => {
    const nextTheme: AppColorScheme = theme === 'dark' ? 'light' : 'dark';
    saveAppTheme(nextTheme);
    setTheme(nextTheme);
    applyColorScheme(nextTheme);
  };
  const actionLabel = theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему';

  return (
    <button
      type="button"
      className={navigation ? 'app-bottom-nav__btn app-theme-toggle--nav' : 'app-theme-toggle'}
      aria-label={actionLabel}
      title={actionLabel}
      onClick={toggleTheme}
    >
      <span
        className={navigation ? 'app-bottom-nav__icon' : 'app-theme-toggle__icon'}
        aria-hidden="true"
      >
        <ThemeIcon theme={theme} />
      </span>
      {navigation && (
        <span className="app-bottom-nav__label">{theme === 'dark' ? 'Светлая' : 'Тёмная'}</span>
      )}
    </button>
  );
}
