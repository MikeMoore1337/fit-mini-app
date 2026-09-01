import { cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AccountAvatar } from '../../../../src/shared/account/AccountIdentity';

const { apiFile } = vi.hoisted(() => ({ apiFile: vi.fn() }));

vi.mock('../../../../src/shared/api/client', () => ({ apiFile }));

describe('AccountAvatar', () => {
  beforeEach(() => {
    apiFile.mockReset();
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:private-avatar'),
      revokeObjectURL: vi.fn(),
    });
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('uses deterministic emoji when no image source exists', () => {
    const view = render(<AccountAvatar name="Анна Петрова" />);
    const first = view.container.textContent;
    view.rerender(<AccountAvatar name="Анна Петрова" />);
    expect(view.container.textContent).toBe(first);
    expect(first).toMatch(/🏋️|💪|🏃|🚴|🥗|⚡|🎯|🔥/);
  });

  it('prefers private bytes and falls back through provider photo to emoji', async () => {
    apiFile.mockResolvedValue({
      blob: new Blob(['private'], { type: 'image/webp' }),
      filename: null,
    });
    const view = render(
      <AccountAvatar
        customAvatarVersion="2030-01-02T12:00:00"
        name="Анна Петрова"
        photoUrl="https://provider.example.test/avatar.jpg"
      />,
    );

    await waitFor(() =>
      expect(view.container.querySelector('img')).toHaveAttribute('src', 'blob:private-avatar'),
    );
    fireEvent.error(view.container.querySelector('img')!);
    expect(view.container.querySelector('img')).toHaveAttribute(
      'src',
      'https://provider.example.test/avatar.jpg',
    );
    fireEvent.error(view.container.querySelector('img')!);
    expect(view.container.querySelector('img')).not.toBeInTheDocument();
    expect(view.container).toHaveTextContent(/🏋️|💪|🏃|🚴|🥗|⚡|🎯|🔥/);
  });
});
