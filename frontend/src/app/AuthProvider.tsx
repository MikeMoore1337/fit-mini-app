import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  api,
  ApiError,
  clearAccessToken,
  getAccessToken,
  refreshAccessToken,
  setAccessToken,
} from '../shared/api/client';
import type { PublicConfig, User } from '../shared/api/types';
import { LIVE_DATA_REFETCH_INTERVAL_MS } from '../shared/sync';
import type { TelegramWebApp } from '../shared/telegram/types';
import { useQueryClient } from '@tanstack/react-query';

interface DevLoginInput {
  telegram_user_id: number;
  username?: string;
  full_name?: string;
  is_coach: boolean;
  is_admin: boolean;
}

interface EmailRegistrationResult {
  verification_required: boolean;
  verification_token?: string | null;
}

interface AuthContextValue {
  user: User | null;
  config: PublicConfig | null;
  loading: boolean;
  error: string | null;
  reloadUser(): Promise<User | null>;
  devLogin(input: DevLoginInput): Promise<void>;
  telegramLogin(telegram?: TelegramWebApp | null): Promise<void>;
  emailLogin(email: string, password: string): Promise<void>;
  emailRegister(
    username: string,
    email: string,
    password: string,
  ): Promise<EmailRegistrationResult>;
  verifyEmail(token: string): Promise<void>;
  requestPasswordReset(email: string): Promise<void>;
  confirmPasswordReset(token: string, password: string): Promise<void>;
  logout(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
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
      if (reason instanceof ApiError && [401, 403].includes(reason.status)) setUser(null);
      setError(reason instanceof Error ? reason.message : 'Не удалось загрузить профиль');
      return null;
    }
  }, []);

  const syncUser = useCallback(async (): Promise<void> => {
    try {
      const current = await api<User>('/api/v1/me');
      setUser(current);
      setError(null);
    } catch (reason) {
      // A temporary connection error must not log the user out. An expired session should.
      if (reason instanceof ApiError && reason.status === 401) setUser(null);
    }
  }, []);

  const userId = user?.id;
  useEffect(() => {
    if (!userId) return;

    const syncVisibleUser = () => {
      if (document.visibilityState === 'visible') void syncUser();
    };
    const interval = window.setInterval(syncVisibleUser, LIVE_DATA_REFETCH_INTERVAL_MS);
    window.addEventListener('focus', syncVisibleUser);
    document.addEventListener('visibilitychange', syncVisibleUser);

    return () => {
      window.clearInterval(interval);
      window.removeEventListener('focus', syncVisibleUser);
      document.removeEventListener('visibilitychange', syncVisibleUser);
    };
  }, [syncUser, userId]);

  const telegramLogin = useCallback(
    async (telegram: TelegramWebApp | null = window.Telegram?.WebApp ?? null) => {
      const initData = telegram?.initData?.trim();
      if (!initData) throw new Error('Telegram не передал данные авторизации');
      const token = await api<{ access_token: string }>('/api/v1/auth/telegram/init', {
        method: 'POST',
        body: { init_data: initData },
        retryAuth: false,
      });
      setUser(null);
      setError(null);
      queryClient.clear();
      setAccessToken(token.access_token);
      await reloadUser();
    },
    [queryClient, reloadUser],
  );

  const devLogin = useCallback(
    async (input: DevLoginInput) => {
      const token = await api<{ access_token: string }>('/api/v1/auth/dev-login', {
        method: 'POST',
        body: input,
        retryAuth: false,
      });
      setUser(null);
      setError(null);
      queryClient.clear();
      setAccessToken(token.access_token);
      await reloadUser();
    },
    [queryClient, reloadUser],
  );

  const acceptToken = useCallback(
    async (token: { access_token: string }) => {
      setUser(null);
      setError(null);
      queryClient.clear();
      setAccessToken(token.access_token);
      await reloadUser();
    },
    [queryClient, reloadUser],
  );

  const emailLogin = useCallback(
    async (email: string, password: string) => {
      const token = await api<{ access_token: string }>('/api/v1/auth/email/login', {
        method: 'POST',
        body: { email, password },
        retryAuth: false,
      });
      await acceptToken(token);
    },
    [acceptToken],
  );

  const emailRegister = useCallback(
    (username: string, email: string, password: string) =>
      api<EmailRegistrationResult>('/api/v1/auth/email/register', {
        method: 'POST',
        body: { username, email, password },
        retryAuth: false,
      }),
    [],
  );

  const verifyEmail = useCallback(
    async (verificationToken: string) => {
      const token = await api<{ access_token: string }>('/api/v1/auth/email/verify', {
        method: 'POST',
        body: { token: verificationToken },
        retryAuth: false,
      });
      await acceptToken(token);
    },
    [acceptToken],
  );

  const requestPasswordReset = useCallback(async (email: string) => {
    await api('/api/v1/auth/password/reset/request', {
      method: 'POST',
      body: { email },
      retryAuth: false,
    });
  }, []);

  const confirmPasswordReset = useCallback(async (token: string, password: string) => {
    await api('/api/v1/auth/password/reset/confirm', {
      method: 'POST',
      body: { token, password },
      retryAuth: false,
    });
  }, []);

  const logout = useCallback(async () => {
    const serverLogout = api('/api/v1/auth/logout', {
      method: 'POST',
      body: {},
      retryAuth: false,
      timeoutMs: 3_000,
    }).catch(() => undefined);
    clearAccessToken();
    setUser(null);
    queryClient.clear();
    await serverLogout;
  }, [queryClient]);

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
    () => ({
      user,
      config,
      loading,
      error,
      reloadUser,
      devLogin,
      telegramLogin,
      emailLogin,
      emailRegister,
      verifyEmail,
      requestPasswordReset,
      confirmPasswordReset,
      logout,
    }),
    [
      user,
      config,
      loading,
      error,
      reloadUser,
      devLogin,
      telegramLogin,
      emailLogin,
      emailRegister,
      verifyEmail,
      requestPasswordReset,
      confirmPasswordReset,
      logout,
    ],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider');
  return value;
}
