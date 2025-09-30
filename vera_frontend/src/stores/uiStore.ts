/**
 * UI State Store using Zustand
 * Implements MVP pattern - Model layer for UI state management
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type ViewMode = 'chat' | 'tasks' | 'messaging' | 'team-dashboard';
export type Theme = 'light' | 'dark' | 'system';
export type SidebarState = 'expanded' | 'collapsed' | 'hidden';

export interface UIState {
  // Layout state
  viewMode: ViewMode;
  sidebarState: SidebarState;
  theme: Theme;

  // Modal and dialog state
  modals: Record<string, boolean>;
  activeModal: string | null;

  // Loading states
  globalLoading: boolean;
  loadingStates: Record<string, boolean>;

  // Toast/notification UI state
  toasts: Array<{
    id: string;
    message: string;
    type: 'success' | 'error' | 'info' | 'warning';
    duration?: number;
  }>;

  // Form state
  unsavedChanges: Record<string, boolean>;

  // Mobile responsiveness
  isMobile: boolean;
  screenSize: 'sm' | 'md' | 'lg' | 'xl';

  // Actions - Layout
  setViewMode: (mode: ViewMode) => void;
  setSidebarState: (state: SidebarState) => void;
  toggleSidebar: () => void;
  setTheme: (theme: Theme) => void;

  // Actions - Modals
  openModal: (modalId: string) => void;
  closeModal: (modalId: string) => void;
  closeAllModals: () => void;
  isModalOpen: (modalId: string) => boolean;

  // Actions - Loading
  setGlobalLoading: (loading: boolean) => void;
  setLoading: (key: string, loading: boolean) => void;
  isLoading: (key: string) => boolean;

  // Actions - Toasts
  addToast: (toast: Omit<UIState['toasts'][0], 'id'>) => string;
  removeToast: (id: string) => void;
  clearToasts: () => void;

  // Actions - Forms
  setUnsavedChanges: (formId: string, hasChanges: boolean) => void;
  hasUnsavedChanges: (formId?: string) => boolean;
  clearUnsavedChanges: (formId?: string) => void;

  // Actions - Responsive
  setScreenSize: (size: 'sm' | 'md' | 'lg' | 'xl') => void;
  setIsMobile: (isMobile: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      // Initial state
      viewMode: 'chat',
      sidebarState: 'expanded',
      theme: 'system',

      modals: {},
      activeModal: null,

      globalLoading: false,
      loadingStates: {},

      toasts: [],

      unsavedChanges: {},

      isMobile: false,
      screenSize: 'lg',

      // Layout actions
      setViewMode: (mode: ViewMode) => {
        set({ viewMode: mode });
      },

      setSidebarState: (state: SidebarState) => {
        set({ sidebarState: state });
      },

      toggleSidebar: () => {
        const { sidebarState } = get();
        const newState = sidebarState === 'expanded' ? 'collapsed' : 'expanded';
        set({ sidebarState: newState });
      },

      setTheme: (theme: Theme) => {
        set({ theme });

        // Apply theme to document
        const root = document.documentElement;
        if (theme === 'dark') {
          root.classList.add('dark');
        } else if (theme === 'light') {
          root.classList.remove('dark');
        } else {
          // System theme
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
          if (prefersDark) {
            root.classList.add('dark');
          } else {
            root.classList.remove('dark');
          }
        }
      },

      // Modal actions
      openModal: (modalId: string) => {
        set(state => ({
          modals: { ...state.modals, [modalId]: true },
          activeModal: modalId
        }));
      },

      closeModal: (modalId: string) => {
        set(state => ({
          modals: { ...state.modals, [modalId]: false },
          activeModal: state.activeModal === modalId ? null : state.activeModal
        }));
      },

      closeAllModals: () => {
        set(state => ({
          modals: Object.keys(state.modals).reduce((acc, key) => {
            acc[key] = false;
            return acc;
          }, {} as Record<string, boolean>),
          activeModal: null
        }));
      },

      isModalOpen: (modalId: string) => {
        const { modals } = get();
        return modals[modalId] || false;
      },

      // Loading actions
      setGlobalLoading: (loading: boolean) => {
        set({ globalLoading: loading });
      },

      setLoading: (key: string, loading: boolean) => {
        set(state => ({
          loadingStates: { ...state.loadingStates, [key]: loading }
        }));
      },

      isLoading: (key: string) => {
        const { loadingStates } = get();
        return loadingStates[key] || false;
      },

      // Toast actions
      addToast: (toastData) => {
        const id = `toast-${Date.now()}-${Math.random()}`;
        const toast = { ...toastData, id };

        set(state => ({
          toasts: [...state.toasts, toast]
        }));

        // Auto-remove toast
        const duration = toast.duration || 5000;
        setTimeout(() => {
          get().removeToast(id);
        }, duration);

        return id;
      },

      removeToast: (id: string) => {
        set(state => ({
          toasts: state.toasts.filter(toast => toast.id !== id)
        }));
      },

      clearToasts: () => {
        set({ toasts: [] });
      },

      // Form actions
      setUnsavedChanges: (formId: string, hasChanges: boolean) => {
        set(state => ({
          unsavedChanges: { ...state.unsavedChanges, [formId]: hasChanges }
        }));
      },

      hasUnsavedChanges: (formId?: string) => {
        const { unsavedChanges } = get();

        if (formId) {
          return unsavedChanges[formId] || false;
        }

        return Object.values(unsavedChanges).some(Boolean);
      },

      clearUnsavedChanges: (formId?: string) => {
        if (formId) {
          set(state => ({
            unsavedChanges: { ...state.unsavedChanges, [formId]: false }
          }));
        } else {
          set({ unsavedChanges: {} });
        }
      },

      // Responsive actions
      setScreenSize: (size: 'sm' | 'md' | 'lg' | 'xl') => {
        set({ screenSize: size });
      },

      setIsMobile: (isMobile: boolean) => {
        set({ isMobile });
      }
    }),
    {
      name: 'ui-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        viewMode: state.viewMode,
        sidebarState: state.sidebarState,
        theme: state.theme
      })
    }
  )
);
