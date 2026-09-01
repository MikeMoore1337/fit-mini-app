import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AvatarSettings } from '../../../../src/features/profile/AvatarSettings';
import { FeedbackProvider } from '../../../../src/shared/ui/FeedbackProvider';
import { createTelegramMock } from '../../../helpers/telegramMock';

const { api, authState, onClose, updateUser } = vi.hoisted(() => ({
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
  onClose: vi.fn(),
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
  const renderEditor = () =>
    render(
      <FeedbackProvider>
        <AvatarSettings open onClose={onClose} />
      </FeedbackProvider>,
    );

  beforeEach(() => {
    api.mockReset();
    updateUser.mockReset();
    onClose.mockReset();
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
    delete window.Telegram;
    vi.unstubAllGlobals();
  });

  it('keeps a selected file for preview and updates the shared user after save', async () => {
    api.mockResolvedValue({ ...authState.user, custom_avatar: { updated_at: '2030-01-02' } });
    renderEditor();

    expect(screen.getByRole('dialog', { name: 'Аватар' })).toBeInTheDocument();
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
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('shows a client validation error for unsupported files without a request', () => {
    renderEditor();
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
    renderEditor();

    fireEvent.click(screen.getByRole('button', { name: 'Удалить свой аватар' }));
    const confirmation = screen.getByRole('alertdialog', { name: 'Удалить свой аватар?' });
    expect(confirmation).toHaveTextContent('Фото из способа входа или emoji');
    fireEvent.click(within(confirmation).getByRole('button', { name: /^Удалить$/ }));

    await waitFor(() =>
      expect(api).toHaveBeenCalledWith('/api/v1/me/avatar', { method: 'DELETE' }),
    );
    expect(updateUser).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('closes only delete confirmation on Escape and restores its exact trigger', async () => {
    authState.user.custom_avatar = {
      content_type: 'image/webp',
      byte_size: 10_000,
      width: 512,
      height: 512,
      updated_at: '2030-01-02T12:00:00',
    };
    renderEditor();

    const deleteAvatar = screen.getByRole('button', { name: 'Удалить свой аватар' });
    fireEvent.click(deleteAvatar);
    const confirmation = screen.getByRole('alertdialog', { name: 'Удалить свой аватар?' });
    await waitFor(() =>
      expect(within(confirmation).getByRole('button', { name: 'Отмена' })).toHaveFocus(),
    );

    fireEvent.keyDown(confirmation, { key: 'Escape' });

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    expect(screen.getByRole('dialog', { name: 'Аватар' })).toBeInTheDocument();
    await waitFor(() => expect(deleteAvatar).toHaveFocus());
    expect(onClose).not.toHaveBeenCalled();
  });

  it('uses Telegram Back to close only delete confirmation and restore its exact trigger', async () => {
    const telegram = createTelegramMock();
    window.Telegram = { WebApp: telegram.webApp };
    authState.user.custom_avatar = {
      content_type: 'image/webp',
      byte_size: 10_000,
      width: 512,
      height: 512,
      updated_at: '2030-01-02T12:00:00',
    };
    renderEditor();

    const deleteAvatar = screen.getByRole('button', { name: 'Удалить свой аватар' });
    fireEvent.click(deleteAvatar);
    await waitFor(() =>
      expect(
        within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Отмена' }),
      ).toHaveFocus(),
    );

    telegram.clickBack();

    await waitFor(() => expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument());
    expect(screen.getByRole('dialog', { name: 'Аватар' })).toBeInTheDocument();
    await waitFor(() => expect(deleteAvatar).toHaveFocus());
    expect(onClose).not.toHaveBeenCalled();
  });

  it('keeps delete confirmation open after an error and retries the request', async () => {
    authState.user.custom_avatar = {
      content_type: 'image/webp',
      byte_size: 10_000,
      width: 512,
      height: 512,
      updated_at: '2030-01-02T12:00:00',
    };
    api.mockRejectedValueOnce(new Error('Сервис временно недоступен')).mockResolvedValueOnce({
      ...authState.user,
      custom_avatar: null,
    });
    renderEditor();

    fireEvent.click(screen.getByRole('button', { name: 'Удалить свой аватар' }));
    const confirmation = screen.getByRole('alertdialog', { name: 'Удалить свой аватар?' });
    fireEvent.click(within(confirmation).getByRole('button', { name: /^Удалить$/ }));

    await waitFor(() =>
      expect(within(confirmation).getByRole('alert')).toHaveTextContent(
        'Сервис временно недоступен',
      ),
    );
    fireEvent.click(within(confirmation).getByRole('button', { name: 'Повторить удаление' }));

    await waitFor(() => expect(api).toHaveBeenCalledTimes(2));
    expect(updateUser).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });
});
