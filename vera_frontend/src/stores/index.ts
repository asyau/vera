/**
 * Central store index - exports all Zustand stores
 * Implements the MVP pattern with proper state management
 */

export { useAuthStore } from './authStore';
export { useTaskStore } from './taskStore';
export { useChatStore } from './chatStore';
export { useNotificationStore } from './notificationStore';
export { useUIStore } from './uiStore';
export { useTeamStore } from './teamStore';

// Store types
export type { AuthState } from './authStore';
export type { TaskState } from './taskStore';
export type { ChatState } from './chatStore';
export type { NotificationState } from './notificationStore';
export type { UIState } from './uiStore';
export type { TeamState } from './teamStore';
