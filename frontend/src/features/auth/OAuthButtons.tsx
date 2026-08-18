const PROVIDER_LABELS: Record<string, string> = {
  telegram: 'Войти через Telegram',
  google: 'Продолжить с Google',
  yandex: 'Войти с Яндекс ID',
  vk: 'Войти с VK ID',
  apple: 'Войти с Apple',
};

function ProviderIcon({ provider }: { provider: string }) {
  if (provider === 'google' || provider === 'yandex') {
    return (
      <img
        src={`/assets/providers/${provider === 'google' ? 'google.png' : 'yandex.webp'}`}
        alt=""
      />
    );
  }
  if (provider === 'telegram')
    return (
      <svg viewBox="0 0 24 24">
        <path d="m21 4-3.2 16-5.8-4.2-3.1 3 .5-4.4L17.5 7 7.3 13.3l-4.2-1.5L21 4Z" />
      </svg>
    );
  if (provider === 'vk')
    return (
      <svg viewBox="0 0 24 24">
        <path d="M13 17.4c-5.2 0-8.2-3.6-8.3-9.6h2.6c.1 4.4 2 6.3 3.5 6.7V7.8H13v3.8c1.5-.2 3-2 3.5-3.8h2.5c-.4 2.2-2.1 4.1-3.3 4.9 1.2.7 3.1 2.4 3.8 4.7h-2.8c-.6-1.7-2-3.2-3.7-3.4v3.4Z" />
      </svg>
    );
  return (
    <svg viewBox="0 0 24 24">
      <path d="M16.8 12.7c0-2.1 1.7-3.2 1.8-3.3a3.9 3.9 0 0 0-3.1-1.7c-1.3-.1-2.6.8-3.2.8s-1.6-.8-2.7-.8a4.1 4.1 0 0 0-3.5 2.1c-1.5 2.6-.4 6.4 1 8.3.7.9 1.5 2 2.6 1.9 1 0 1.5-.7 2.8-.7s1.7.7 2.8.7c1.2 0 1.9-1 2.6-1.9.8-1.1 1.1-2.2 1.1-2.3-.1 0-2.2-.8-2.2-3.1ZM14.6 6.2c.6-.8 1-1.8.9-2.9-.9 0-2.1.6-2.7 1.4-.5.6-1 1.7-.9 2.7 1.1.1 2.1-.5 2.7-1.2Z" />
    </svg>
  );
}

export function OAuthButtons({ providers }: { providers: string[] }) {
  if (!providers.length) return null;

  return (
    <section className="oauth-auth" aria-label="Вход через другой сервис">
      <p className="muted">Войти с помощью</p>
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
            <span className="oauth-button__icon" aria-hidden="true">
              <ProviderIcon provider={provider} />
            </span>
            {PROVIDER_LABELS[provider] ?? provider}
          </a>
        ))}
      </div>
    </section>
  );
}
