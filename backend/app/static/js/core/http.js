import { accessTokenKey, refreshTokenKey } from './config.js';
import { log } from './ui.js';

export function clearTokens() {
  localStorage.removeItem(accessTokenKey);
  localStorage.removeItem(refreshTokenKey);
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

    const error = new Error(`${response.status} ${text}`);
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
