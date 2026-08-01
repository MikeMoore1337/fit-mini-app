import { describe, expect, it, vi } from 'vitest';
import { getTimezoneOptions } from '../../../../src/features/profile/timezones';

describe('timezone options', () => {
  it('keeps the current timezone and UTC in the selectable list', () => {
    vi.spyOn(
      Intl as typeof Intl & { supportedValuesOf?: () => string[] },
      'supportedValuesOf',
    ).mockReturnValue(['Europe/Moscow', 'Asia/Tokyo']);

    expect(getTimezoneOptions('Asia/Yekaterinburg')).toEqual([
      'Asia/Tokyo',
      'Asia/Yekaterinburg',
      'Europe/Moscow',
      'UTC',
    ]);
  });
});
