import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../app/AuthProvider';
import { AccountAvatar } from '../../shared/account/AccountIdentity';
import { api, ApiError } from '../../shared/api/client';
import type { User } from '../../shared/api/types';

const MAX_AVATAR_BYTES = 5 * 1024 * 1024;
const SUPPORTED_AVATAR_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);

function userDisplayName(user: User): string {
  return user.profile?.full_name || user.first_name || user.username || 'Пользователь';
}

function selectedFileError(file: File): string | null {
  if (file.size > MAX_AVATAR_BYTES) return 'Файл больше 5 МБ. Выберите изображение поменьше.';
  if (file.type && !SUPPORTED_AVATAR_TYPES.has(file.type)) {
    return 'Поддерживаются только JPEG, PNG и WebP. HEIC, SVG и анимация не поддерживаются.';
  }
  return null;
}

export function AvatarSettings() {
  const { updateUser, user } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);
  const chooseButtonRef = useRef<HTMLButtonElement>(null);
  const deleteButtonRef = useRef<HTMLButtonElement>(null);
  const confirmDeleteButtonRef = useRef<HTMLButtonElement>(null);
  const previewRef = useRef<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(
    () => () => {
      if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    },
    [],
  );

  useEffect(() => {
    if (confirmDelete) confirmDeleteButtonRef.current?.focus();
  }, [confirmDelete]);

  if (!user) return null;

  const clearSelection = () => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    previewRef.current = null;
    setPreviewUrl(null);
    setSelectedFile(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const chooseFile = (file: File | null) => {
    setStatus(null);
    setError(null);
    if (!file) return;
    const validationError = selectedFileError(file);
    if (validationError) {
      clearSelection();
      setError(validationError);
      return;
    }
    clearSelection();
    const objectUrl = URL.createObjectURL(file);
    previewRef.current = objectUrl;
    setPreviewUrl(objectUrl);
    setSelectedFile(file);
  };

  const saveAvatar = async () => {
    if (!selectedFile || saving) return;
    setSaving(true);
    setError(null);
    setStatus(null);
    const formData = new FormData();
    formData.append('file', selectedFile, selectedFile.name);
    try {
      const current = await api<User>('/api/v1/me/avatar', {
        method: 'PUT',
        body: formData,
        timeoutMs: 20_000,
      });
      updateUser(current);
      clearSelection();
      setStatus('Аватар сохранён и уже используется в профиле.');
    } catch (reason) {
      setError(
        reason instanceof ApiError || reason instanceof Error
          ? reason.message
          : 'Не удалось сохранить аватар. Попробуйте снова.',
      );
    } finally {
      setSaving(false);
    }
  };

  const deleteAvatar = async () => {
    if (deleting) return;
    setDeleting(true);
    setError(null);
    setStatus(null);
    try {
      const current = await api<User>('/api/v1/me/avatar', { method: 'DELETE' });
      updateUser(current);
      clearSelection();
      setConfirmDelete(false);
      requestAnimationFrame(() => chooseButtonRef.current?.focus());
      setStatus(
        current.photo_url
          ? 'Свой аватар удалён. Снова показывается фото из способа входа.'
          : 'Свой аватар удалён. Снова показывается нейтральный emoji.',
      );
    } catch (reason) {
      setError(
        reason instanceof ApiError || reason instanceof Error
          ? reason.message
          : 'Не удалось удалить аватар. Попробуйте снова.',
      );
    } finally {
      setDeleting(false);
    }
  };

  const hasCustomAvatar = Boolean(user.custom_avatar);
  const sourceLabel = selectedFile
    ? 'Предпросмотр нового изображения'
    : hasCustomAvatar
      ? 'Используется свой аватар'
      : user.photo_url
        ? 'Используется фото из способа входа'
        : 'Используется нейтральный emoji';

  return (
    <section className="profile-avatar-card" id="profile-avatar" aria-labelledby="avatar-title">
      <div className="profile-avatar-card__visual">
        <AccountAvatar
          className="profile-avatar-card__avatar"
          customAvatarVersion={user.custom_avatar?.updated_at}
          name={userDisplayName(user)}
          photoUrl={user.photo_url}
          previewUrl={previewUrl}
        />
        <span>{sourceLabel}</span>
      </div>

      <div className="profile-avatar-card__body">
        <div className="profile-avatar-card__copy">
          <span className="eyebrow">Персонализация аккаунта</span>
          <h2 id="avatar-title">Аватар</h2>
          <p>
            Выберите JPEG, PNG или WebP до 5 МБ. Перед сохранением изображение будет обрезано по
            центру до квадрата, а исходные metadata будут удалены.
          </p>
        </div>

        <input
          ref={inputRef}
          className="sr-only"
          type="file"
          accept="image/jpeg,image/png,image/webp"
          aria-label="Выбрать изображение для аватара"
          onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
        />

        <div className="profile-avatar-card__actions">
          <button
            ref={chooseButtonRef}
            type="button"
            className="secondary"
            disabled={saving || deleting}
            onClick={() => inputRef.current?.click()}
          >
            {selectedFile ? 'Выбрать другое' : hasCustomAvatar ? 'Заменить' : 'Выбрать изображение'}
          </button>
          {selectedFile && (
            <>
              <button type="button" disabled={saving} onClick={() => void saveAvatar()}>
                {saving ? 'Сохраняем…' : error ? 'Повторить сохранение' : 'Сохранить аватар'}
              </button>
              <button
                type="button"
                className="text-button"
                disabled={saving}
                onClick={() => {
                  clearSelection();
                  setError(null);
                }}
              >
                Отмена
              </button>
            </>
          )}
          {hasCustomAvatar && !selectedFile && (
            <button
              ref={deleteButtonRef}
              type="button"
              className="secondary profile-avatar-card__delete"
              disabled={deleting}
              onClick={() => setConfirmDelete(true)}
            >
              Удалить свой аватар
            </button>
          )}
        </div>

        {confirmDelete && hasCustomAvatar && (
          <div
            className="profile-avatar-delete-confirmation"
            role="alertdialog"
            aria-labelledby="avatar-delete-title"
            aria-describedby="avatar-delete-description"
            onKeyDown={(event) => {
              if (event.key !== 'Escape') return;
              setConfirmDelete(false);
              requestAnimationFrame(() => deleteButtonRef.current?.focus());
            }}
          >
            <div>
              <strong id="avatar-delete-title">Удалить свой аватар?</strong>
              <p id="avatar-delete-description">
                Свой файл будет удалён. Фото из способа входа или emoji останется доступным.
              </p>
            </div>
            <div className="profile-avatar-delete-confirmation__actions">
              <button
                ref={confirmDeleteButtonRef}
                type="button"
                className="btn-danger"
                disabled={deleting}
                onClick={() => void deleteAvatar()}
              >
                {deleting ? 'Удаляем…' : 'Удалить'}
              </button>
              <button
                type="button"
                className="secondary"
                disabled={deleting}
                onClick={() => {
                  setConfirmDelete(false);
                  requestAnimationFrame(() => deleteButtonRef.current?.focus());
                }}
              >
                Отмена
              </button>
            </div>
          </div>
        )}

        {error && (
          <p className="profile-avatar-card__message is-error" role="alert">
            {error}
          </p>
        )}
        {status && (
          <p className="profile-avatar-card__message is-success" role="status">
            {status}
          </p>
        )}
      </div>
    </section>
  );
}
