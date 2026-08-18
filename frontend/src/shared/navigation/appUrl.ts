export function appUrlForHostname(hostname: string): string {
  return ['your-fitness-coach.ru', 'www.your-fitness-coach.ru'].includes(hostname)
    ? 'https://app.your-fitness-coach.ru/app'
    : '/app';
}
