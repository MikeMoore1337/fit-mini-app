import { describe, expect, it } from 'vitest';
import {
  scheduleWeekdaysForSave,
  shouldSaveTemplateAsCopy,
  templateDraftTitle,
} from '../../../../src/features/programs/templateEditing';

describe('template editing mode', () => {
  it('creates a personal copy for every ready-made or read-only template', () => {
    expect(
      shouldSaveTemplateAsCopy({ title: 'Системный', is_example: true, can_edit: false }),
    ).toBe(true);
    expect(
      shouldSaveTemplateAsCopy({ title: 'Публичный', is_example: false, can_edit: false }),
    ).toBe(true);
    expect(shouldSaveTemplateAsCopy({ title: 'Свой', is_example: false, can_edit: true })).toBe(
      false,
    );
  });

  it('marks a copy title and uses automatic scheduling for an eight-day cycle', () => {
    const template = { title: 'Тяни/Ноги/Толкай/Ноги', is_example: true, can_edit: false };

    expect(templateDraftTitle(template, true)).toBe('Тяни/Ноги/Толкай/Ноги — моя');
    expect(scheduleWeekdaysForSave(8, [0, 1, 2, 3, 4, 5, 6, 0])).toBeNull();
    expect(scheduleWeekdaysForSave(4, [0, 2, 4, 6])).toEqual([0, 2, 4, 6]);
  });
});
