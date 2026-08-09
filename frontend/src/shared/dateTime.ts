export function detectedTimeZone(fallback = 'Europe/Moscow'): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || fallback;
  } catch {
    return fallback;
  }
}

export function dateInputValue(date: Date, timeZone = detectedTimeZone()): string {
  try {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).formatToParts(date);
    const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    if (value.year && value.month && value.day) return `${value.year}-${value.month}-${value.day}`;
  } catch {
    // Fall back to the device-local calendar below for an invalid or unsupported timezone.
  }
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function addCalendarDays(value: string, days: number): string {
  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) return value;
  const date = new Date(Date.UTC(year, month - 1, day + days));
  return date.toISOString().slice(0, 10);
}
