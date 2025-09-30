/**
 * Authentication Store using Zustand
 * Implements MVP pattern - Model layer for authentication state
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { AuthUser } from '@/types/auth';
import { api } from '@/services/api';

export interface AuthState {
  // State
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string, role: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  hasRole: (role: string) => boolean;
  hasAnyRole: (roles: string[]) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });

        try {
          const { token, user } = await api.login({ email, password });

          // Store token in localStorage
          localStorage.setItem('authToken', token);

          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          set({
            error: error.message || 'Login failed',
            isLoading: false,
            isAuthenticated: false,
            user: null
          });
          throw error;
        }
      },

      signup: async (name: string, email: string, password: string, role: string) => {
        set({ isLoading: true, error: null });

        try {
          const { token, user } = await api.signup({
            name,
            email,
            password,
            role
          });

          // Store token in localStorage
          localStorage.setItem('authToken', token);

          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          set({
            error: error.message || 'Signup failed',
            isLoading: false,
            isAuthenticated: false,
            user: null
          });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem('authToken');
        set({
          user: null,
          isAuthenticated: false,
          error: null
        });
      },

      refreshUser: async () => {
        const token = localStorage.getItem('authToken');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true });

        try {
          const user = await api.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          });
        } catch (error: any) {
          // Token is invalid, remove it
          localStorage.removeItem('authToken');
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: 'Session expired'
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },

      hasRole: (role: string) => {
        const { user } = get();
        return user?.role === role;
      },

      hasAnyRole: (roles: string[]) => {
        const { user } = get();
        return user ? roles.includes(user.role) : false;
      }
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
);
