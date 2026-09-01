import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AvatarSettings } from '../../../../src/features/profile/AvatarSettings';

const { api, authState, updateUser } = vi.hoisted(() => ({
  api: vi.fn(),
  authState: {
    user: {
      id: 7,
      first_name: 'Анна',
      username: 'anna',
      photo_url: null as string | null,
      custom_avatar: null as null | {
        content_type: 'image/webp';
        byte_size: number;
        width: 512;
        height: 512;
        updated_at: string;
      },
      profile: { full_name: 'Анна Петрова' },
    },
  },
  updateUser: vi.fn(),
}));

vi.mock('../../../../src/app/AuthProvider', () => ({
  useAuth: () => ({ user: authState.user, updateUser }),
}));

vi.mock('../../../../src/shared/api/client', () => ({
  api,
  ApiError: class ApiError extends Error {},
}));

vi.mock('../../../../src/shared/account/AccountIdentity', () => ({
  AccountAvatar: ({ previewUrl }: { previewUrl?: string | null }) => (
    <span data-testid="avatar-preview" data-preview-url={previewUrl ?? ''} />
  ),
}));

describe('AvatarSettings', () => {
  beforeEach(() => {
    api.mockReset();
    updateUser.mockReset();
    authState.user.photo_url = null;
    authState.user.custom_avatar = null;
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: vi.fn(() => 'blob:selected-avatar'),
      revokeObjectURL: vi.fn(),
    });
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('keeps a selected file for preview and updates the shared user after save', async () => {
    api.mockResolvedValue({ ...authState.user, custom_avatar: { updated_at: '2030-01-02' } });
    render(<AvatarSettings />);

    expect(screen.getByText('Используется нейтральный emoji')).toBeInTheDocument();
    const file = new File(['png'], 'portrait.png', { type: 'image/png' });
    fireEvent.change(screen.getByLabelText('Выбрать изображение для аватара'), {
      target: { files: [file] },
    });
    expect(screen.getByTestId('avatar-preview')).toHaveAttribute(
      'data-preview-url',
      'blob:selected-avatar',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Сохранить аватар' }));
    await waitFor(() => expect(api).toHaveBeenCalledOnce());
    const options = api.mock.calls[0]?.[1];
    expect(options.body).toBeInstanceOf(FormData);
    const uploadedFile = (options.body as FormData).get('file') as File;
    expect(uploadedFile).toMatchObject({ name: file.name, size: file.size, type: file.type });
    await waitFor(() => expect(updateUser).toHaveBeenCalledOnce());
    expect(screen.getByRole('status')).toHaveTextContent('Аватар сохранён');
  });

  it('shows a client validation error for unsupported files without a request', () => {
    render(<AvatarSettings />);
    fireEvent.change(screen.getByLabelText('Выбрать изображение для аватара'), {
      target: { files: [new File(['heic'], 'portrait.heic', { type: 'image/heic' })] },
    });

    expect(screen.getByRole('alert')).toHaveTextContent('Поддерживаются только JPEG, PNG и WebP');
    expect(api).not.toHaveBeenCalled();
  });

  it('requires explicit confirmation and applies provider fallback after delete', async () => {
    authState.user.photo_url = 'https://provider.example.test/avatar.jpg';
    authState.user.custom_avatar = {
      content_type: 'image/webp',
      byte_size: 10_000,
      width: 512,
      height: 512,
      updated_at: '2030-01-02T12:00:00',
    };
    api.mockResolvedValue({ ...authState.user, custom_avatar: null });
    render(<AvatarSettings />);

    fireEvent.click(screen.getByRole('button', { name: 'Удалить свой аватар' }));
    const confirmation = screen.getByRole('alertdialog', { name: 'Удалить свой аватар?' });
    expect(confirmation).toHaveTextContent('Фото из способа входа или emoji');
    fireEvent.click(screen.getByRole('button', { name: /^Удалить$/ }));

    await waitFor(() =>
      expect(api).toHaveBeenCalledWith('/api/v1/me/avatar', { method: 'DELETE' }),
    );
    expect(updateUser).toHaveBeenCalledOnce();
  });
});
