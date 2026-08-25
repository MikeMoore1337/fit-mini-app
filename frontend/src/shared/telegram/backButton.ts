import type { TelegramWebApp } from './types';

type BackButtonPriority = 'route' | 'overlay';

interface BackButtonRegistration {
  id: symbol;
  telegram: TelegramWebApp;
  callback: () => void;
  priority: number;
  order: number;
}

const registrations = new Map<symbol, BackButtonRegistration>();
let registrationOrder = 0;
let mounted: Pick<BackButtonRegistration, 'id' | 'telegram' | 'callback'> | null = null;

function activeRegistration(): BackButtonRegistration | null {
  return (
    [...registrations.values()].sort(
      (left, right) => right.priority - left.priority || right.order - left.order,
    )[0] ?? null
  );
}

function reconcileBackButton(): void {
  const desired = activeRegistration();
  if (mounted?.id === desired?.id) return;

  if (mounted) {
    mounted.telegram.BackButton?.offClick(mounted.callback);
    if (!desired || desired.telegram !== mounted.telegram) mounted.telegram.BackButton?.hide();
    mounted = null;
  }

  if (!desired?.telegram.initData || !desired.telegram.BackButton) return;
  desired.telegram.BackButton.onClick(desired.callback);
  desired.telegram.BackButton.show();
  mounted = desired;
}

export function registerTelegramBackButton(
  telegram: TelegramWebApp | null | undefined,
  callback: () => void,
  priority: BackButtonPriority,
): () => void {
  if (!telegram?.initData || !telegram.BackButton) return () => undefined;

  const id = Symbol(priority);
  registrations.set(id, {
    id,
    telegram,
    callback,
    priority: priority === 'overlay' ? 100 : 0,
    order: ++registrationOrder,
  });
  reconcileBackButton();

  return () => {
    registrations.delete(id);
    reconcileBackButton();
  };
}

export function hideTelegramBackButtonWhenIdle(telegram: TelegramWebApp | null | undefined): void {
  if (!telegram?.initData || !telegram.BackButton || activeRegistration()) return;
  telegram.BackButton.hide();
}
