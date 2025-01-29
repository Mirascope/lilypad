import api from "@/api";
import {
  OrganizationInviteCreate,
  OrganizationInvitePublic,
} from "@/types/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export const createOrganizationInvite = async (
  data: OrganizationInviteCreate
) => {
  return (
    await api.post<OrganizationInvitePublic>(`/organizations/invites`, data)
  ).data;
};

export const useCreateOrganizationInviteMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OrganizationInviteCreate) =>
      await createOrganizationInvite(data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["organization-invites"],
      });
    },
  });
};
