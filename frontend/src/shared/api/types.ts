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
export type WorkoutHistorySummary = ApiSchemas['WorkoutHistorySummary'];
export type BodyMeasurement = ApiSchemas['BodyMeasurementResponse'];
export type BodyMeasurementSave = ApiSchemas['BodyMeasurementSave'];
export type NutritionTarget = ApiSchemas['NutritionTargetResponse'];
export type NutritionTargetSave = ApiSchemas['NutritionTargetSave'];
export type NotificationItem = ApiSchemas['NotificationResponse'];
export type NotificationSetting = ApiSchemas['NotificationSettingResponse'];
export type AdminUser = ApiSchemas['AdminUserRow'];
export type AdminNotification = ApiSchemas['AdminNotificationRow'];
export type AdminTemplate = ApiSchemas['AdminTemplateRow'];
export type AdminCoachRoleApplication = ApiSchemas['AdminCoachRoleApplicationRow'];
export type CoachRoleApplication = ApiSchemas['CoachRoleApplicationResponse'];
export type InviteLink = ApiSchemas['CoachInviteLinkResponse'];
export type CoachInvitePreview = ApiSchemas['CoachInvitePreviewResponse'];
export type TelegramLinkCreate = ApiSchemas['TelegramLinkCreateResponse'];
export type OAuthLinkCreate = ApiSchemas['OAuthLinkCreateResponse'];
export type ProgressVolumePoint = ApiSchemas['ProgressVolumePoint'];
export type WorkoutProgress = ApiSchemas['WorkoutProgressResponse'];
export type WorkoutTimelineItem = ApiSchemas['WorkoutTimelineItem'];

export interface PublicConfig {
  app_env: string;
  enable_dev_auth: boolean;
  enable_web_auth: boolean;
  enable_email_auth: boolean;
  telegram_bot_username: string;
  oauth_providers: string[];
}
