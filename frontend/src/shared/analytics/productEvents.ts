export const PRODUCT_EVENT_NAME = 'yfc:product-event';
export const PRODUCT_ANALYTICS_STATUS_NAME = 'yfc:product-analytics-status';
export const PRODUCT_EVENT_SCHEMA_VERSION = 1 as const;

export type ProductAnalyticsEnvironment = 'production' | 'staging' | 'development' | 'test';
export type ProductSurface = 'web' | 'telegram';

type ContextFreeProductEventName =
  | 'landing_viewed'
  | 'landing_demo_selected'
  | 'landing_login_selected'
  | 'demo_started'
  | 'demo_login_selected'
  | 'login_started'
  | 'login_completed'
  | 'onboarding_started'
  | 'onboarding_minimum_saved'
  | 'program_recommendation_started'
  | 'program_recommendation_completed'
  | 'program_activated'
  | 'workout_started'
  | 'workout_completed'
  | 'food_logged'
  | 'measurement_logged'
  | 'check_in_logged';

type ContextFreeProductEvent = {
  [Name in ContextFreeProductEventName]: {
    name: Name;
    surface: ProductSurface;
  };
}[ContextFreeProductEventName];

export type ProductEvent =
  | ContextFreeProductEvent
  | {
      name: 'onboarding_next_action_selected';
      surface: ProductSurface;
      next_action: 'today' | 'nutrition' | 'programs' | 'continuation';
    };

export type ProductEventName = ProductEvent['name'];

export type ProductEventEnvelope = ProductEvent & {
  schema_version: typeof PRODUCT_EVENT_SCHEMA_VERSION;
  environment: ProductAnalyticsEnvironment;
  occurred_at: string;
};

export type ProductAnalyticsStatus = {
  provider: string;
  environment: ProductAnalyticsEnvironment;
  reason: 'provider_unavailable';
};

export interface ProductAnalyticsProvider {
  name: string;
  environment: ProductAnalyticsEnvironment;
  send(event: ProductEventEnvelope): void | Promise<void>;
}

export type ProductEventTrackOptions = {
  dedupe?: 'none' | 'session';
};

type ProductAnalyticsRuntimeOptions = {
  target: EventTarget;
  environment: ProductAnalyticsEnvironment;
  now?: () => Date;
};

const CONTEXT_FREE_EVENT_NAMES = new Set<ProductEventName>([
  'landing_viewed',
  'landing_demo_selected',
  'landing_login_selected',
  'demo_started',
  'demo_login_selected',
  'login_started',
  'login_completed',
  'onboarding_started',
  'onboarding_minimum_saved',
  'program_recommendation_started',
  'program_recommendation_completed',
  'program_activated',
  'workout_started',
  'workout_completed',
  'food_logged',
  'measurement_logged',
  'check_in_logged',
]);
const PRODUCT_SURFACES = new Set<ProductSurface>(['web', 'telegram']);
const PRODUCT_ANALYTICS_ENVIRONMENTS = new Set<ProductAnalyticsEnvironment>([
  'production',
  'staging',
  'development',
  'test',
]);
const ONBOARDING_NEXT_ACTIONS = new Set(['today', 'nutrition', 'programs', 'continuation']);
const BASE_EVENT_KEYS = ['name', 'surface'] as const;
const ENVELOPE_KEYS = ['schema_version', 'environment', 'occurred_at'] as const;
const PROVIDER_NAME_PATTERN = /^[a-z][a-z0-9_-]{0,63}$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(value: Record<string, unknown>, allowedKeys: readonly string[]): boolean {
  const keys = Object.keys(value);
  return keys.length === allowedKeys.length && keys.every((key) => allowedKeys.includes(key));
}

