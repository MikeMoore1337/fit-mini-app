import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import KnowledgeHandoffPage from '../../../../src/pages/public/KnowledgeHandoffPage';

const navigate = vi.fn();

vi.mock('../../../../src/shared/navigation/router', () => ({
  useNavigation: () => ({ navigate, path: '/knowledge', search: '' }),
  AppLink: ({ to, children, ...props }: React.ComponentProps<'a'> & { to: string }) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

describe('KnowledgeHandoffPage', () => {
  afterEach(() => {
    cleanup();
    navigate.mockClear();
    delete window.Telegram;
    window.history.replaceState({}, '', '/');
  });

  it('waits for an explicit TMA click, opens the public URL and restores the app route', () => {
    const openLink = vi.fn();
    window.Telegram = { WebApp: { initData: 'signed', openLink } };
    render(<KnowledgeHandoffPage articlePath="/knowledge/training/repetitions-in-reserve" />);

    expect(openLink).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('link', { name: 'Открыть материал на сайте' }));

    expect(openLink).toHaveBeenCalledWith(
      'http://localhost:3000/knowledge/training/repetitions-in-reserve',
      { try_instant_view: false },
    );
    expect(navigate).toHaveBeenCalledWith('/app', true);
  });

  it('keeps an explicit native-link fallback when the Telegram API is unavailable', () => {
    window.history.replaceState({}, '', '/knowledge?tgWebAppPlatform=web');
    render(<KnowledgeHandoffPage articlePath="/knowledge" />);

    const link = screen.getByRole('link', { name: 'Открыть материал на сайте' });
    expect(link).toHaveAttribute('href', '/knowledge');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(screen.getByRole('link', { name: 'Вернуться в приложение' })).toHaveAttribute(
      'href',
      '/app',
    );
    expect(navigate).not.toHaveBeenCalled();
  });

  it('redirects a same-origin Web legacy route to the canonical public path', async () => {
    render(<KnowledgeHandoffPage articlePath="/knowledge/progress/how-to-read-progress" />);

    await waitFor(() =>
      expect(navigate).toHaveBeenCalledWith('/knowledge/progress/how-to-read-progress', true),
    );
  });
});
