import api from "@/api";
import { UserOrganizationTable, UserPublic } from "@/types/types";
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
  return (await api.get<UserPublic[]>(`/user-organizations/users`)).data;
};

export const fetchUserOrganizations = async () => {
  return (await api.get<UserOrganizationTable[]>(`/user-organizations`)).data;
};

export const createUserOrganization = async () => {
  return (await api.post<UserOrganizationTable>(`/user-organizations`)).data;
};
export const deleteUserOrganization = async (userOrganizationUuid: string) => {
  return (
    await api.delete<boolean>(`/user-organizations/${userOrganizationUuid}`)
  ).data;
};

export const userQueryOptions = () =>
  queryOptions({
    queryKey: ["user"],
    queryFn: () => fetchUser(),
  });

export const userOrganizationsQueryOptions = () =>
  queryOptions({
    queryKey: ["user-organizations"],
    queryFn: () => fetchUserOrganizations(),
  });

export const usersByOrganizationQueryOptions = () =>
  queryOptions({
    queryKey: ["usersByOrganization"],
    queryFn: () => fetchUsersByOrganization(),
  });

export const useCreateUserOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => await createUserOrganization(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["user-organizations"],
      });
    },
  });
};
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

export const useDeleteUserOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectUuid: string) =>
      await deleteUserOrganization(projectUuid),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["user-organizations"],
      });
    },
  });
};
