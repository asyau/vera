import React, { createContext, useState, useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, User } from '@/lib/api';

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string, role: 'employee' | 'supervisor') => Promise<void>;
  logout: () => void;
  hasRole: (role: 'employee' | 'supervisor') => boolean;
  hasAnyRole: (roles: ('employee' | 'supervisor')[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  const isAuthenticated = !!user;

  // Check for existing session on app load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('authToken');
        if (token) {
          // Verify token and get user info
          const userData = await api.getCurrentUser();
          setUser(userData);
        }
      } catch (error) {
        // Token is invalid, remove it
        localStorage.removeItem('authToken');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const { token, user: userData } = await api.login({ email, password });
      
      // Store token
      localStorage.setItem('authToken', token);
      
      setUser(userData);
      navigate('/');
    } catch (error: any) {
      throw new Error(error.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (name: string, email: string, password: string, role: 'employee' | 'supervisor') => {
    try {
      setIsLoading(true);
      const { token, user: userData } = await api.signup({ 
        name, 
        email, 
        password, 
        role 
      });
      
      // Store token
      localStorage.setItem('authToken', token);
      
      setUser(userData);
      navigate('/');
    } catch (error: any) {
      throw new Error(error.message || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
    navigate('/login');
  };

  const hasRole = (role: 'employee' | 'supervisor') => {
    return user?.role === role;
  };

  const hasAnyRole = (roles: ('employee' | 'supervisor')[]) => {
    return user ? roles.includes(user.role) : false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        signup,
        logout,
        hasRole,
        hasAnyRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 