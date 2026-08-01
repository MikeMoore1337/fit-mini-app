import { useEffect, useMemo } from 'react';
import type { TelegramThemeParams, TelegramWebApp } from './types';

function setVar(name: string, value: string | undefined): void {
  if (value) document.documentElement.style.setProperty(name, value);
}

function applyTheme(tg: TelegramWebApp | null): void {
  const params: TelegramThemeParams = tg?.themeParams ?? {};
  const root = document.documentElement;
  root.dataset.colorScheme =
    tg?.colorScheme ??
    (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');

  setVar('--bg', params.bg_color);
  setVar('--page-bg', params.bg_color);
  setVar('--bg-elev', params.secondary_bg_color ?? params.section_bg_color);
  setVar('--card', params.section_bg_color ?? params.secondary_bg_color ?? params.bg_color);
  setVar('--card-bg', params.section_bg_color ?? params.secondary_bg_color ?? params.bg_color);
  setVar('--text', params.text_color);
  setVar('--muted', params.hint_color ?? params.subtitle_text_color);
  setVar('--accent', params.button_color ?? params.accent_text_color ?? params.link_color);
  setVar('--button-text', params.button_text_color);
  setVar('--link-color', params.link_color ?? params.accent_text_color);
  setVar('--nav-bg', params.bottom_bar_bg_color ?? params.secondary_bg_color);
  setVar('--danger', params.destructive_text_color);

  const color = params.header_bg_color ?? params.bg_color;
  const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (color) meta?.setAttribute('content', color);
  try {
    if (color) tg?.setHeaderColor(color);
    if (params.bg_color) tg?.setBackgroundColor(params.bg_color);
    if (params.bottom_bar_bg_color) tg?.setBottomBarColor(params.bottom_bar_bg_color);
  } catch {
    // Older Telegram clients may not implement every color method.
  }
}

export function useTelegram(): TelegramWebApp | null {
  const telegram = useMemo(() => window.Telegram?.WebApp ?? null, []);
  useEffect(() => {
    const onTheme = () => applyTheme(telegram);
    onTheme();
    if (!telegram) return;
    telegram.onEvent?.('themeChanged', onTheme);
    telegram.ready?.();
    telegram.expand?.();
    return () => telegram.offEvent?.('themeChanged', onTheme);
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
