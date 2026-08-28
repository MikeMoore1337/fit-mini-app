export function telegramMiniAppUrl(username: string): string {
  const normalized = username.trim().replace(/^@/, '');
  return `https://t.me/${encodeURIComponent(normalized)}?startapp`;
}

const CANONICAL_TELEGRAM_BOT_USERNAME = 'your_fitness_coach_bot';

export const PUBLIC_TELEGRAM_LINKS = {
  miniApp: telegramMiniAppUrl(CANONICAL_TELEGRAM_BOT_USERNAME),
  news: 'https://t.me/your_fitness_news',
  support: `https://t.me/${CANONICAL_TELEGRAM_BOT_USERNAME}?start=support`,
} as const;
