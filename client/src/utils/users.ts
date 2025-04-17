import api from "@/api";
import {
  UserOrganizationTable,
  UserOrganizationUpdate,
  UserPublic,
} from "@/types/types";
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
  return (await api.get<UserPublic[]>(`/ee/user-organizations/users`)).data;
};

export const fetchUserOrganizations = async () => {
  return (await api.get<UserOrganizationTable[]>(`/ee/user-organizations`))
    .data;
};

export const createUserOrganization = async (token: string) => {
  return (
    await api.post<UserPublic>(`/ee/user-organizations`, {
      token,
    })
  ).data;
};

export const updateUserOrganization = async (
  userOrganizationUuid: string,
  data: UserOrganizationUpdate
) => {
  return (
    await api.patch<UserOrganizationTable>(
      `/ee/user-organizations/${userOrganizationUuid}`,
      data
    )
  ).data;
};

export const deleteUserOrganization = async (userOrganizationUuid: string) => {
  return (
    await api.delete<boolean>(`/ee/user-organizations/${userOrganizationUuid}`)
  ).data;
};

export const userQueryOptions = () =>
  queryOptions({
    queryKey: ["user"],
    queryFn: () => fetchUser(),
  });

export const userOrganizationsQueryOptions = () =>
  queryOptions({
    queryKey: ["userOrganizations"],
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
    mutationFn: async (token: string) => await createUserOrganization(token),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["usersByOrganization"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["user"],
      });
    },
  });
};

export const useUpdateUserOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      userOrganizationUuid,
      data,
    }: {
      userOrganizationUuid: string;
      data: UserOrganizationUpdate;
    }) => await updateUserOrganization(userOrganizationUuid, data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["usersByOrganization"],
      });
    },
  });
};

export const useUpdateActiveOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ organizationUuid }: { organizationUuid: string }) =>
      await updateActiveOrganization(organizationUuid),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [] });
    },
  });
};

export const useUpdateUserKeysMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: object) => await updateUserKeys(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["user"] });
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
        queryKey: ["usersByOrganization"],
      });
    },
  });
};
