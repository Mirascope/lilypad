import api from "@/api";
import {
  OrganizationInviteCreate,
  OrganizationInvitePublic,
} from "@/types/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export const getOrganizationInvite = async (inviteToken: string) => {
  return (
    await api.get<OrganizationInvitePublic>(
      `/organizations/invites/${inviteToken}`
    )
  ).data;
};

export const createOrganizationInvite = async (
  data: OrganizationInviteCreate
) => {
  return (
    await api.post<OrganizationInvitePublic>(`/organizations/invites`, data)
  ).data;
};

export const organizationInviteQueryOptions = (inviteToken: string) => ({
  queryKey: ["organization-invites", inviteToken],
  queryFn: () => getOrganizationInvite(inviteToken),
});
export const useCreateOrganizationInviteMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OrganizationInviteCreate) =>
      await createOrganizationInvite(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [["organization-invites"], ["user"]],
      });
    },
  });
};
