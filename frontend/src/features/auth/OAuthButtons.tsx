const PROVIDER_LABELS: Record<string, string> = {
  telegram: 'Telegram',
  google: 'Google',
  yandex: 'Яндекс',
  vk: 'VK ID',
  apple: 'Apple',
};

function ProviderIcon({ provider }: { provider: string }) {
  if (provider === 'telegram')
    return <svg viewBox="0 0 24 24"><path d="m21 4-3.2 16-5.8-4.2-3.1 3 .5-4.4L17.5 7 7.3 13.3l-4.2-1.5L21 4Z" /></svg>;
  if (provider === 'google')
    return <svg viewBox="0 0 24 24"><path d="M21.2 12.2c0-.7-.1-1.4-.2-2H12v3.8h5.1a4.4 4.4 0 0 1-1.9 2.9v2.5h3.1c1.8-1.7 2.9-4.2 2.9-7.2Z" /><path d="M12 21.5c2.6 0 4.8-.9 6.4-2.3l-3.1-2.5c-.9.6-2 .9-3.3.9-2.5 0-4.6-1.7-5.4-4H3.4V16a9.5 9.5 0 0 0 8.6 5.5Z" /><path d="M6.6 13.6a5.7 5.7 0 0 1 0-3.5V7.7H3.4a9.5 9.5 0 0 0 0 8.4l3.2-2.5Z" /><path d="M12 6.1c1.4 0 2.7.5 3.7 1.4l2.8-2.8A9.4 9.4 0 0 0 3.4 7.7l3.2 2.5c.8-2.4 2.9-4.1 5.4-4.1Z" /></svg>;
  if (provider === 'yandex') return <svg viewBox="0 0 24 24"><path d="M13.2 20H9.7l2.1-5.1C8.5 14.2 7 12.2 7 9.5 7 5.9 9.6 4 13.1 4H17v16h-3.3V7.2h-.8c-1.6 0-2.6.8-2.6 2.3 0 1.7 1.1 2.6 3.2 2.6v2.7L13.2 20Z" /></svg>;
  if (provider === 'vk') return <svg viewBox="0 0 24 24"><path d="M13 17.4c-5.2 0-8.2-3.6-8.3-9.6h2.6c.1 4.4 2 6.3 3.5 6.7V7.8H13v3.8c1.5-.2 3-2 3.5-3.8h2.5c-.4 2.2-2.1 4.1-3.3 4.9 1.2.7 3.1 2.4 3.8 4.7h-2.8c-.6-1.7-2-3.2-3.7-3.4v3.4Z" /></svg>;
  return <svg viewBox="0 0 24 24"><path d="M16.8 12.7c0-2.1 1.7-3.2 1.8-3.3a3.9 3.9 0 0 0-3.1-1.7c-1.3-.1-2.6.8-3.2.8s-1.6-.8-2.7-.8a4.1 4.1 0 0 0-3.5 2.1c-1.5 2.6-.4 6.4 1 8.3.7.9 1.5 2 2.6 1.9 1 0 1.5-.7 2.8-.7s1.7.7 2.8.7c1.2 0 1.9-1 2.6-1.9.8-1.1 1.1-2.2 1.1-2.3-.1 0-2.2-.8-2.2-3.1ZM14.6 6.2c.6-.8 1-1.8.9-2.9-.9 0-2.1.6-2.7 1.4-.5.6-1 1.7-.9 2.7 1.1.1 2.1-.5 2.7-1.2Z" /></svg>;
}

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
            <span className="oauth-button__icon" aria-hidden="true"><ProviderIcon provider={provider} /></span>
            {PROVIDER_LABELS[provider] ?? provider}
          </a>
        ))}
      </div>
    </section>
  );
}
