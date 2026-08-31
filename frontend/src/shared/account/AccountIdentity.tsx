import { useState } from 'react';

const AVATAR_EMOJIS = ['🏋️', '💪', '🏃', '🚴', '🥗', '⚡', '🎯', '🔥'] as const;

function avatarFallback(name: string): string {
  const hash = Array.from(name.trim()).reduce(
    (value, character) => (value * 31 + (character.codePointAt(0) ?? 0)) >>> 0,
    0,
  );
  return AVATAR_EMOJIS[hash % AVATAR_EMOJIS.length] ?? AVATAR_EMOJIS[0];
}

export function accountRoleLabel(isRoot: boolean, isCoach: boolean): string {
  if (isRoot) return isCoach ? 'Root · Тренер' : 'Root · Личный режим';
  if (isCoach) return 'Тренер';
  return 'Клиент';
}

export function AccountAvatar({
  className = 'account-identity__avatar',
  name,
  photoUrl,
}: {
  className?: string;
  name: string;
  photoUrl?: string | null;
}) {
  const [failedPhotoUrl, setFailedPhotoUrl] = useState<string | null>(null);
  const photoFailed = Boolean(photoUrl && failedPhotoUrl === photoUrl);

  return (
    <span className={className} aria-hidden="true">
      {photoUrl && !photoFailed ? (
        <img
          src={photoUrl}
          alt=""
          referrerPolicy="no-referrer"
          onError={() => setFailedPhotoUrl(photoUrl)}
        />
      ) : (
        avatarFallback(name)
      )}
    </span>
  );
}

export function AccountIdentity({
  avatarClassName,
  className = 'account-identity',
  name,
  photoUrl,
  role,
}: {
  avatarClassName?: string;
  className?: string;
  name: string;
  photoUrl?: string | null;
  role: string;
}) {
  return (
    <span className={className}>
      <AccountAvatar className={avatarClassName} name={name} photoUrl={photoUrl} />
      <span className="account-identity__copy">
        <strong className="account-identity__name">{name}</strong>
        <small className="account-identity__role">{role}</small>
      </span>
    </span>
  );
}
