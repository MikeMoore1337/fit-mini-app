import { AppLink } from '../shared/navigation/router';
import { Card } from '../shared/ui/common';

export default function NotFoundPage() {
  return (
    <main className="container">
      <Card collapsible={false} title="Страница не найдена">
        <AppLink className="button-link" to="/app">
          Вернуться в Your Fitness Coach
        </AppLink>
      </Card>
    </main>
  );
}
