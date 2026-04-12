import { accessTokenKey, refreshTokenKey } from './config.js';
import { log } from './ui.js';

export function clearTokens() {
  localStorage.removeItem(accessTokenKey);
  localStorage.removeItem(refreshTokenKey);
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Человекочитаемое сообщение из тела ответа API (FastAPI detail / validation). */
export function formatApiErrorMessage(text, status) {
  const fallback = status ? `Ошибка ${status}` : 'Что-то пошло не так';
  if (!text || !String(text).trim()) return fallback;
  try {
    const parsed = JSON.parse(text);
    if (typeof parsed.detail === 'string') return parsed.detail;
    if (Array.isArray(parsed.detail)) {
      const parts = parsed.detail.map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          const loc = Array.isArray(item.loc)
            ? item.loc.filter((x) => x !== 'body' && x !== 'query' && x !== 'path').join('. ')
            : '';
          return loc ? `${loc}: ${item.msg}` : String(item.msg);
        }
        return String(item);
      });
      return parts.filter(Boolean).join(' ') || fallback;
    }
    if (parsed.detail != null && typeof parsed.detail !== 'object') {
      return String(parsed.detail);
    }
  } catch {
    // не JSON
  }
  const trimmed = String(text).trim();
  if (trimmed.length > 320) return `${trimmed.slice(0, 317)}…`;
  return trimmed || fallback;
}

function authHeaders(extra = {}) {
  const token = localStorage.getItem(accessTokenKey);
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...extra,
  };
}

export async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: authHeaders(options.headers || {}),
  });

  const text = await response.text();

  if (!response.ok) {
    log({
      apiError: true,
      path,
      status: response.status,
      response: text,
    });

    const userMessage = formatApiErrorMessage(text, response.status);
    const error = new Error(userMessage);
    error.status = response.status;
    error.responseText = text;
    throw error;
  }

  if (response.status === 204 || !text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}
