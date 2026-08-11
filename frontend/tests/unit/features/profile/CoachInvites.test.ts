import { describe, expect, it } from 'vitest';
import { tokenFromInvite } from '../../../../src/features/profile/CoachInvites';

describe('tokenFromInvite', () => {
  const token = 'abcdefghijklmnopqrstuvwxyz_123456';

  it('accepts universal browser invitation links', () => {
    expect(tokenFromInvite(`https://app.your-fitness-coach.ru/join/${token}`)).toBe(token);
  });

  it('keeps Telegram deep links and copied codes compatible', () => {
    expect(tokenFromInvite(`https://t.me/fit_bot?startapp=trainer_${token}`)).toBe(token);
    expect(tokenFromInvite(`trainer_${token}`)).toBe(token);
  });
});
