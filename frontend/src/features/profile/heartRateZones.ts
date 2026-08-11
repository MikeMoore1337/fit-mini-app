export type HeartRateZone = {
  zone: number;
  title: string;
  min_bpm: number;
  max_bpm: number;
};

const ranges = [
  ['Восстановление', 0.5, 0.6],
  ['Лёгкая', 0.6, 0.7],
  ['Аэробная', 0.7, 0.8],
  ['Пороговая', 0.8, 0.9],
  ['Максимальная', 0.9, 1],
] as const;

export function calculateTanakaZones(
  birthDate: string | null | undefined,
  today = new Date(),
): { age: number; maximum: number; zones: HeartRateZone[] } | null {
  if (!birthDate) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(birthDate);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  let age = today.getFullYear() - year;
  if (today.getMonth() + 1 < month || (today.getMonth() + 1 === month && today.getDate() < day)) {
    age -= 1;
  }
  if (age < 10 || age > 100) return null;
  const maximum = Math.round(208 - 0.7 * age);
  return {
    age,
    maximum,
    zones: ranges.map(([title, lower, upper], index) => ({
      zone: index + 1,
      title,
      min_bpm: Math.round(maximum * lower),
      max_bpm: Math.round(maximum * upper),
    })),
  };
}
