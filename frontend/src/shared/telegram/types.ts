export interface TelegramThemeParams {
  bg_color?: string;
  secondary_bg_color?: string;
  section_bg_color?: string;
  section_separator_color?: string;
  text_color?: string;
  hint_color?: string;
  subtitle_text_color?: string;
  button_color?: string;
  button_text_color?: string;
  link_color?: string;
  accent_text_color?: string;
  section_header_text_color?: string;
  destructive_text_color?: string;
  header_bg_color?: string;
  bottom_bar_bg_color?: string;
}

export interface TelegramBackButton {
  isVisible?: boolean;
  show(): void;
  hide(): void;
  onClick(callback: () => void): void;
  offClick(callback: () => void): void;
}

export interface TelegramButton extends TelegramBackButton {
  setText(text: string): void;
  enable(): void;
  disable(): void;
}

export interface TelegramInsets {
  top: number;
  right: number;
  bottom: number;
  left: number;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: { start_param?: string };
  version?: string;
  platform?: string;
  colorScheme?: 'light' | 'dark';
  themeParams?: TelegramThemeParams;
  isActive?: boolean;
  viewportHeight?: number;
  viewportStableHeight?: number;
  safeAreaInset?: Partial<TelegramInsets>;
  contentSafeAreaInset?: Partial<TelegramInsets>;
  MainButton?: TelegramButton;
  BackButton?: TelegramBackButton;
  HapticFeedback?: {
    impactOccurred(style: string): void;
    notificationOccurred(type: string): void;
  };
  ready?(): void;
  expand?(): void;
  onEvent?(event: string, callback: () => void): void;
  offEvent?(event: string, callback: () => void): void;
  setHeaderColor?(color: string): void;
  setBackgroundColor?(color: string): void;
  setBottomBarColor?(color: string): void;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}
