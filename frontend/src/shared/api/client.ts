const ACCESS_TOKEN_KEY = 'fit_access_token';
const AUTH_CHANNEL_NAME = 'fit_auth_session';
export const AUTH_LOGOUT_EVENT = 'fit:auth-logout';

type AuthChannelMessage = { type: 'access-token'; token: string } | { type: 'logout' };

const authChannel =
  typeof window !== 'undefined' && typeof window.BroadcastChannel === 'function'
    ? new window.BroadcastChannel(AUTH_CHANNEL_NAME)
    : null;

authChannel?.addEventListener('message', (event: MessageEvent<AuthChannelMessage>) => {
  if (!event.data || typeof event.data !== 'object' || !('type' in event.data)) return;
  if (event.data.type === 'access-token' && typeof event.data.token === 'string') {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, event.data.token);
  } else if (event.data.type === 'logout') {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT));
  }
});

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

function migrateLegacyToken(): void {
  const legacy = localStorage.getItem(ACCESS_TOKEN_KEY);
  if (legacy && !sessionStorage.getItem(ACCESS_TOKEN_KEY)) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, legacy);
  }
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem('fit_refresh_token');
}

migrateLegacyToken();

export function getAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
  authChannel?.postMessage({ type: 'access-token', token } satisfies AuthChannelMessage);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_LOGOUT_EVENT));
  authChannel?.postMessage({ type: 'logout' } satisfies AuthChannelMessage);
}

async function responseError(response: Response): Promise<ApiError> {
  const text = await response.text();
  let body: unknown = text;
  let message = text || `Ошибка ${response.status}`;
  try {
    body = JSON.parse(text);
    if (body && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === 'string') message = detail;
      if (Array.isArray(detail)) {
        message = detail
          .map((item) =>
            item && typeof item === 'object' && 'msg' in item ? String(item.msg) : String(item),
          )
          .join(' ');
      }
    }
  } catch {
    // Non-JSON error bodies remain readable.
  }
  return new ApiError(message.slice(0, 500), response.status, body);
}

let refreshPromise: Promise<boolean> | null = null;

async function requestAccessTokenRefresh(): Promise<boolean> {
  try {
    const response = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: '{}',
    });
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) clearAccessToken();
      return false;
    }
    const data = (await response.json()) as { access_token?: unknown };
    if (typeof data.access_token !== 'string' || !data.access_token) {
      clearAccessToken();
      return false;
    }
    setAccessToken(data.access_token);
    return true;
  } catch {
    return false;
  }
}

export async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    try {
      const tokenBeforeLock = getAccessToken();
      if (navigator.locks?.request) {
        return await navigator.locks.request('fit-auth-refresh', async () => {
          const tokenAfterLock = getAccessToken();
          if (tokenAfterLock && tokenAfterLock !== tokenBeforeLock) return true;
          return requestAccessTokenRefresh();
        });
      }
      return await requestAccessTokenRefresh();
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

export interface ApiOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  timeoutMs?: number;
  retryAuth?: boolean;
}

export async function api<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { body, timeoutMs = 15_000, retryAuth = true, headers, ...init } = options;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const token = getAccessToken();
  try {
    const response = await fetch(path, {
      ...init,
      credentials: 'same-origin',
      signal: controller.signal,
      headers: {
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      ...(body !== undefined
        ? { body: typeof body === 'string' ? body : JSON.stringify(body) }
        : {}),
    });
    if (response.status === 401 && retryAuth && (await refreshAccessToken())) {
      return api<T>(path, { ...options, retryAuth: false });
    }
    if (!response.ok) throw await responseError(response);
    if (response.status === 204) return undefined as T;
    const text = await response.text();
    return (text ? JSON.parse(text) : null) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('Сервер не ответил вовремя. Попробуйте снова.', 0);
    }
    if (error instanceof TypeError) {
      throw new ApiError('Нет соединения с сервером. Проверьте интернет и попробуйте снова.', 0);
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}
