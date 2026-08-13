import { useEffect, useMemo } from 'react';
import { APP_THEME_STORAGE_KEY, applyColorScheme, browserAppTheme } from '../theme';
import type { TelegramWebApp } from './types';

function setVar(name: string, value: string | undefined): void {
  if (value) document.documentElement.style.setProperty(name, value);
}

const TELEGRAM_THEME_VARS = [
  '--bg',
  '--page-bg',
  '--bg-elev',
  '--bg-soft',
  '--card',
  '--card-bg',
  '--border',
  '--text',
  '--muted',
  '--field-label',
  '--placeholder',
  '--brand-accent',
  '--brand-accent-hover',
  '--brand-accent-active',
  '--accent',
  '--accent-hover',
  '--accent-soft',
  '--accent-line',
  '--accent-strong',
  '--accent-end',
  '--accent-alt',
  '--accent-alt-soft',
  '--accent-alt-line',
  '--button-text',
  '--link-color',
  '--focus-ring',
  '--surface',
  '--surface-subtle',
  '--surface-soft',
  '--surface-hover',
  '--surface-active',
  '--secondary-bg',
  '--secondary-hover',
  '--segment-bg',
  '--log-bg',
  '--log-text',
  '--metric-bg',
  '--metric-border',
  '--metric-text',
  '--toast-bg',
  '--nav-bg',
  '--modal-backdrop',
  '--shadow',
  '--danger',
  '--danger-button',
  '--danger-hover',
  '--danger-soft',
  '--danger-line',
  '--danger-text',
  '--danger-toast-bg',
  '--danger-toast-text',
] as const;

function mix(color: string, amount: number, base = 'transparent'): string {
  return `color-mix(in srgb, ${color} ${amount}%, ${base})`;
}

function clearTelegramTheme(): void {
  for (const property of TELEGRAM_THEME_VARS) {
    document.documentElement.style.removeProperty(property);
  }
  delete document.documentElement.dataset.appSurface;
}

function applyTelegramTheme(telegram: TelegramWebApp): void {
  const params = telegram.themeParams ?? {};
  const colorScheme = telegram.colorScheme ?? 'light';
  const dark = colorScheme === 'dark';
  const bg = params.bg_color ?? (dark ? '#17212b' : '#ffffff');
  const secondary = params.secondary_bg_color ?? (dark ? '#232e3c' : '#f1f1f1');
  const card = params.section_bg_color ?? secondary;
  const text = params.text_color ?? (dark ? '#f5f5f5' : '#111111');
  const muted = params.subtitle_text_color ?? params.hint_color ?? mix(text, 62, bg);
  const hint = params.hint_color ?? muted;
  const button = params.button_color ?? params.accent_text_color ?? (dark ? '#6ab2f2' : '#2481cc');
  const buttonText = params.button_text_color ?? '#ffffff';
  const link = params.link_color ?? params.accent_text_color ?? button;
  const sectionAccent = params.section_header_text_color ?? params.accent_text_color ?? link;
  const separator = params.section_separator_color ?? mix(text, 16, card);
  const danger = params.destructive_text_color ?? (dark ? '#ff6767' : '#d14e4e');

  document.documentElement.dataset.appSurface = 'telegram';
  applyColorScheme(colorScheme, params.header_bg_color ?? bg);

  setVar('--bg', bg);
  setVar('--page-bg', bg);
  setVar('--bg-elev', secondary);
  setVar('--bg-soft', secondary);
  setVar('--card', card);
  setVar('--card-bg', card);
  setVar('--border', separator);
  setVar('--text', text);
  setVar('--muted', muted);
  setVar('--field-label', muted);
  setVar('--placeholder', hint);
  setVar('--brand-accent', button);
  setVar('--brand-accent-hover', mix(button, 88, text));
  setVar('--brand-accent-active', mix(button, 78, text));
  setVar('--accent', button);
  setVar('--accent-hover', mix(button, 88, text));
  setVar('--accent-soft', mix(button, 14));
  setVar('--accent-line', mix(button, 34));
  setVar('--accent-strong', sectionAccent);
  setVar('--accent-end', sectionAccent);
  setVar('--accent-alt', sectionAccent);
  setVar('--accent-alt-soft', mix(sectionAccent, 12));
  setVar('--accent-alt-line', mix(sectionAccent, 28));
  setVar('--button-text', buttonText);
  setVar('--link-color', link);
  setVar('--focus-ring', button);
  setVar('--surface', mix(text, 3, card));
  setVar('--surface-subtle', mix(text, 2, card));
  setVar('--surface-soft', mix(text, 5, card));
  setVar('--surface-hover', mix(text, 8, card));
  setVar('--surface-active', mix(text, 12, card));
  setVar('--secondary-bg', secondary);
  setVar('--secondary-hover', mix(text, 8, secondary));
  setVar('--segment-bg', secondary);
  setVar('--log-bg', secondary);
  setVar('--log-text', muted);
  setVar('--metric-bg', secondary);
  setVar('--metric-border', separator);
  setVar('--metric-text', text);
  setVar('--toast-bg', card);
  setVar('--nav-bg', params.bottom_bar_bg_color ?? secondary);
  setVar('--modal-backdrop', 'rgba(0, 0, 0, 0.5)');
  setVar('--shadow', dark ? '0 10px 30px rgba(0, 0, 0, 0.28)' : '0 10px 30px rgba(0, 0, 0, 0.12)');
  setVar('--danger', danger);
  setVar('--danger-button', danger);
  setVar('--danger-hover', mix(danger, 84, text));
  setVar('--danger-soft', mix(danger, 14, card));
  setVar('--danger-line', mix(danger, 34));
  setVar('--danger-text', danger);
  setVar('--danger-toast-bg', mix(danger, 18, card));
  setVar('--danger-toast-text', danger);

  try {
    telegram.setHeaderColor(params.header_bg_color ?? bg);
    telegram.setBackgroundColor(bg);
    telegram.setBottomBarColor(params.bottom_bar_bg_color ?? secondary);
  } catch {
    // Older Telegram clients may not implement every color method.
  }
}

function applyTheme(tg: TelegramWebApp | null): void {
  if (tg?.initData) {
    applyTelegramTheme(tg);
    return;
  }

  clearTelegramTheme();
  applyColorScheme(browserAppTheme());
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
