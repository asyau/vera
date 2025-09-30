/**
 * Notification Store using Zustand
 * Implements MVP pattern - Model layer for notification state
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  read: boolean;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface NotificationPreferences {
  channels: {
    in_app: boolean;
    email: boolean;
    slack: boolean;
    teams: boolean;
    push: boolean;
  };
  notification_types: Record<string, string[]>;
  quiet_hours: {
    enabled: boolean;
    start_time: string;
    end_time: string;
  };
}

export interface NotificationState {
  // State
  notifications: Notification[];
  preferences: NotificationPreferences | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;

  // Preferences
  fetchPreferences: () => Promise<void>;
  updatePreferences: (preferences: NotificationPreferences) => Promise<void>;

  // Utils
  clearError: () => void;

  // Selectors
  getUnreadCount: () => number;
  getNotificationsByType: (type: string) => Notification[];
  getRecentNotifications: (limit?: number) => Notification[];
}

export const useNotificationStore = create<NotificationState>()(
  devtools(
    (set, get) => ({
      // Initial state
      notifications: [],
      preferences: null,
      isLoading: false,
      error: null,

      // Actions
      addNotification: (notificationData) => {
        const notification: Notification = {
          ...notificationData,
          id: `notification-${Date.now()}-${Math.random()}`,
          timestamp: new Date().toISOString(),
          read: false
        };

        set(state => ({
          notifications: [notification, ...state.notifications]
        }));

        // Auto-remove after 5 seconds for non-urgent notifications
        if (notification.priority !== 'urgent') {
          setTimeout(() => {
            get().removeNotification(notification.id);
          }, 5000);
        }
      },

      removeNotification: (id: string) => {
        set(state => ({
          notifications: state.notifications.filter(n => n.id !== id)
        }));
      },

      markAsRead: (id: string) => {
        set(state => ({
          notifications: state.notifications.map(n =>
            n.id === id ? { ...n, read: true } : n
          )
        }));
      },

      markAllAsRead: () => {
        set(state => ({
          notifications: state.notifications.map(n => ({ ...n, read: true }))
        }));
      },

      clearNotifications: () => {
        set({ notifications: [] });
      },

      // Preferences
      fetchPreferences: async () => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call to fetch preferences
          const preferences: NotificationPreferences = {
            channels: {
              in_app: true,
              email: true,
              slack: false,
              teams: false,
              push: true
            },
            notification_types: {
              task_assigned: ['in_app', 'email'],
              task_due_soon: ['in_app', 'push'],
              task_overdue: ['in_app', 'email', 'push'],
              new_message: ['in_app', 'push'],
              daily_briefing: ['in_app', 'email']
            },
            quiet_hours: {
              enabled: false,
              start_time: '22:00',
              end_time: '08:00'
            }
          };

          set({ preferences, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch preferences',
            isLoading: false
          });
        }
      },

      updatePreferences: async (preferences: NotificationPreferences) => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call to update preferences
          set({ preferences, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to update preferences',
            isLoading: false
          });
        }
      },

      // Utils
      clearError: () => {
        set({ error: null });
      },

      // Selectors
      getUnreadCount: () => {
        const { notifications } = get();
        return notifications.filter(n => !n.read).length;
      },

      getNotificationsByType: (type: string) => {
        const { notifications } = get();
        return notifications.filter(n => n.type === type);
      },

      getRecentNotifications: (limit = 10) => {
        const { notifications } = get();
        return notifications
          .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .slice(0, limit);
      }
    }),
    {
      name: 'notification-store'
    }
  )
);
