import { TraceTab } from "@/src/types/traces";
import { EnvironmentPublic, ProjectPublic, UserPublic } from "@/src/types/types";
import {
  AUTH_STORAGE_KEY,
  ENVIRONMENT_UUID_STORAGE_KEY,
  PRIVACY_STORAGE_KEY,
  TERMS_STORAGE_KEY,
  USER_CONFIG_STORAGE_KEY,
} from "@/src/utils/constants";
import { environmentsQueryOptions } from "@/src/utils/environments";
import { useSuspenseQuery } from "@tanstack/react-query";
import { VisibilityState } from "@tanstack/react-table";
import { createContext, ReactNode, useCallback, useContext, useState } from "react";

export interface UserConfig {
  defaultTraceTab?: TraceTab;
  defaultMessageRenderer?: "raw" | "markdown";
  tracesTableVisibilityState?: VisibilityState;
  font?: "default" | "professional" | "fun";
}

export interface AuthContext {
  isAuthenticated: boolean;
  logout: () => void;
  user: UserPublic | null;
  setSession: (user: UserPublic | null) => void;
  setProject: (project: ProjectPublic | null | undefined) => void;
  activeProject: ProjectPublic | null | undefined;
  setEnvironment: (environment: EnvironmentPublic | null | undefined) => void;
  activeEnvironment: EnvironmentPublic | null | undefined;
  setTermsVersion: (termsVersion: string) => void;
  setPrivacyPolicyVersion: (privacyPolicyVersion: string) => void;
  loadPrivacyPolicyVersion: () => string | null;
  loadTermsVersion: () => string | null;
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

const savePrivacyPolicyVersionToStorage = (privacyPolicyVersion: string) => {
  localStorage.setItem(PRIVACY_STORAGE_KEY, privacyPolicyVersion);
};

const saveTermsVersionToStorage = (termsVersion: string) => {
  localStorage.setItem(TERMS_STORAGE_KEY, termsVersion);
};

const saveEnvironmentToStorage = (environment: EnvironmentPublic | null | undefined) => {
  if (environment) {
    localStorage.setItem(ENVIRONMENT_UUID_STORAGE_KEY, JSON.stringify(environment));
  } else {
    localStorage.removeItem(ENVIRONMENT_UUID_STORAGE_KEY);
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

const loadPrivacyPolicyVersionFromStorage = (): string | null => {
  const version = localStorage.getItem(PRIVACY_STORAGE_KEY);
  if (!version) return null;
  return version;
};
const loadTermsVersionFromStorage = (): string | null => {
  const version = localStorage.getItem(TERMS_STORAGE_KEY);
  if (!version) return null;
  return version;
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

export const loadEnvironmentFromStorage = (): EnvironmentPublic | null => {
  const stored = localStorage.getItem(ENVIRONMENT_UUID_STORAGE_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored) as EnvironmentPublic;
  } catch {
    localStorage.removeItem(ENVIRONMENT_UUID_STORAGE_KEY);
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
  const { data: environments } = useSuspenseQuery(environmentsQueryOptions());
  const [user, setUser] = useState<UserPublic | null>(loadFromStorage());
  const [userConfig, setUserConfig] = useState<UserConfig | null>(loadUserConfigFromStorage());
  const [activeProject, setActiveProject] = useState<ProjectPublic | null | undefined>(null);
  const [activeEnvironment, setActiveEnvironment] = useState<EnvironmentPublic | null | undefined>(
    loadEnvironmentFromStorage() ?? (environments[0] || null)
  );
  const isAuthenticated = !!user;

  const setSession = useCallback((newSession: UserPublic | null) => {
    setUser(newSession);
    saveToStorage(newSession);
  }, []);

  const setProject = useCallback((project: ProjectPublic | null | undefined) => {
    setActiveProject(project);
  }, []);

  const setEnvironment = useCallback((environment: EnvironmentPublic | null | undefined) => {
    setActiveEnvironment(environment);
    saveEnvironmentToStorage(environment);
  }, []);

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
        setEnvironment,
        activeEnvironment,
        setTermsVersion: saveTermsVersionToStorage,
        setPrivacyPolicyVersion: savePrivacyPolicyVersionToStorage,
        loadPrivacyPolicyVersion: loadPrivacyPolicyVersionFromStorage,
        loadTermsVersion: loadTermsVersionFromStorage,
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
