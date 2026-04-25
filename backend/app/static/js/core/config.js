export const FRONTEND_VERSION = 'v29';

export const accessTokenKey = 'fit_access_token';
export const refreshTokenKey = 'fit_refresh_token';
export const sectionStoragePrefix = 'fit_section_';

export const API = {
  publicConfig: '/api/v1/public/config',
  telegramInit: '/api/v1/auth/telegram/init',
  devLogin: '/api/v1/auth/dev-login',
  me: '/api/v1/me',
  meProfile: '/api/v1/me/profile',
  detachTrainer: '/api/v1/me/trainer',
  saveNutritionTarget: '/api/v1/nutrition/targets',

  exercises: '/api/v1/programs/exercises',
  createExercise: '/api/v1/programs/exercises',
  updateExercise: (exerciseId) => `/api/v1/programs/exercises/${exerciseId}`,
  deleteExercise: (exerciseId) => `/api/v1/programs/exercises/${exerciseId}`,

  saveTemplate: '/api/v1/programs/templates',
  myTemplates: '/api/v1/programs/templates/mine',
  getTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  updateTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  assignTemplateToMe: (templateId) => `/api/v1/programs/templates/${templateId}/assign-to-me`,
  deleteTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  clients: '/api/v1/programs/clients',
  createClient: '/api/v1/programs/clients',

  todayWorkout: '/api/v1/workouts/today',
  deleteTodayWorkout: '/api/v1/workouts/today',
  startWorkout: (workoutId) => `/api/v1/workouts/${workoutId}/start`,
  finishWorkout: (workoutId) => `/api/v1/workouts/${workoutId}/finish`,
  updateSet: (setId) => `/api/v1/workouts/sets/${setId}`,
  workoutHistory: (offset, limit) => `/api/v1/workouts/history?offset=${offset}&limit=${limit}`,
  clearWorkoutHistory: '/api/v1/workouts/history',

  billingPlans: '/api/v1/billing/plans',
  billingSubscription: '/api/v1/billing/subscription',
  billingCheckout: '/api/v1/billing/checkout',
  billingMockComplete: (checkoutId) => `/api/v1/billing/mock/complete/${checkoutId}`,

  notificationsSettings: '/api/v1/notifications/settings',
  notifications: '/api/v1/notifications',
  deleteNotification: (notificationId) => `/api/v1/notifications/${notificationId}`,
};
