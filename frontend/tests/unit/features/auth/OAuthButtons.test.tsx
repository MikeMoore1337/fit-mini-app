import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { OAuthButtons } from '../../../../src/features/auth/OAuthButtons';

describe('OAuthButtons', () => {
  afterEach(() => {
    cleanup();
    window.history.replaceState(null, '', '/');
  });

  it('renders Google, Yandex and VK ID login links', () => {
    render(<OAuthButtons providers={['google', 'yandex', 'vk']} />);

    expect(screen.getByRole('link', { name: 'Google' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/google/start',
    );
    expect(screen.getByRole('link', { name: 'Яндекс' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/yandex/start',
    );
    expect(screen.getByRole('link', { name: 'VK ID' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/vk/start',
    );
    expect(document.querySelectorAll('.oauth-button__icon svg')).toHaveLength(3);
  });

  it('preserves a safe invitation path for VK ID login', () => {
    window.history.replaceState(null, '', '/join/Abc_12345678901234567890');
    render(<OAuthButtons providers={['vk']} />);

    expect(screen.getByRole('link', { name: 'VK ID' })).toHaveAttribute(
      'href',
      '/api/v1/auth/oauth/vk/start?next=%2Fjoin%2FAbc_12345678901234567890',
    );
  });
});
