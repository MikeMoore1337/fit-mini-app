import { useEffect, useMemo } from 'react';
import { APP_THEME_STORAGE_KEY, applyColorScheme, browserAppTheme } from '../theme';
import type { TelegramThemeParams, TelegramWebApp } from './types';

function setVar(name: string, value: string | undefined): void {
  if (value) document.documentElement.style.setProperty(name, value);
}

function applyTheme(tg: TelegramWebApp | null): void {
  const telegram = tg?.initData ? tg : null;
  const params: TelegramThemeParams = telegram?.themeParams ?? {};
  const colorScheme = telegram?.colorScheme ?? browserAppTheme();
  if (telegram) {
    applyColorScheme(colorScheme, params.header_bg_color ?? params.bg_color);
  } else {
    document.documentElement.dataset.colorScheme = colorScheme;
  }

  setVar('--bg', params.bg_color);
  setVar('--page-bg', params.bg_color);
  setVar('--bg-elev', params.secondary_bg_color ?? params.section_bg_color);
  setVar('--card', params.section_bg_color ?? params.secondary_bg_color ?? params.bg_color);
  setVar('--card-bg', params.section_bg_color ?? params.secondary_bg_color ?? params.bg_color);
  setVar('--text', params.text_color);
  setVar('--muted', params.hint_color ?? params.subtitle_text_color);
  setVar('--nav-bg', params.bottom_bar_bg_color ?? params.secondary_bg_color);
  setVar('--danger', params.destructive_text_color);

  const color = params.header_bg_color ?? params.bg_color;
  try {
    if (color) telegram?.setHeaderColor(color);
    if (params.bg_color) telegram?.setBackgroundColor(params.bg_color);
    if (params.bottom_bar_bg_color) telegram?.setBottomBarColor(params.bottom_bar_bg_color);
  } catch {
    // Older Telegram clients may not implement every color method.
  }
}

export function useTelegram(): TelegramWebApp | null {
  const telegram = useMemo(() => window.Telegram?.WebApp ?? null, []);
  useEffect(() => {
    const onTheme = () => applyTheme(telegram);
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    const onStorage = (event: StorageEvent) => {
      if (event.key === APP_THEME_STORAGE_KEY) onTheme();
    };
    onTheme();
    media?.addEventListener?.('change', onTheme);
    window.addEventListener('storage', onStorage);
    telegram?.onEvent?.('themeChanged', onTheme);
    telegram?.ready?.();
    telegram?.expand?.();
    return () => {
      media?.removeEventListener?.('change', onTheme);
      window.removeEventListener('storage', onStorage);
      telegram?.offEvent?.('themeChanged', onTheme);
    };
  }, [telegram]);
  return telegram;
}

export function haptic(type: 'success' | 'error' | 'warning' = 'success'): void {
  try {
    window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred(type);
  } catch {
    // Haptics are optional outside Telegram.
  }
}
