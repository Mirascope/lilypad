import api from "@/api";
import {
  OrganizationCreate,
  OrganizationInviteCreate,
  OrganizationInvitePublic,
  OrganizationPublic,
  OrganizationUpdate,
  UserPublic,
} from "@/types/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export const getOrganizationInvite = async (inviteToken: string) => {
  return (
    await api.get<OrganizationInvitePublic>(
      `/organizations-invites/${inviteToken}`
    )
  ).data;
};

export const getOrganizationInvites = async () => {
  return (await api.get<OrganizationInvitePublic[]>(`/organizations-invites/`))
    .data;
};

export const createOrganizationInvite = async (
  data: OrganizationInviteCreate
) => {
  return (
    await api.post<OrganizationInvitePublic>(`/organizations-invites`, data)
  ).data;
};

export const resendOrganizationInvite = async (
  organizationInviteUuid: string,
  data: OrganizationInviteCreate
) => {
  return (
    await api.post<OrganizationInvitePublic>(
      `/organizations-invites/${organizationInviteUuid}`,
      data
    )
  ).data;
};

export const deleteOrganizationInvite = async (
  organizationInviteUuid: string
) => {
  return (
    await api.delete<OrganizationInvitePublic>(
      `/organizations-invites/${organizationInviteUuid}`
    )
  ).data;
};

export const postOrganization = async (data: OrganizationCreate) => {
  return (await api.post<OrganizationPublic>(`/organizations`, data)).data;
};

export const updateOrganization = async (data: OrganizationUpdate) => {
  return (await api.patch<OrganizationPublic>(`/organizations`, data)).data;
};

export const deleteOrganization = async () => {
  return (await api.delete<UserPublic>(`/organizations`)).data;
};

export const organizationInviteQueryOptions = (inviteToken: string) => ({
  queryKey: ["organization-invites", inviteToken],
  queryFn: () => getOrganizationInvite(inviteToken),
});

export const organizationInvitesQueryOptions = () => ({
  queryKey: ["organization-invites"],
  queryFn: () => getOrganizationInvites(),
});

export const useDeleteOrganizationInviteMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (organizationInviteUuid: string) =>
      await deleteOrganizationInvite(organizationInviteUuid),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["organization-invites"],
      });
    },
  });
};

export const useCreateOrganizationInviteMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OrganizationInviteCreate) =>
      await createOrganizationInvite(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["organization-invites"],
      });
    },
  });
};

export const useUpdateOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OrganizationUpdate) =>
      await updateOrganization(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["license"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["user"],
      });
    },
  });
};

export const useCreateOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OrganizationCreate) =>
      await postOrganization(data),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["organizations"],
      });
    },
  });
};

export const useDeleteOrganizationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => await deleteOrganization(),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["organizations"],
      });
      await queryClient.invalidateQueries({
        queryKey: ["user"],
      });
    },
  });
};
