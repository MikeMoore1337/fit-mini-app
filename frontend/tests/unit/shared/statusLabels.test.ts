import { describe, expect, it } from 'vitest';
import { notificationStatusLabel, workoutStatusLabel } from '../../../src/shared/statusLabels';

describe('status labels', () => {
  it.each([
    ['planned', 'Запланирована'],
    ['in_progress', 'В процессе'],
    ['completed', 'Завершена'],
    ['skipped', 'Пропущена'],
    ['cancelled', 'Отменена'],
  ])('локализует статус тренировки %s', (status, label) => {
    expect(workoutStatusLabel(status)).toBe(label);
  });

  it.each([
    ['queued', 'Ожидает отправки'],
    ['processing', 'Отправляется'],
    ['sent', 'Отправлено'],
    ['failed', 'Ошибка отправки'],
    ['cancelled', 'Отменено'],
  ])('локализует статус уведомления %s', (status, label) => {
    expect(notificationStatusLabel(status)).toBe(label);
  });

  it('не показывает неизвестный код статуса пользователю', () => {
    expect(workoutStatusLabel('new_server_status')).toBe('Статус не определён');
    expect(notificationStatusLabel('new_server_status')).toBe('Статус не определён');
  });
});
