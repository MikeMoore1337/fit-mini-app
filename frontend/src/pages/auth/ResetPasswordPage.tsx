import { useState, type FormEvent } from 'react';
import { useAuth } from '../../app/AuthProvider';
import { AppLink } from '../../shared/navigation/router';
import { Card, ErrorState } from '../../shared/ui/common';

export default function ResetPasswordPage() {
  const { confirmPasswordReset } = useAuth();
  const token = new URLSearchParams(window.location.search).get('token') ?? '';
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await confirmPasswordReset(token, password);
      setCompleted(true);
      setPassword('');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось изменить пароль');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="container narrow">
      <Card
        className="auth-panel"
        title="Новый пароль"
        description="Создайте новый пароль длиной не менее 12 символов."
      >
        <div className="stack top-gap">
          {error && <ErrorState message={error} />}
          {!token && <ErrorState message="В ссылке отсутствует токен восстановления" />}
          {completed ? (
            <p className="auth-success" role="status">
              Пароль изменён. Теперь можно войти.
            </p>
          ) : (
            token && (
              <form className="stack" onSubmit={(event) => void submit(event)}>
                <label>
                  Новый пароль
                  <input
                    required
                    type="password"
                    minLength={12}
                    maxLength={128}
                    autoComplete="new-password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </label>
                <button type="submit" disabled={busy}>
                  {busy ? 'Сохраняем…' : 'Сохранить новый пароль'}
                </button>
              </form>
            )
          )}
          <AppLink className="button-link secondary" to="/app">
            Перейти ко входу
          </AppLink>
        </div>
      </Card>
    </main>
  );
}
