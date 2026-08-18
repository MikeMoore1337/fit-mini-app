import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { configuredOAuthProviders, OAuthButtons } from '../../../../src/features/auth/OAuthButtons';

describe('OAuthButtons', () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState(null, '', '/');
  });

  it('renders Google, Yandex and VK ID login links', () => {
    render(<OAuthButtons providers={['google', 'yandex', 'vk']} nextPath="/app" />);

    expect(screen.getByRole('link', { name: 'Продолжить с Google' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/google/start?next=%2Fapp',
    );
    expect(screen.getByRole('link', { name: 'Войти с Яндекс ID' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/yandex/start?next=%2Fapp',
    );
    expect(screen.getByRole('link', { name: 'Войти с VK ID' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/vk/start?next=%2Fapp',
    );
    expect(document.querySelectorAll('.oauth-button__icon svg')).toHaveLength(1);
    expect(
      screen.getByRole('link', { name: 'Продолжить с Google' }).querySelector('img'),
    ).toHaveAttribute('src', '/assets/providers/google.png');
    expect(
      screen.getByRole('link', { name: 'Войти с Яндекс ID' }).querySelector('img'),
    ).toHaveAttribute('src', '/assets/providers/yandex.webp');
  });

  it('preserves a safe invitation path for VK ID login', () => {
    render(<OAuthButtons providers={['vk']} nextPath="/join/Abc_12345678901234567890" />);

    expect(screen.getByRole('link', { name: 'Войти с VK ID' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/vk/start?next=%2Fjoin%2FAbc_12345678901234567890',
    );
  });

  it('keeps only known configured providers in the product order', () => {
    expect(configuredOAuthProviders(['apple', 'unknown', 'vk', 'telegram', 'google'])).toEqual([
      'telegram',
      'google',
      'vk',
      'apple',
    ]);
  });
});
