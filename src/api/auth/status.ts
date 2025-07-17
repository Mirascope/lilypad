import type { PublicUser } from '@/db/schema';
import { useQuery } from '@tanstack/react-query';

const AUTH_STALE_TIME = 5 * 60 * 1000; // 5 minutes

async function checkAuthStatus(): Promise<PublicUser | null> {
  try {
    const response = await fetch('/auth/me', {
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        return null;
      }
      throw new Error(`Auth check failed: ${response.status}`);
    }

    const data: { success: boolean; user: PublicUser } = await response.json();

    if (data.success && data.user) {
      return data.user;
    }

    return null;
  } catch (error) {
    console.error('Auth check error:', error);
    return null;
  }
}

export const useAuthStatus = () => {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: checkAuthStatus,
    retry: false,
    staleTime: AUTH_STALE_TIME,
  });
};
