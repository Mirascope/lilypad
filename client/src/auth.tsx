import { ProjectPublic, UserPublic } from "@/types/types";
import { AUTH_STORAGE_KEY } from "@/utils/constants";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useState,
} from "react";
export interface AuthContext {
  isAuthenticated: boolean;
  logout: () => Promise<void>;
  user: UserPublic | null;
  setSession: (user: UserPublic | null) => void;
  setProject: (project: ProjectPublic | null | undefined) => void;
  activeProject: ProjectPublic | null | undefined;
}

const AuthContext = createContext<AuthContext | null>(null);

const saveToStorage = (session: UserPublic | null) => {
  if (session) {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  } else {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  }
};

const loadFromStorage = (): UserPublic | null => {
  const stored = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!stored) return null;

  try {
    const session = JSON.parse(stored) as UserPublic;
    // TODO: Check if token is expired
    // if (Date.now() > new Date(session.expires_at).getTime()) {
    //   localStorage.removeItem(AUTH_STORAGE_KEY);
    //   return null;
    // }
    return session;
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(loadFromStorage());
  const [activeProject, setActiveProject] = useState<
    ProjectPublic | null | undefined
  >(null);
  const isAuthenticated = !!user;

  const setSession = useCallback((newSession: UserPublic | null) => {
    setUser(newSession);
    saveToStorage(newSession);
  }, []);

  const setProject = useCallback(
    (project: ProjectPublic | null | undefined) => {
      setActiveProject(project);
    },
    []
  );

  const logout = useCallback(async () => {
    setUser(null);
    saveToStorage(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        logout,
        setSession,
        setProject,
        activeProject,
      }}
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
