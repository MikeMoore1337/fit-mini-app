import type { components } from './schema';

export type ApiSchemas = components['schemas'];
export type User = ApiSchemas['UserResponse'];
export type UserProfile = ApiSchemas['UserProfileResponse'];
export type UserProfileUpdate = ApiSchemas['UserProfileUpdate'];
export type Exercise = ApiSchemas['ExerciseCatalogItem'];
export type ExerciseGuide = ApiSchemas['ExerciseGuide'];
export type ProgramTemplate = ApiSchemas['ProgramTemplateResponse'];
export type ProgramTemplateCreate = ApiSchemas['ProgramTemplateCreate'];
export type Client = ApiSchemas['ClientResponse'];
export type CoachAssignedProgram = ApiSchemas['CoachAssignedProgramResponse'];
export type Workout = ApiSchemas['WorkoutTodayResponse'];
export type WorkoutScheduleItem = ApiSchemas['WorkoutScheduleItem'];
export type WorkoutHistoryItem = ApiSchemas['WorkoutHistoryItem'];
export type BodyMeasurement = ApiSchemas['BodyMeasurementResponse'];
export type BodyMeasurementSave = ApiSchemas['BodyMeasurementSave'];
export type NutritionTarget = ApiSchemas['NutritionTargetResponse'];
export type NutritionTargetSave = ApiSchemas['NutritionTargetSave'];
export type NotificationItem = ApiSchemas['NotificationResponse'];
export type NotificationSetting = ApiSchemas['NotificationSettingResponse'];
export type BillingPlan = ApiSchemas['PlanResponse'];
export type Subscription = ApiSchemas['SubscriptionResponse'];
export type AdminUser = ApiSchemas['AdminUserRow'];
export type AdminPayment = ApiSchemas['AdminPaymentRow'];
export type AdminNotification = ApiSchemas['AdminNotificationRow'];
export type AdminTemplate = ApiSchemas['AdminTemplateRow'];

export interface PublicConfig {
  app_env: string;
  enable_dev_auth: boolean;
  telegram_bot_username: string;
}

export interface CoachInvite {
  id: number;
  coach_user_id: number;
  coach_full_name?: string | null;
  coach_username?: string | null;
  created_at?: string | null;
}

export interface InviteLink {
  invite_id: number;
  url?: string | null;
  start_param: string;
  expires_at: string;
}
