import { useState, type MouseEventHandler, type ReactNode } from 'react';
import { markProductLoginStarted } from '../../shared/analytics/productEvents';
import { oauthStartHref } from '../../shared/auth/oauthRecovery';
import { Icon } from '../../shared/ui/Icon';

const PROVIDER_LABELS: Record<string, string> = {
  telegram: 'Войти через Telegram',
  google: 'Продолжить с Google',
  yandex: 'Войти с Яндекс ID',
  vk: 'Войти с VK ID',
  apple: 'Войти с Apple',
};

const PROVIDER_ORDER = ['telegram', 'google', 'yandex', 'vk', 'apple'];

export function configuredOAuthProviders(providers: string[]): string[] {
  const configured = new Set(providers.map((provider) => provider.trim().toLowerCase()));
  return PROVIDER_ORDER.filter((provider) => configured.has(provider));
}

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
        <path d="m9.78 18.65.28-4.23 7.68-6.92c.34-.31-.07-.46-.52-.19l-9.48 5.99-4.1-1.3c-.88-.25-.89-.86.2-1.29l16-6.17c.73-.33 1.43.18 1.15 1.3l-2.72 12.81c-.19.91-.73 1.13-1.49.7l-4.15-3.07-2 1.93c-.23.22-.41.41-.85.41Z" />
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

export function OAuthProviderButton({
  busy = false,
  children,
  disabled = false,
  href,
  onClick,
  provider,
  rel,
  target,
}: {
  busy?: boolean;
  children: ReactNode;
  disabled?: boolean;
  href?: string;
  onClick?: MouseEventHandler<HTMLAnchorElement | HTMLButtonElement>;
  provider: string;
  rel?: string;
  target?: string;
}) {
  const content = (
    <>
      <span className="oauth-button__icon" aria-hidden="true">
        <ProviderIcon provider={provider} />
      </span>
      <span className="oauth-button__label">{children}</span>
      <Icon className="oauth-button__arrow" name="arrow-right" size={16} />
    </>
  );
  const className = `oauth-button oauth-button--${provider}`;

  if (href) {
    return (
      <a
        className={className}
        href={href}
        target={target}
        rel={rel}
        aria-disabled={disabled || undefined}
        aria-busy={busy || undefined}
        data-motion-feedback={busy ? 'busy' : undefined}
        onClick={(event) => {
          if (disabled) {
            event.preventDefault();
            return;
          }
          onClick?.(event);
        }}
      >
        {content}
      </a>
    );
  }

  return (
    <button
      className={className}
      type="button"
      disabled={disabled}
      aria-busy={busy || undefined}
      data-motion-feedback={busy ? 'busy' : undefined}
      onClick={onClick as MouseEventHandler<HTMLButtonElement> | undefined}
    >
      {content}
    </button>
  );
}

export function OAuthButtons({
  providers,
  nextPath,
}: {
  providers: string[];
  nextPath?: string | null;
}) {
  const [redirectingProvider, setRedirectingProvider] = useState<string | null>(null);
  const configuredProviders = configuredOAuthProviders(providers);
  if (!configuredProviders.length) return null;

  return (
    <section className="oauth-auth" aria-label="Вход через другой сервис">
      <p className="muted">Войти с помощью</p>
      <div className="oauth-auth__grid">
        {configuredProviders.map((provider) => {
          const href = oauthStartHref(provider, nextPath);
          if (!href) return null;
          return (
            <OAuthProviderButton
              key={provider}
              provider={provider}
              href={href}
              disabled={redirectingProvider !== null}
              busy={redirectingProvider === provider}
              onClick={(event) => {
                if (redirectingProvider !== null) {
                  event.preventDefault();
                  return;
                }
                setRedirectingProvider(provider);
                markProductLoginStarted();
              }}
            >
              {redirectingProvider === provider ? 'Переходим…' : PROVIDER_LABELS[provider]}
            </OAuthProviderButton>
          );
        })}
      </div>
    </section>
  );
}
