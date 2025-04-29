import { TraceTab } from "@/types/traces";
import { ProjectPublic, UserPublic } from "@/types/types";
import { AUTH_STORAGE_KEY, USER_CONFIG_STORAGE_KEY } from "@/utils/constants";
import { VisibilityState } from "@tanstack/react-table";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useState,
} from "react";

export interface UserConfig {
  defaultTraceTab?: TraceTab;
  defaultMessageRenderer?: "raw" | "markdown";
  tracesTableVisibilityState?: VisibilityState;
}

export interface AuthContext {
  isAuthenticated: boolean;
  logout: () => void;
  user: UserPublic | null;
  setSession: (user: UserPublic | null) => void;
  setProject: (project: ProjectPublic | null | undefined) => void;
  activeProject: ProjectPublic | null | undefined;
  updateUserConfig: (userConfigUpdate: Partial<UserConfig>) => void;
  userConfig: UserConfig | null;
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

const loadUserConfigFromStorage = (): UserConfig | null => {
  const stored = localStorage.getItem(USER_CONFIG_STORAGE_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored) as UserConfig;
  } catch {
    localStorage.removeItem(USER_CONFIG_STORAGE_KEY);
    return null;
  }
};

const saveUserConfigToStorage = (config: UserConfig | null) => {
  if (config) {
    localStorage.setItem(USER_CONFIG_STORAGE_KEY, JSON.stringify(config));
  } else {
    localStorage.removeItem(USER_CONFIG_STORAGE_KEY);
  }
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(loadFromStorage());
  const [userConfig, setUserConfig] = useState<UserConfig | null>(
    loadUserConfigFromStorage()
  );
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

  const updateUserConfig = useCallback(
    (userConfigUpdate: Partial<UserConfig>) => {
      const updatedConfig = {
        ...(userConfig ?? {}),
        ...userConfigUpdate,
      };

      // Save the updated config
      setUserConfig(updatedConfig);
      saveUserConfigToStorage(updatedConfig);
    },
    [userConfig]
  );

  const logout = useCallback(() => {
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
        updateUserConfig,
        userConfig,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
