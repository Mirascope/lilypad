import { useAuth } from '@/src/auth';
import type { ReactNode } from 'react';
import { LoginPage } from './login-page';

export function Protected({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
