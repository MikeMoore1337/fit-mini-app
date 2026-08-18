import { useState } from 'react';
import { useAuth } from '../../app/AuthProvider';
import { AppLink, useNavigation } from '../../shared/navigation/router';
import { Card, ErrorState } from '../../shared/ui/common';
import { PublicShell } from '../../shared/ui/PublicShell';
import { loginPathForNext, safeAuthNextPath } from '../../shared/auth/redirects';
import './auth.css';

export default function VerifyEmailPage() {
  const { verifyEmail } = useAuth();
  const { navigate } = useNavigation();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const token = new URLSearchParams(window.location.search).get('token') ?? '';
  const requestedNext = new URLSearchParams(window.location.search).get('next');
  const nextPath = safeAuthNextPath(requestedNext);

  const verify = async () => {
    setBusy(true);
    setError(null);
    try {
      await verifyEmail(token);
      navigate(nextPath, true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось подтвердить email');
    } finally {
      setBusy(false);
    }
  };

  return (
    <PublicShell skipTarget="verify-email-content">
      <main id="verify-email-content" className="auth-aux-layout" tabIndex={-1}>
        <Card
          collapsible={false}
          className="auth-panel"
          title="Подтверждение email"
          description="После подтверждения вы войдёте в Your Fitness Coach."
        >
          <div className="stack top-gap">
            {error && <ErrorState message={error} />}
            {!token ? (
              <ErrorState message="В ссылке отсутствует токен подтверждения" />
            ) : (
              <button disabled={busy} onClick={() => void verify()}>
                {busy ? 'Подтверждаем…' : 'Подтвердить email'}
              </button>
            )}
            <AppLink className="button-link secondary" to={loginPathForNext(nextPath)}>
              Вернуться ко входу
            </AppLink>
          </div>
        </Card>
      </main>
    </PublicShell>
  );
}
