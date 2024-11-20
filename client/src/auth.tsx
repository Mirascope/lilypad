import { LoginType, UserSession } from "@/types/types";
import { useLoginMutation } from "@/utils/auth";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useState,
} from "react";

export interface AuthContext {
  isAuthenticated: boolean;
  login: (loginType: LoginType) => Promise<void>;
  logout: () => Promise<void>;
  user: UserSession | null;
  setSession: (user: UserSession | null) => void;
}

const AuthContext = createContext<AuthContext | null>(null);

const AUTH_STORAGE_KEY = "auth-session";

const saveToStorage = (session: UserSession | null) => {
  if (session) {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  } else {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
};

const loadFromStorage = (): UserSession | null => {
  const stored = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!stored) return null;

  try {
    const session = JSON.parse(stored) as UserSession;
    // Check if session has expired
    if (Date.now() > new Date(session.expires_at).getTime()) {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      return null;
    }
    return session;
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(loadFromStorage());
  const isAuthenticated = !!user;
  const loginMutation = useLoginMutation();

  const setSession = useCallback((newSession: UserSession | null) => {
    setUser(newSession);
    saveToStorage(newSession);
  }, []);

  const logout = useCallback(async () => {
    setUser(null);
    saveToStorage(null);
  }, []);

  const login = useCallback(async (loginType: LoginType) => {
    const result = await loginMutation.mutateAsync({ loginType });
    window.location.assign(result.authorization_url);
  }, []);
  return (
    <AuthContext.Provider
      value={{ isAuthenticated, user, login, logout, setSession }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
