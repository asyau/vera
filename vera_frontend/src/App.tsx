import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
// Removed AuthProvider - now using Zustand stores
import { SessionProvider } from "@/contexts/SessionContext";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import { useAuthStore } from "@/stores/authStore";
import Index from "./pages/Index";
import Tasks from "./pages/Tasks";
import Users from "./pages/Users";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import Calendar from "./pages/Calendar";
import Integrations from "./pages/Integrations";
import IntegrationCallback from "./pages/IntegrationCallback";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Unauthorized from "./pages/Unauthorized";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

// Authentication initializer component
const AuthInitializer = ({ children }: { children: React.ReactNode }) => {
  const { refreshUser } = useAuthStore();

  useEffect(() => {
    // Initialize authentication state on app start
    const initializeAuth = async () => {
      const token = localStorage.getItem('authToken');
      if (token) {
        try {
          await refreshUser();
        } catch (error) {
          // If token is invalid, refreshUser will handle cleanup
          console.warn('Failed to refresh user on app initialization:', error);
        }
      }
    };

    initializeAuth();
  }, [refreshUser]);

  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthInitializer>
          <SessionProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/unauthorized" element={<Unauthorized />} />
              <Route path="/integrations/callback" element={<IntegrationCallback />} />

              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Index />
                </ProtectedRoute>
              } />
              <Route path="/tasks" element={
                <ProtectedRoute>
                  <Tasks />
                </ProtectedRoute>
              } />
              <Route path="/users" element={
                <ProtectedRoute requiredRoles={['supervisor']}>
                  <Users />
                </ProtectedRoute>
              } />
              <Route path="/profile" element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              } />
              <Route path="/settings" element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              } />
              <Route path="/calendar" element={
                <ProtectedRoute>
                  <Calendar />
                </ProtectedRoute>
              } />
              <Route path="/integrations" element={
                <ProtectedRoute>
                  <Integrations />
                </ProtectedRoute>
              } />

              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </SessionProvider>
        </AuthInitializer>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
