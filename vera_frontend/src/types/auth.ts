/**
 * Authentication-related type definitions
 */

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: 'employee' | 'supervisor' | 'admin';
  company_id: string;
  team_id: string | null;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  preferences?: Record<string, any>;
  notification_preferences?: Record<string, any>;
  // Additional fields for team dashboard
  team_name?: string;
  company_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
  role: string;
}

export interface AuthResponse {
  token: string;
  user: AuthUser;
}
