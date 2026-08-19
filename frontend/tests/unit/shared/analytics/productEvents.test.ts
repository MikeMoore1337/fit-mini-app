import { describe, expect, it, vi } from 'vitest';
import {
  createProductAnalytics,
  isProductEvent,
  isProductEventEnvelope,
  PRODUCT_ANALYTICS_STATUS_NAME,
  PRODUCT_EVENT_NAME,
  PRODUCT_EVENT_SCHEMA_VERSION,
  productAnalyticsEnvironment,
  type ProductAnalyticsStatus,
  type ProductEvent,
  type ProductEventEnvelope,
} from '../../../../src/shared/analytics/productEvents';

function testAnalytics(target = new EventTarget()) {
  return {
    target,
    analytics: createProductAnalytics({
      target,
      environment: 'test',
      now: () => new Date('2026-08-19T10:00:00.000Z'),
    }),
  };
}

describe('product event contract', () => {
  it('emits a versioned provider-neutral envelope', () => {
    const { target, analytics } = testAnalytics();
    const events: ProductEventEnvelope[] = [];
    target.addEventListener(PRODUCT_EVENT_NAME, (event) => {
      events.push((event as CustomEvent<ProductEventEnvelope>).detail);
    });

    expect(analytics.track({ name: 'workout_completed', surface: 'telegram' })).toBe(true);
    expect(events).toEqual([
      {
        name: 'workout_completed',
        surface: 'telegram',
        schema_version: PRODUCT_EVENT_SCHEMA_VERSION,
        environment: 'test',
        occurred_at: '2026-08-19T10:00:00.000Z',
      },
    ]);
    expect(isProductEventEnvelope(events[0])).toBe(true);
  });

  it('deduplicates only when the caller selects session scope', () => {
    const { target, analytics } = testAnalytics();
    const listener = vi.fn();
    target.addEventListener(PRODUCT_EVENT_NAME, listener);
    const event = { name: 'onboarding_started', surface: 'web' } as const;

    expect(analytics.track(event, { dedupe: 'session' })).toBe(true);
    expect(analytics.track(event, { dedupe: 'session' })).toBe(false);
    expect(listener).toHaveBeenCalledOnce();

    expect(analytics.track({ name: 'food_logged', surface: 'web' })).toBe(true);
    expect(analytics.track({ name: 'food_logged', surface: 'web' })).toBe(true);
    expect(listener).toHaveBeenCalledTimes(3);
  });

  it.each([
    ['food_contents', 'Борщ'],
    ['weight_kg', 81.4],
    ['waist_cm', 92],
    ['calories', 2400],
    ['trainer_comment', 'private'],
    ['ai_conversation', 'private'],
    ['access_token', 'secret'],
    ['user_id', 42],
  ])('rejects forbidden or unversioned payload field %s', (field, value) => {
    const { target, analytics } = testAnalytics();
    const listener = vi.fn();
    target.addEventListener(PRODUCT_EVENT_NAME, listener);
    const unsafeEvent = {
      name: 'measurement_logged',
      surface: 'web',
      [field]: value,
    } as unknown as ProductEvent;

    expect(isProductEvent(unsafeEvent)).toBe(false);
    expect(analytics.track(unsafeEvent)).toBe(false);
    expect(listener).not.toHaveBeenCalled();
  });

  it('validates constrained event context values', () => {
    expect(
      isProductEvent({
        name: 'onboarding_next_action_selected',
        surface: 'web',
        next_action: 'programs',
      }),
    ).toBe(true);
    expect(
      isProductEvent({
        name: 'onboarding_next_action_selected',
        surface: 'web',
        next_action: '/private/path?token=secret',
      }),
    ).toBe(false);
  });

  it('rejects unknown schema versions and malformed timestamps', () => {
    const envelope = {
      name: 'workout_started',
      surface: 'web',
      schema_version: PRODUCT_EVENT_SCHEMA_VERSION,
      environment: 'test',
      occurred_at: '2026-08-19T10:00:00.000Z',
    };

    expect(isProductEventEnvelope({ ...envelope, schema_version: 2 })).toBe(false);
    expect(isProductEventEnvelope({ ...envelope, occurred_at: '2026-99-99' })).toBe(false);
    expect(isProductEventEnvelope({ ...envelope, name: 'unknown_event' })).toBe(false);
  });

  it('keeps development, test, staging and production providers isolated', () => {
    const { analytics } = testAnalytics();
    const testProvider = { name: 'test_sink', environment: 'test' as const, send: vi.fn() };
    const productionProvider = {
      name: 'production_sink',
      environment: 'production' as const,
      send: vi.fn(),
    };
    analytics.subscribe(testProvider);
    analytics.subscribe(productionProvider);

    analytics.track({ name: 'landing_viewed', surface: 'web' });

    expect(testProvider.send).toHaveBeenCalledOnce();
    expect(productionProvider.send).not.toHaveBeenCalled();
    expect(productAnalyticsEnvironment('production')).toBe('production');
    expect(productAnalyticsEnvironment('staging')).toBe('staging');
    expect(productAnalyticsEnvironment('test')).toBe('test');
    expect(productAnalyticsEnvironment('custom-local-mode')).toBe('development');
  });

  it('ignores forged bus payloads before they reach a provider', () => {
    const { target, analytics } = testAnalytics();
    const provider = { name: 'safe_sink', environment: 'test' as const, send: vi.fn() };
    analytics.subscribe(provider);

    target.dispatchEvent(
      new CustomEvent(PRODUCT_EVENT_NAME, {
        detail: {
          name: 'food_logged',
          surface: 'web',
          food_contents: 'private',
          schema_version: PRODUCT_EVENT_SCHEMA_VERSION,
          environment: 'test',
          occurred_at: '2026-08-19T10:00:00.000Z',
        },
      }),
    );

    expect(provider.send).not.toHaveBeenCalled();
  });

  it('isolates an unavailable provider from the product flow', async () => {
    const { target, analytics } = testAnalytics();
    const statuses: ProductAnalyticsStatus[] = [];
    target.addEventListener(PRODUCT_ANALYTICS_STATUS_NAME, (event) => {
      statuses.push((event as CustomEvent<ProductAnalyticsStatus>).detail);
    });
    analytics.subscribe({
      name: 'unavailable_sink',
      environment: 'test',
      send: () => Promise.reject(new Error('provider payload must not escape')),
    });

    expect(analytics.track({ name: 'login_completed', surface: 'web' })).toBe(true);
    await Promise.resolve();
    await Promise.resolve();

    expect(statuses).toEqual([
      { provider: 'unavailable_sink', environment: 'test', reason: 'provider_unavailable' },
    ]);
    expect(JSON.stringify(statuses)).not.toContain('provider payload must not escape');
  });
});
