import type { ProgramTemplate } from '../../shared/api/types';

type EditableTemplate = Pick<ProgramTemplate, 'can_edit' | 'is_example' | 'title'>;

export function shouldSaveTemplateAsCopy(template: EditableTemplate): boolean {
  return template.is_example || !template.can_edit;
}

export function templateDraftTitle(template: EditableTemplate, saveAsCopy: boolean): string {
  return saveAsCopy ? `${template.title} — моя` : template.title;
}

export function scheduleWeekdaysForSave(dayCount: number, weekdays: number[]): number[] | null {
  return dayCount > 7 ? null : weekdays;
}
