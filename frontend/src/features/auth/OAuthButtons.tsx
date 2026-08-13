const PROVIDER_LABELS: Record<string, string> = {
  telegram: 'Telegram',
  google: 'Google',
  yandex: 'Яндекс',
  vk: 'VK ID',
  apple: 'Apple',
};

const PROVIDER_MARKS: Record<string, string> = {
  telegram: '✦',
  google: 'G',
  yandex: 'Я',
  vk: 'VK',
  apple: 'A',
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
            href={`/api/v1/auth/oauth/${provider}/start${
              window.location.pathname.startsWith('/join/')
                ? `?next=${encodeURIComponent(window.location.pathname)}`
                : ''
            }`}
          >
            <span aria-hidden="true">{PROVIDER_MARKS[provider] ?? '?'}</span>
            {PROVIDER_LABELS[provider] ?? provider}
          </a>
        ))}
      </div>
    </section>
  );
}
