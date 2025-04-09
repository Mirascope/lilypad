import { ProjectPublic, UserPublic } from "@/types/types";
import {
  AUTH_STORAGE_KEY,
  PRIVACY_STORAGE_KEY,
  TERMS_STORAGE_KEY,
} from "@/utils/constants";
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
  setTermsVersion: (termsVersion: string) => void;
  setPrivacyPolicyVersion: (privacyPolicyVersion: string) => void;
  loadPrivacyPolicyVersion: () => string | null;
  loadTermsVersion: () => string | null;
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
        setTermsVersion: saveTermsVersionToStorage,
        setPrivacyPolicyVersion: savePrivacyPolicyVersionToStorage,
        loadPrivacyPolicyVersion: loadPrivacyPolicyVersionFromStorage,
        loadTermsVersion: loadTermsVersionFromStorage,
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
