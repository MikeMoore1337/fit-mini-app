import { describe, expect, it } from 'vitest';
import { calculateTanakaZones } from '../../../../src/features/profile/heartRateZones';

describe('calculateTanakaZones', () => {
  it('uses exact age and the Tanaka maximum heart rate formula', () => {
    const result = calculateTanakaZones('1990-09-10', new Date(2026, 7, 11));

    expect(result?.age).toBe(35);
    expect(result?.maximum).toBe(184);
    expect(result?.zones).toEqual([
      { zone: 1, title: 'Восстановление', min_bpm: 92, max_bpm: 110 },
      { zone: 2, title: 'Лёгкая', min_bpm: 110, max_bpm: 129 },
      { zone: 3, title: 'Аэробная', min_bpm: 129, max_bpm: 147 },
      { zone: 4, title: 'Пороговая', min_bpm: 147, max_bpm: 166 },
      { zone: 5, title: 'Максимальная', min_bpm: 166, max_bpm: 184 },
    ]);
  });

  it('returns null until a valid birth date is entered', () => {
    expect(calculateTanakaZones(null)).toBeNull();
    expect(calculateTanakaZones('not-a-date')).toBeNull();
  });
});
