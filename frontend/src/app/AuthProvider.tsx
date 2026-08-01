import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  api,
  clearAccessToken,
  getAccessToken,
  refreshAccessToken,
  setAccessToken,
} from '../shared/api/client';
import type { PublicConfig, User } from '../shared/api/types';
import type { TelegramWebApp } from '../shared/telegram/types';

interface DevLoginInput {
  telegram_user_id: number;
  username?: string;
  full_name?: string;
  is_coach: boolean;
  is_admin: boolean;
}

interface AuthContextValue {
  user: User | null;
  config: PublicConfig | null;
  loading: boolean;
  error: string | null;
  reloadUser(): Promise<User | null>;
  devLogin(input: DevLoginInput): Promise<void>;
  telegramLogin(telegram?: TelegramWebApp | null): Promise<void>;
  logout(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reloadUser = useCallback(async (): Promise<User | null> => {
    try {
      const current = await api<User>('/api/v1/me');
      setUser(current);
      setError(null);
      return current;
    } catch (reason) {
      setUser(null);
      setError(reason instanceof Error ? reason.message : 'Не удалось загрузить профиль');
      return null;
    }
  }, []);

  const telegramLogin = useCallback(
    async (telegram: TelegramWebApp | null = window.Telegram?.WebApp ?? null) => {
      const initData = telegram?.initData?.trim();
      if (!initData) throw new Error('Telegram не передал данные авторизации');
      const token = await api<{ access_token: string }>('/api/v1/auth/telegram/init', {
        method: 'POST',
        body: { init_data: initData },
        retryAuth: false,
      });
      setAccessToken(token.access_token);
      await reloadUser();
    },
    [reloadUser],
  );

  const devLogin = useCallback(
    async (input: DevLoginInput) => {
      const token = await api<{ access_token: string }>('/api/v1/auth/dev-login', {
        method: 'POST',
        body: input,
        retryAuth: false,
      });
      setAccessToken(token.access_token);
      await reloadUser();
    },
    [reloadUser],
  );

  const logout = useCallback(async () => {
    try {
      await api('/api/v1/auth/logout', { method: 'POST', body: {}, retryAuth: false });
    } finally {
      clearAccessToken();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const publicConfig = await api<PublicConfig>('/api/v1/public/config', {
          retryAuth: false,
        });
        if (cancelled) return;
        setConfig(publicConfig);

        if (getAccessToken()) {
          const current = await reloadUser();
          if (current || cancelled) return;
        }

        // The access token deliberately lives only in sessionStorage. A page reload in a
        // new tab can still restore the session through the HttpOnly refresh cookie.
        if (!getAccessToken() && (await refreshAccessToken())) {
          const current = await reloadUser();
          if (current || cancelled) return;
        }

        const tg = window.Telegram?.WebApp;
        if (tg?.initData?.trim()) {
          try {
            await telegramLogin(tg);
          } catch (reason) {
            if (!cancelled) {
              setError(
                reason instanceof Error ? reason.message : 'Не удалось войти через Telegram',
              );
            }
          }
        }
      } catch (reason) {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : 'Не удалось запустить приложение');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [reloadUser, telegramLogin]);

  const value = useMemo(
    () => ({ user, config, loading, error, reloadUser, devLogin, telegramLogin, logout }),
    [user, config, loading, error, reloadUser, devLogin, telegramLogin, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
