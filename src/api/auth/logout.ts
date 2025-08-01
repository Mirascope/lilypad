import { useMutation, useQueryClient } from '@tanstack/react-query';

async function logout(): Promise<void> {
  await fetch('/auth/logout', {
    method: 'POST',
    credentials: 'include',
  });
}

export const useLogout = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
    },
  });
};
