import { useEffect, useState } from 'react';
import {
  APP_THEME_CHANGE_EVENT,
  APP_THEME_STORAGE_KEY,
  LEGACY_LANDING_THEME_STORAGE_KEY,
  applyWebTheme,
  browserAppTheme,
  saveAppThemePreference,
  storedAppThemePreference,
  type AppColorScheme,
  type ThemePreference,
} from './theme';

type WebThemeState = {
  preference: ThemePreference;
  colorScheme: AppColorScheme;
};

function currentState(): WebThemeState {
  const preference = storedAppThemePreference();
  return { preference, colorScheme: browserAppTheme(preference) };
}

export function useWebTheme(): WebThemeState & {
  setPreference(preference: ThemePreference): void;
} {
  const [state, setState] = useState<WebThemeState>(currentState);

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    const sync = () => {
      applyWebTheme();
      setState(currentState());
    };
    const onStorage = (event: StorageEvent) => {
      if (
        event.key === APP_THEME_STORAGE_KEY ||
        event.key === LEGACY_LANDING_THEME_STORAGE_KEY ||
        event.key === null
      ) {
        sync();
      }
    };

    sync();
    media?.addEventListener?.('change', sync);
    window.addEventListener('storage', onStorage);
    window.addEventListener(APP_THEME_CHANGE_EVENT, sync);
    return () => {
      media?.removeEventListener?.('change', sync);
      window.removeEventListener('storage', onStorage);
      window.removeEventListener(APP_THEME_CHANGE_EVENT, sync);
    };
  }, []);

  return {
    ...state,
    setPreference(preference) {
      saveAppThemePreference(preference);
      applyWebTheme();
      setState({ preference, colorScheme: browserAppTheme(preference) });
    },
  };
}
