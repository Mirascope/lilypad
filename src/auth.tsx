import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { useNavigate } from '@tanstack/react-router';
import type { PublicUser } from '@/db/schema';
import { useAuthStatus } from '@/src/api/auth/status';
import { useLogout } from '@/src/api/auth/logout';

type AuthContextType = {
  user: PublicUser | null;
  isLoading: boolean;
  loginWithGitHub: () => void;
  loginWithGoogle: () => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<PublicUser | null>(null);
  const navigate = useNavigate();

  // Use TanStack Query hooks
  const { data: authUser, isLoading: isCheckingAuth } = useAuthStatus();
  const logoutMutation = useLogout();

  // Update user state when auth status changes
  useEffect(() => {
    setUser(authUser || null);
  }, [authUser]);

  useEffect(() => {
    // Check for auth success in URL params (from OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const userData = urlParams.get('user');

    if (success === 'true' && userData) {
      try {
        const user = JSON.parse(decodeURIComponent(userData)) as PublicUser;
        setUser(user);

        // Clean up URL
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname
        );

        void navigate({ to: '/', replace: true });
      } catch (error) {
        console.error('Failed to process auth callback:', error);
      }
    }
  }, [navigate]);

  const loginWithGitHub = () => {
    window.location.href = '/auth/github';
  };

  const loginWithGoogle = () => {
    window.location.href = '/auth/google';
  };

  const logout = async () => {
    try {
      await logoutMutation.mutateAsync();
    } catch (error) {
      console.error('Failed to logout:', error);
    }

    // Clear user state (mutation already clears query cache)
    setUser(null);
  };

  const value = {
    user,
    isLoading: isCheckingAuth,
    loginWithGitHub,
    loginWithGoogle,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
