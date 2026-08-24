const TELEGRAM_SDK_PATHS = new Set(['/app', '/coach', '/admin', '/demo']);
const TELEGRAM_LAUNCH_PARAMS = ['tgWebAppData', 'tgWebAppPlatform', 'tgWebAppVersion'];

export function isTelegramLaunch(
  location: Pick<Location, 'pathname' | 'search' | 'hash'>,
): boolean {
  const appRoute =
    TELEGRAM_SDK_PATHS.has(location.pathname) || location.pathname.startsWith('/join/');
  if (!appRoute) return false;

  const params = new URLSearchParams(location.search);
  const hashParams = new URLSearchParams(location.hash.replace(/^#/, ''));
  return TELEGRAM_LAUNCH_PARAMS.some((name) => params.has(name) || hashParams.has(name));
}
