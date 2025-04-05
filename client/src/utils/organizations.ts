import api from "@/api";
import {
  OrganizationInviteCreate,
  OrganizationInvitePublic,
  OrganizationPublic,
  OrganizationUpdate,
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

export const updateOrganization = async (data: OrganizationUpdate) => {
  return (await api.patch<OrganizationPublic>(`/organizations`, data)).data;
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

export const useResendOrganizationInviteMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      organizationInviteUuid,
      data,
    }: {
      organizationInviteUuid: string;
      data: OrganizationInviteCreate;
    }) => await resendOrganizationInvite(organizationInviteUuid, data),
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
    },
  });
};
