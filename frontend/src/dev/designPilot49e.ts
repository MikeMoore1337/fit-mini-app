import type { TelegramButton, TelegramWebApp } from '../shared/telegram/types';

const PILOT_ID = '49e';
const DEFAULT_SAFE_AREA = { top: 24, right: 0, bottom: 20, left: 0 } as const;
const DEFAULT_CONTENT_SAFE_AREA = { top: 44, right: 0, bottom: 12, left: 0 } as const;

type TelegramEvent =
  | 'themeChanged'
  | 'viewportChanged'
  | 'safeAreaChanged'
  | 'contentSafeAreaChanged'
  | 'activated'
  | 'deactivated';

type Insets = { top: number; right: number; bottom: number; left: number };

interface PilotTelegramWebApp extends TelegramWebApp {
  version: string;
  platform: string;
  isActive: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  safeAreaInset: Insets;
  contentSafeAreaInset: Insets;
}

interface PilotController {
  emit(event: TelegramEvent): void;
  setActive(active: boolean): void;
  setTheme(theme: 'light' | 'dark'): void;
  setViewport(height: number, stableHeight?: number): void;
}

declare global {
  interface Window {
    __YFC_DESIGN_PILOT_49E__?: PilotController;
  }
}

function boundedNumber(params: URLSearchParams, name: string, fallback: number): number {
  const rawValue = params.get(name);
  if (rawValue === null || rawValue.trim() === '') return fallback;
  const value = Number(rawValue);
  return Number.isFinite(value) ? Math.min(1200, Math.max(0, value)) : fallback;
}

function insetsFromParams(
  params: URLSearchParams,
  prefix: 'pilot_safe' | 'pilot_content_safe',
  fallback: Insets,
): Insets {
  return {
    top: boundedNumber(params, `${prefix}_top`, fallback.top),
    right: boundedNumber(params, `${prefix}_right`, fallback.right),
    bottom: boundedNumber(params, `${prefix}_bottom`, fallback.bottom),
    left: boundedNumber(params, `${prefix}_left`, fallback.left),
  };
}

function applyMockViewport(webApp: PilotTelegramWebApp): void {
  const root = document.documentElement;
  root.style.setProperty('--tg-viewport-height', `${webApp.viewportHeight}px`);
  root.style.setProperty('--tg-viewport-stable-height', `${webApp.viewportStableHeight}px`);

  for (const side of ['top', 'right', 'bottom', 'left'] as const) {
    root.style.setProperty('--tg-safe-area-inset-' + side, `${webApp.safeAreaInset[side]}px`);
    root.style.setProperty(
      '--tg-content-safe-area-inset-' + side,
      `${webApp.contentSafeAreaInset[side]}px`,
    );
  }
}

function pilotButton(kind: 'back' | 'main'): TelegramButton {
  const handlers = new Set<() => void>();
  return {
    show() {
      if (kind === 'back') document.documentElement.dataset.pilotBackButton = 'visible';
    },
    hide() {
      if (kind === 'back') document.documentElement.dataset.pilotBackButton = 'hidden';
    },
    setText() {},
    enable() {},
    disable() {},
    onClick(callback) {
      handlers.add(callback);
    },
    offClick(callback) {
      handlers.delete(callback);
    },
  };
}

function installTelegramMock(params: URLSearchParams): void {
  const listeners = new Map<TelegramEvent, Set<() => void>>();
  const theme = params.get('pilot_theme') === 'dark' ? 'dark' : 'light';
  const viewportHeight = boundedNumber(params, 'pilot_viewport_height', window.innerHeight);
  const stableHeight = boundedNumber(params, 'pilot_stable_height', viewportHeight);
  const root = document.documentElement;

  const webApp: PilotTelegramWebApp = {
    initData: 'query_id=49e-pilot-fixture',
    initDataUnsafe: {},
    version: params.get('tgWebAppVersion') || '8.0',
    platform: params.get('tgWebAppPlatform') || 'android',
    colorScheme: theme,
    themeParams:
      theme === 'dark'
        ? { bg_color: '#101310', secondary_bg_color: '#161916', text_color: '#eef0ea' }
        : { bg_color: '#f4f5f2', secondary_bg_color: '#ffffff', text_color: '#161a17' },
    isActive: true,
    viewportHeight,
    viewportStableHeight: stableHeight,
    safeAreaInset: insetsFromParams(params, 'pilot_safe', DEFAULT_SAFE_AREA),
    contentSafeAreaInset: insetsFromParams(params, 'pilot_content_safe', DEFAULT_CONTENT_SAFE_AREA),
    BackButton: pilotButton('back'),
    MainButton: pilotButton('main'),
    HapticFeedback: {
      impactOccurred() {},
      notificationOccurred() {},
    },
    ready() {
      root.dataset.pilotTelegramReady = 'true';
    },
    expand() {
      root.dataset.pilotTelegramExpanded = 'true';
    },
    onEvent(event, callback) {
      const typedEvent = event as TelegramEvent;
      const callbacks = listeners.get(typedEvent) ?? new Set<() => void>();
      callbacks.add(callback);
      listeners.set(typedEvent, callbacks);
    },
    offEvent(event, callback) {
      listeners.get(event as TelegramEvent)?.delete(callback);
    },
    setHeaderColor(color) {
      root.style.setProperty('--pilot-telegram-header', color);
    },
    setBackgroundColor(color) {
      root.style.setProperty('--pilot-telegram-background', color);
    },
    setBottomBarColor(color) {
      root.style.setProperty('--pilot-telegram-bottom-bar', color);
    },
  };

  const emit = (event: TelegramEvent) => {
    listeners.get(event)?.forEach((callback) => callback());
  };

  window.Telegram = { WebApp: webApp };
  window.__YFC_DESIGN_PILOT_49E__ = {
    emit,
    setActive(active) {
      webApp.isActive = active;
      root.dataset.pilotTelegramActive = String(active);
      emit(active ? 'activated' : 'deactivated');
    },
    setTheme(nextTheme) {
      webApp.colorScheme = nextTheme;
      webApp.themeParams =
        nextTheme === 'dark'
          ? { bg_color: '#101310', secondary_bg_color: '#161916', text_color: '#eef0ea' }
          : { bg_color: '#f4f5f2', secondary_bg_color: '#ffffff', text_color: '#161a17' };
      emit('themeChanged');
    },
    setViewport(height, nextStableHeight = height) {
      webApp.viewportHeight = Math.max(0, height);
      webApp.viewportStableHeight = Math.max(0, nextStableHeight);
      root.dataset.pilotKeyboard = nextStableHeight - height >= 120 ? 'visible' : 'hidden';
      applyMockViewport(webApp);
      emit('viewportChanged');
    },
  };

  root.dataset.pilotSurface = 'tma-mock';
  root.dataset.pilotBackButton = 'hidden';
  root.dataset.pilotKeyboard = stableHeight - viewportHeight >= 120 ? 'visible' : 'hidden';
  root.dataset.pilotTelegramActive = 'true';
  applyMockViewport(webApp);
}

export async function enableDesignPilot49e(): Promise<boolean> {
  if (!import.meta.env.DEV) return false;

  const params = new URLSearchParams(window.location.search);
  if (params.get('design_pilot') !== PILOT_ID) return false;

  document.documentElement.dataset.designPilot = PILOT_ID;
  document.documentElement.dataset.pilotEvidence = 'development-only';
  await import('./designPilot49e.css');

  if (params.get('pilot_surface') === 'tma') installTelegramMock(params);
  else document.documentElement.dataset.pilotSurface = 'mobile-web';
  return true;
}
