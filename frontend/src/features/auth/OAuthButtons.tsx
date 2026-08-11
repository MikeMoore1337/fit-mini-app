const PROVIDER_LABELS: Record<string, string> = {
  telegram: 'Telegram',
  google: 'Google',
  yandex: 'Яндекс',
  apple: 'Apple',
};

export function OAuthButtons({ providers }: { providers: string[] }) {
  if (!providers.length) return null;

  return (
    <section className="oauth-auth" aria-label="Вход через другой сервис">
      <p className="muted">Продолжить с аккаунтом</p>
      <div className="oauth-auth__grid">
        {providers.map((provider) => (
          <a
            key={provider}
            className={`oauth-button oauth-button--${provider}`}
            href={`/api/v1/auth/oauth/${provider}/start`}
          >
            <span aria-hidden="true">
              {provider === 'telegram' ? '✦' : (provider[0]?.toUpperCase() ?? '?')}
            </span>
            {PROVIDER_LABELS[provider] ?? provider}
          </a>
        ))}
      </div>
    </section>
  );
}
