import type {
  TelegramInsets,
  TelegramThemeParams,
  TelegramWebApp,
} from '../../src/shared/telegram/types';

type TelegramEventHandler = (payload?: { isStateStable: boolean }) => void;

export interface TelegramMockOptions {
  initData?: string;
  version?: string;
  platform?: string;
  colorScheme?: 'light' | 'dark';
  isActive?: boolean;
  viewportHeight?: number;
  viewportStableHeight?: number;
  safeAreaInset?: Partial<TelegramInsets>;
  contentSafeAreaInset?: Partial<TelegramInsets>;
}

export interface TelegramMockCalls {
  ready: number;
  expand: number;
  subscribed: string[];
  unsubscribed: string[];
  backButton: { shown: number; hidden: number };
  shellColors: { header: string[]; background: string[]; bottomBar: string[] };
}

export interface TelegramMockController {
  webApp: TelegramWebApp;
  calls: TelegramMockCalls;
  emit(event: string, payload?: { isStateStable: boolean }): void;
  setTheme(colorScheme: 'light' | 'dark', themeParams?: TelegramThemeParams): void;
  setViewport(viewportHeight: number, viewportStableHeight: number, isStateStable?: boolean): void;
  setSafeArea(value: Partial<TelegramInsets>): void;
  setContentSafeArea(value: Partial<TelegramInsets>): void;
  setActive(active: boolean): void;
  clickBack(): void;
}

export function createTelegramMock(options: TelegramMockOptions = {}): TelegramMockController {
  const eventHandlers = new Map<string, Set<TelegramEventHandler>>();
  const calls: TelegramMockCalls = {
    ready: 0,
    expand: 0,
    subscribed: [],
    unsubscribed: [],
    backButton: { shown: 0, hidden: 0 },
    shellColors: { header: [], background: [], bottomBar: [] },
  };
  const emit = (event: string, payload?: { isStateStable: boolean }) => {
    eventHandlers.get(event)?.forEach((handler) => handler(payload));
  };
  const webApp: TelegramWebApp = {
    initData: options.initData ?? 'query_id=test&auth_date=1700000000&hash=test-signature',
    initDataUnsafe: {},
    version: options.version ?? '8.0',
    platform: options.platform ?? 'android',
    colorScheme: options.colorScheme ?? 'light',
    themeParams: {},
    isActive: options.isActive ?? true,
    viewportHeight: options.viewportHeight ?? 844,
    viewportStableHeight: options.viewportStableHeight ?? 844,
    safeAreaInset: options.safeAreaInset ?? { top: 0, right: 0, bottom: 0, left: 0 },
    contentSafeAreaInset: options.contentSafeAreaInset ?? {
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
    },
    BackButton: {
      show() {
        calls.backButton.shown += 1;
      },
      hide() {
        calls.backButton.hidden += 1;
      },
      onClick(callback) {
        const handlers = eventHandlers.get('backButtonClicked') ?? new Set<TelegramEventHandler>();
        handlers.add(callback);
        eventHandlers.set('backButtonClicked', handlers);
      },
      offClick(callback) {
        eventHandlers.get('backButtonClicked')?.delete(callback);
      },
    },
    ready() {
      calls.ready += 1;
    },
    expand() {
      calls.expand += 1;
    },
    onEvent(event, callback) {
      calls.subscribed.push(event);
      const handlers = eventHandlers.get(event) ?? new Set<TelegramEventHandler>();
      handlers.add(callback);
      eventHandlers.set(event, handlers);
    },
    offEvent(event, callback) {
      calls.unsubscribed.push(event);
      eventHandlers.get(event)?.delete(callback);
    },
    setHeaderColor(color) {
      calls.shellColors.header.push(color);
    },
    setBackgroundColor(color) {
      calls.shellColors.background.push(color);
    },
    setBottomBarColor(color) {
      calls.shellColors.bottomBar.push(color);
    },
  };

  return {
    webApp,
    calls,
    emit,
    setTheme(colorScheme, themeParams = {}) {
      webApp.colorScheme = colorScheme;
      webApp.themeParams = themeParams;
      emit('themeChanged');
    },
    setViewport(viewportHeight, viewportStableHeight, isStateStable = true) {
      webApp.viewportHeight = viewportHeight;
      webApp.viewportStableHeight = viewportStableHeight;
      emit('viewportChanged', { isStateStable });
    },
    setSafeArea(value) {
      webApp.safeAreaInset = value;
      emit('safeAreaChanged');
    },
    setContentSafeArea(value) {
      webApp.contentSafeAreaInset = value;
      emit('contentSafeAreaChanged');
    },
    setActive(active) {
      webApp.isActive = active;
      emit(active ? 'activated' : 'deactivated');
    },
    clickBack() {
      emit('backButtonClicked');
    },
  };
}
