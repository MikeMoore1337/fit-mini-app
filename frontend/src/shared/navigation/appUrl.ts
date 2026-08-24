export function appUrlForHostname(hostname: string): string {
  return ['your-fitness-coach.ru', 'www.your-fitness-coach.ru'].includes(hostname)
    ? 'https://app.your-fitness-coach.ru/app'
    : '/app';
}

export function loginUrlForHostname(hostname: string): string {
  return ['your-fitness-coach.ru', 'www.your-fitness-coach.ru'].includes(hostname)
    ? 'https://app.your-fitness-coach.ru/login'
    : '/login';
}

export function demoUrlForHostname(hostname: string): string {
  return ['your-fitness-coach.ru', 'www.your-fitness-coach.ru'].includes(hostname)
    ? 'https://app.your-fitness-coach.ru/demo'
    : '/demo';
}

export function publicUrlForHostname(hostname: string, path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return ['app.your-fitness-coach.ru', 'www.app.your-fitness-coach.ru'].includes(hostname)
    ? `https://your-fitness-coach.ru${normalizedPath}`
    : normalizedPath;
}