function isProductEventRecord(value: unknown, envelope: boolean): boolean {
  if (!isRecord(value) || typeof value.name !== 'string') return false;

  const eventKeys =
    value.name === 'onboarding_next_action_selected'
      ? [...BASE_EVENT_KEYS, 'next_action']
      : BASE_EVENT_KEYS;
  const allowedKeys = envelope ? [...eventKeys, ...ENVELOPE_KEYS] : eventKeys;
  if (!hasOnlyKeys(value, allowedKeys)) return false;
  if (!PRODUCT_SURFACES.has(value.surface as ProductSurface)) return false;

  const validEvent =
    CONTEXT_FREE_EVENT_NAMES.has(value.name as ProductEventName) ||
    (value.name === 'onboarding_next_action_selected' &&
      ONBOARDING_NEXT_ACTIONS.has(value.next_action as string));
  if (!validEvent) return false;
  if (!envelope) return true;

  if (
    typeof value.occurred_at !== 'string' ||
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(value.occurred_at)
  ) {
    return false;
  }
  const occurredAtTime = Date.parse(value.occurred_at);

  return (
    value.schema_version === PRODUCT_EVENT_SCHEMA_VERSION &&
    PRODUCT_ANALYTICS_ENVIRONMENTS.has(value.environment as ProductAnalyticsEnvironment) &&
    Number.isFinite(occurredAtTime) &&
    new Date(occurredAtTime).toISOString() === value.occurred_at
  );
}

export function isProductEvent(value: unknown): value is ProductEvent {
  return isProductEventRecord(value, false);
}

export function isProductEventEnvelope(value: unknown): value is ProductEventEnvelope {
  return isProductEventRecord(value, true);
}

export function productAnalyticsEnvironment(mode: string): ProductAnalyticsEnvironment {
  if (mode === 'production' || mode === 'staging' || mode === 'test') return mode;
  return 'development';
}

export function productEventSurface(): ProductSurface {
  return window.Telegram?.WebApp?.initData?.trim() ? 'telegram' : 'web';
}

export function createProductAnalytics({
  target,
  environment,
  now = () => new Date(),
}: ProductAnalyticsRuntimeOptions) {
  const sessionDedupe = new Set<string>();

  const reportProviderUnavailable = (provider: ProductAnalyticsProvider) => {
    target.dispatchEvent(
      new CustomEvent<ProductAnalyticsStatus>(PRODUCT_ANALYTICS_STATUS_NAME, {
        detail: Object.freeze({
          provider: provider.name,
          environment,
          reason: 'provider_unavailable',
        }),
      }),
    );
  };

  return {
    track(event: ProductEvent, options: ProductEventTrackOptions = {}): boolean {
      if (!isProductEvent(event)) return false;

      const dedupeKey = `${PRODUCT_EVENT_SCHEMA_VERSION}:${environment}:${event.surface}:${event.name}`;
      if (options.dedupe === 'session') {
        if (sessionDedupe.has(dedupeKey)) return false;
        sessionDedupe.add(dedupeKey);
      }

      const envelope = Object.freeze({
        ...event,
        schema_version: PRODUCT_EVENT_SCHEMA_VERSION,
        environment,
        occurred_at: now().toISOString(),
      }) as ProductEventEnvelope;
      target.dispatchEvent(
        new CustomEvent<ProductEventEnvelope>(PRODUCT_EVENT_NAME, { detail: envelope }),
      );
      return true;
    },

    subscribe(provider: ProductAnalyticsProvider): () => void {
      if (!PROVIDER_NAME_PATTERN.test(provider.name)) {
        throw new Error('Product analytics provider name must be a safe lowercase identifier');
      }
      if (provider.environment !== environment) return () => undefined;

      const listener = (rawEvent: Event) => {
        if (!(rawEvent instanceof CustomEvent) || !isProductEventEnvelope(rawEvent.detail)) return;
        if (rawEvent.detail.environment !== provider.environment) return;

        try {
          void Promise.resolve(provider.send(rawEvent.detail)).catch(() => {
            reportProviderUnavailable(provider);
          });
        } catch {
          reportProviderUnavailable(provider);
        }
      };
      target.addEventListener(PRODUCT_EVENT_NAME, listener);
      return () => target.removeEventListener(PRODUCT_EVENT_NAME, listener);
    },
  };
}

const browserProductAnalytics = createProductAnalytics({
  target: window,
  environment: productAnalyticsEnvironment(import.meta.env.MODE),
});

export function trackProductEvent(
  event: ProductEvent,
  options?: ProductEventTrackOptions,
): boolean {
  return browserProductAnalytics.track(event, options);
}

export function subscribeProductAnalyticsProvider(provider: ProductAnalyticsProvider): () => void {
  return browserProductAnalytics.subscribe(provider);
}
