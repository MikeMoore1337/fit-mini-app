export const FRONTEND_VERSION = 'v50';

export const accessTokenKey = 'fit_access_token';
export const sectionStoragePrefix = 'fit_section_';

export const API = {
  publicConfig: '/api/v1/public/config',
  telegramInit: '/api/v1/auth/telegram/init',
  devLogin: '/api/v1/auth/dev-login',
  refresh: '/api/v1/auth/refresh',
  logout: '/api/v1/auth/logout',
  me: '/api/v1/me',
  meProfile: '/api/v1/me/profile',
  detachTrainer: '/api/v1/me/trainer',
  coachInvites: '/api/v1/me/coach-invites',
  acceptCoachInvite: (inviteId) => `/api/v1/me/coach-invites/${inviteId}/accept`,
  declineCoachInvite: (inviteId) => `/api/v1/me/coach-invites/${inviteId}/decline`,
  saveNutritionTarget: '/api/v1/nutrition/targets',

  exercises: '/api/v1/programs/exercises',
  createExercise: '/api/v1/programs/exercises',
  updateExercise: (exerciseId) => `/api/v1/programs/exercises/${exerciseId}`,
  deleteExercise: (exerciseId) => `/api/v1/programs/exercises/${exerciseId}`,

  saveTemplate: '/api/v1/programs/templates',
  myTemplates: '/api/v1/programs/templates/mine',
  hiddenTemplates: '/api/v1/programs/templates/hidden',
  getTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  updateTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  assignTemplateToMe: (templateId) => `/api/v1/programs/templates/${templateId}/assign-to-me`,
  deleteTemplate: (templateId) => `/api/v1/programs/templates/${templateId}`,
  restoreTemplate: (templateId) => `/api/v1/programs/templates/${templateId}/restore`,
  clients: '/api/v1/programs/clients',
  createClient: '/api/v1/programs/clients',

  todayWorkout: '/api/v1/workouts/today',
  weekSchedule: '/api/v1/workouts/week',
  deleteTodayWorkout: '/api/v1/workouts/today',
  startWorkout: (workoutId) => `/api/v1/workouts/${workoutId}/start`,
  finishWorkout: (workoutId) => `/api/v1/workouts/${workoutId}/finish`,
  updateSet: (setId) => `/api/v1/workouts/sets/${setId}`,
  workoutHistory: (offset, limit) => `/api/v1/workouts/history?offset=${offset}&limit=${limit}`,
  clearWorkoutHistory: '/api/v1/workouts/history',
  bodyMeasurements: '/api/v1/workouts/diary',
  createBodyMeasurement: '/api/v1/workouts/diary',
  deleteBodyMeasurement: (measurementId) => `/api/v1/workouts/diary/${measurementId}`,

  billingPlans: '/api/v1/billing/plans',
  billingSubscription: '/api/v1/billing/subscription',
  billingCheckout: '/api/v1/billing/checkout',
  billingMockComplete: (checkoutId) => `/api/v1/billing/mock/complete/${checkoutId}`,

  notificationsSettings: '/api/v1/notifications/settings',
  notifications: '/api/v1/notifications',
  deleteNotification: (notificationId) => `/api/v1/notifications/${notificationId}`,
};
