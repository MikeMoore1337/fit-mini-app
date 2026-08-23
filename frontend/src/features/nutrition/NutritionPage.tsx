import type { NutritionTarget } from '../../shared/api/types';
import { AppLink } from '../../shared/navigation/router';
import { NutritionDiary } from './NutritionDiary';
import { NutritionForm } from './NutritionForm';

export function NutritionPage({
  initial,
  initialDate,
  onSaved,
  returnPath,
  timeZone,
}: {
  initial?: NutritionTarget | null;
  initialDate?: string;
  onSaved?: () => void | Promise<void>;
  returnPath?: string;
  timeZone?: string | null;
}) {
  return (
    <div className="nutrition-experience">
      {returnPath && (
        <nav aria-label="Возврат к отчёту по питанию" className="nutrition-report-return">
          <AppLink className="button-link secondary-link" to={returnPath}>
            К отчёту по питанию
          </AppLink>
        </nav>
      )}
      <NutritionDiary initialDate={initialDate} timeZone={timeZone} />
      <div id="nutrition-target-settings" className="nutrition-target-settings">
        <NutritionForm initial={initial} timeZone={timeZone} onSaved={onSaved} />
      </div>
    </div>
  );
}
