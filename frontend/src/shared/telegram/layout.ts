import type { TelegramInsets, TelegramWebApp } from './types';

export interface MobileViewportSnapshot {
  active: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  safeArea: TelegramInsets;
  contentSafeArea: TelegramInsets;
}

const SIDES = ['top', 'right', 'bottom', 'left'] as const;
const LAYOUT_EVENTS = [
  'viewportChanged',
  'safeAreaChanged',
  'contentSafeAreaChanged',
  'activated',
  'deactivated',
] as const;

function boundedMetric(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : fallback;
}

function normalizedInsets(value: Partial<TelegramInsets> | undefined): TelegramInsets {
  return {
    top: boundedMetric(value?.top, 0),
    right: boundedMetric(value?.right, 0),
    bottom: boundedMetric(value?.bottom, 0),
    left: boundedMetric(value?.left, 0),
  };
}

export function readMobileViewportSnapshot(
  telegram: TelegramWebApp | null,
): MobileViewportSnapshot {
  const browserHeight = boundedMetric(window.visualViewport?.height, window.innerHeight);
  const stableFallback = boundedMetric(window.innerHeight, browserHeight);
  const isMiniApp = Boolean(telegram?.initData);
  const viewportHeight = isMiniApp
    ? boundedMetric(telegram?.viewportHeight, browserHeight)
    : browserHeight;

  return {
    active: isMiniApp ? telegram?.isActive !== false : document.visibilityState !== 'hidden',
    viewportHeight,
    viewportStableHeight: isMiniApp
      ? boundedMetric(telegram?.viewportStableHeight, stableFallback)
      : stableFallback,
    safeArea: isMiniApp ? normalizedInsets(telegram?.safeAreaInset) : normalizedInsets(undefined),
    contentSafeArea: isMiniApp
      ? normalizedInsets(telegram?.contentSafeAreaInset)
      : normalizedInsets(undefined),
  };
}

function editableTarget(target: Element | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  if (target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement) return true;
  if (!(target instanceof HTMLInputElement)) return false;
  return ![
    'button',
    'checkbox',
    'color',
    'file',
    'hidden',
    'image',
    'radio',
    'range',
    'reset',
    'submit',
  ].includes(target.type);
}

export function applyMobileViewportSnapshot(
  snapshot: MobileViewportSnapshot,
  telegram: TelegramWebApp | null,
): void {
  const root = document.documentElement;
  root.dataset.yfcViewportActive = String(snapshot.active);
  root.dataset.yfcLayoutSurface = telegram?.initData ? 'telegram' : 'browser';
  root.style.setProperty('--yfc-viewport-height', `${snapshot.viewportHeight}px`);
  root.style.setProperty('--yfc-viewport-stable-height', `${snapshot.viewportStableHeight}px`);

  for (const side of SIDES) {
    root.style.setProperty(`--yfc-tg-safe-${side}`, `${snapshot.safeArea[side]}px`);
    root.style.setProperty(`--yfc-tg-content-safe-${side}`, `${snapshot.contentSafeArea[side]}px`);
  }

  root.dataset.yfcKeyboard = editableTarget(document.activeElement) ? 'visible' : 'hidden';
}

export function installMobileLayoutAdapter(telegram: TelegramWebApp | null): () => void {
  const update = () => applyMobileViewportSnapshot(readMobileViewportSnapshot(telegram), telegram);
  let focusFrame: number | null = null;
  const updateAfterFocus = () => {
    if (focusFrame !== null) window.cancelAnimationFrame(focusFrame);
    focusFrame = window.requestAnimationFrame(() => {
      focusFrame = null;
      update();
    });
  };

  update();
  LAYOUT_EVENTS.forEach((event) => telegram?.onEvent?.(event, update));
  window.visualViewport?.addEventListener('resize', update);
  window.visualViewport?.addEventListener('scroll', update);
  window.addEventListener('resize', update);
  document.addEventListener('visibilitychange', update);
  document.addEventListener('focusin', update);
  document.addEventListener('focusout', updateAfterFocus);

  return () => {
    if (focusFrame !== null) window.cancelAnimationFrame(focusFrame);
    LAYOUT_EVENTS.forEach((event) => telegram?.offEvent?.(event, update));
    window.visualViewport?.removeEventListener('resize', update);
    window.visualViewport?.removeEventListener('scroll', update);
    window.removeEventListener('resize', update);
    document.removeEventListener('visibilitychange', update);
    document.removeEventListener('focusin', update);
    document.removeEventListener('focusout', updateAfterFocus);
  };
}
