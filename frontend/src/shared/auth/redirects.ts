const SAFE_AUTH_PATHS = new Set(['/app', '/coach', '/admin']);
const SAFE_JOIN_PATH = /^\/join\/[A-Za-z0-9_-]{20,128}$/;

export function safeAuthNextPath(value: string | null | undefined): string {
  const normalized = value?.trim() ?? '';
  return SAFE_AUTH_PATHS.has(normalized) || SAFE_JOIN_PATH.test(normalized) ? normalized : '/app';
}

export function loginPathForNext(value: string | null | undefined): string {
  return `/login?next=${encodeURIComponent(safeAuthNextPath(value))}`;
}
