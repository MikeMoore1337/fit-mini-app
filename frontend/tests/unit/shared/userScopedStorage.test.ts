import { beforeEach, describe, expect, it } from 'vitest';
import {
  AUTHENTICATED_USER_ID_STORAGE_KEY,
  USER_SCOPED_PERSISTENT_STORAGE_REGISTRY,
  clearSensitiveUserScopedStorage,
} from '../../../src/shared/userScopedStorage';

describe('user-scoped browser storage registry', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it('cleans every current and legacy sensitive domain while preserving global preferences', () => {
    const sensitiveKeys = USER_SCOPED_PERSISTENT_STORAGE_REGISTRY.flatMap(({ prefixes }) =>
      prefixes.map((prefix) => `${prefix}fixture`),
    );
    for (const key of sensitiveKeys) localStorage.setItem(key, '{"private":true}');
    localStorage.setItem('fit_access_token', 'legacy-access-token');
    localStorage.setItem('fit_refresh_token', 'legacy-refresh-token');
    sessionStorage.setItem(AUTHENTICATED_USER_ID_STORAGE_KEY, '7');
    localStorage.setItem('app-theme', 'dark');
    localStorage.setItem('landing-theme', 'light');
    localStorage.setItem('fit_telegram_link_prompt_dismissed_7', 'true');

    clearSensitiveUserScopedStorage();
    clearSensitiveUserScopedStorage();

    for (const key of sensitiveKeys) expect(localStorage.getItem(key)).toBeNull();
    expect(localStorage.getItem('fit_access_token')).toBeNull();
    expect(localStorage.getItem('fit_refresh_token')).toBeNull();
    expect(sessionStorage.getItem(AUTHENTICATED_USER_ID_STORAGE_KEY)).toBeNull();
    expect(localStorage.getItem('app-theme')).toBe('dark');
    expect(localStorage.getItem('landing-theme')).toBe('light');
    expect(localStorage.getItem('fit_telegram_link_prompt_dismissed_7')).toBe('true');
  });
});
