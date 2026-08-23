import type { NutritionTarget } from '../../shared/api/types';
import { NutritionDiary } from './NutritionDiary';
import { NutritionForm } from './NutritionForm';

export function NutritionPage({
  initial,
  onSaved,
  timeZone,
}: {
  initial?: NutritionTarget | null;
  onSaved?: () => void | Promise<void>;
  timeZone?: string | null;
}) {
  return (
    <div className="nutrition-experience">
      <NutritionDiary timeZone={timeZone} />
      <div id="nutrition-target-settings" className="nutrition-target-settings">
        <NutritionForm initial={initial} timeZone={timeZone} onSaved={onSaved} />
      </div>
    </div>
  );
}
