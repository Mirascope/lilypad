import api from "@/api";
import { UserPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
export const updateActiveOrganization = async (organizationUuid: string) => {
  return (await api.put<UserPublic>(`/users/${organizationUuid}`)).data;
};

export const updateUserKeys = async (data: object) => {
  return (await api.patch<UserPublic>(`/users`, data)).data;
};

export const fetchUser = async () => {
  return (await api.get<UserPublic>(`/current-user`)).data;
};

export const fetchUsersByOrganization = async () => {
  return (await api.get<UserPublic[]>(`/users/organizations`)).data;
};

export const userQueryOptions = () =>
  queryOptions({
    queryKey: ["user"],
    queryFn: () => fetchUser(),
  });

export const usersByOrganizationQueryOptions = () =>
  queryOptions({
    queryKey: ["usersByOrganization"],
    queryFn: () => fetchUsersByOrganization(),
  });

export const useUpdateActiveOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ organizationUuid }: { organizationUuid: string }) =>
      await updateActiveOrganization(organizationUuid),
    onSuccess: (_data) => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
};

export const useUpdateUserKeysMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: object) => await updateUserKeys(data),
    onSuccess: (_data) => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
    },
  });
};
