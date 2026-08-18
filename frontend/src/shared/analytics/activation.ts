export const PRODUCT_EVENT_NAME = 'yfc:product-event';

export type ActivationEvent =
  | {
      name: 'onboarding_started' | 'onboarding_minimum_saved';
      surface: 'web' | 'telegram';
    }
  | {
      name: 'onboarding_next_action_selected';
      surface: 'web' | 'telegram';
      next_action: 'today' | 'nutrition' | 'programs' | 'continuation';
    };

export function activationSurface(): ActivationEvent['surface'] {
  return window.Telegram?.WebApp?.initData?.trim() ? 'telegram' : 'web';
}

export function emitActivationEvent(event: ActivationEvent): void {
  window.dispatchEvent(new CustomEvent<ActivationEvent>(PRODUCT_EVENT_NAME, { detail: event }));
}
