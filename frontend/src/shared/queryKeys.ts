import type { QueryClient } from '@tanstack/react-query';

export const queryKeys = {
  measurements: {
    all: ['measurements'] as const,
    subject: (clientId?: number) => ['measurements', clientId ?? 'me'] as const,
  },
  progress: {
    summaries: ['workout', 'progress-summary'] as const,
    summary: (periodDays: number) => ['workout', 'progress-summary', periodDays] as const,
  },
  trainer: {
    clients: ['coach', 'clients'] as const,
    clientAnalytics: (clientId: number) => ['coach', 'client', clientId, 'analytics'] as const,
    clientSummary: (clientId: number) => ['coach', 'client', clientId, 'summary'] as const,
    clientSummaries: ['coach', 'client-summaries'] as const,
  },
  nutrition: {
    diary: ['nutrition', 'diary'] as const,
    diaryDate: (diaryDate: string) => ['nutrition', 'diary', diaryDate] as const,
  },
  notifications: {
    all: ['notifications'] as const,
  },
};

export async function invalidateMeasurementMutation(
  queryClient: QueryClient,
  clientId?: number,
): Promise<void> {
  const invalidations = [
    queryClient.invalidateQueries({ queryKey: queryKeys.measurements.subject(clientId) }),
  ];
  if (clientId == null) {
    invalidations.push(
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.summaries }),
      queryClient.invalidateQueries({ queryKey: queryKeys.nutrition.diary }),
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications.all }),
    );
  } else {
    invalidations.push(
      queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clientAnalytics(clientId) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clientSummary(clientId) }),
      queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clientSummaries }),
      queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clients }),
    );
  }
  await Promise.all(invalidations);
}

export async function invalidateNutritionSummaries(
  queryClient: QueryClient,
  clientId?: number,
): Promise<void> {
  if (clientId == null) {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.progress.summaries }),
      queryClient.invalidateQueries({ queryKey: queryKeys.nutrition.diary }),
    ]);
    return;
  }
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clientSummary(clientId) }),
    queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clientSummaries }),
    queryClient.invalidateQueries({ queryKey: queryKeys.trainer.clients }),
  ]);
}
