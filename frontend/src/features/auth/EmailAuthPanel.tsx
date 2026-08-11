import { useState, type FormEvent } from 'react';
import { useAuth } from '../../app/AuthProvider';
import { ErrorState } from '../../shared/ui/common';

type AuthMode = 'login' | 'register' | 'recover';

export function EmailAuthPanel() {
  const { emailLogin, emailRegister, requestPasswordReset } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setError(null);
    setMessage(null);
    setPassword('');
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      if (mode === 'login') {
        await emailLogin(email, password);
      } else if (mode === 'register') {
        const nextPath = window.location.pathname.startsWith('/join/')
          ? window.location.pathname
          : null;
        await emailRegister(username, email, password, nextPath);
        setMessage('Аккаунт создан. Проверьте почту и подтвердите email.');
        setPassword('');
      } else {
        await requestPasswordReset(email);
        setMessage('Если аккаунт существует, письмо для восстановления уже отправлено.');
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось выполнить запрос');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="email-auth" aria-label="Вход по email">
      <div className="email-auth__tabs" role="tablist" aria-label="Способ входа">
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'login'}
          className={mode === 'login' ? 'is-active' : 'secondary'}
          onClick={() => switchMode('login')}
        >
          Вход
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === 'register'}
          className={mode === 'register' ? 'is-active' : 'secondary'}
          onClick={() => switchMode('register')}
        >
          Регистрация
        </button>
      </div>

      {error && <ErrorState message={error} />}
      {message && (
        <p className="auth-success" role="status">
          {message}
        </p>
      )}

      <form className="stack" onSubmit={(event) => void submit(event)}>
        {mode === 'register' && (
          <label>
            Имя пользователя
            <input
              required
              minLength={3}
              maxLength={32}
              autoComplete="username"
              pattern="[a-z0-9][a-z0-9_.-]{2,31}"
              placeholder="например, alex_fit"
              value={username}
              onChange={(event) => setUsername(event.target.value.toLowerCase())}
            />
            <small className="muted">Латинские буквы, цифры, точка, дефис или подчёркивание.</small>
          </label>
        )}
        <label>
          Email
          <input
            required
            type="email"
            maxLength={320}
            autoComplete="email"
            placeholder="name@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        {mode !== 'recover' && (
          <label>
            Пароль
            <input
              required
              type="password"
              minLength={mode === 'register' ? 12 : 1}
              maxLength={128}
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            {mode === 'register' && (
              <small className="muted">
                Не менее 12 символов. Подойдёт длинная запоминающаяся фраза.
              </small>
            )}
          </label>
        )}
        <button type="submit" disabled={busy}>
          {busy
            ? 'Подождите…'
            : mode === 'login'
              ? 'Войти'
              : mode === 'register'
                ? 'Создать аккаунт'
                : 'Отправить ссылку'}
        </button>
      </form>

      {mode === 'login' && (
        <button className="text-link-button" type="button" onClick={() => switchMode('recover')}>
          Не помню пароль
        </button>
      )}
      {mode === 'recover' && (
        <button className="text-link-button" type="button" onClick={() => switchMode('login')}>
          Вернуться ко входу
        </button>
      )}
    </section>
  );
}
