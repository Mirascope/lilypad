import api from "@/src/api";
import { UserConsentCreate, UserConsentPublic, UserConsentUpdate } from "@/src/types/types";
import { useMutation } from "@tanstack/react-query";

export const postUserConsent = async (userConsentCreate: UserConsentCreate) => {
  return (await api.post<UserConsentPublic>(`/user-consents`, userConsentCreate)).data;
};

export const useCreateUserConsentMutation = () => {
  return useMutation({
    mutationFn: async (userConsentCreate: UserConsentCreate) =>
      await postUserConsent(userConsentCreate),
  });
};

export const patchUserConsent = async (
  userConsentUuid: string,
  userConsentUpdate: UserConsentUpdate
) => {
  return (
    await api.patch<UserConsentPublic>(`/user-consents/${userConsentUuid}`, userConsentUpdate)
  ).data;
};

export const useUpdateUserConsentMutation = () => {
  return useMutation({
    mutationFn: async ({
      userConsentUuid,
      userConsentUpdate,
    }: {
      userConsentUuid: string;
      userConsentUpdate: UserConsentUpdate;
    }) => await patchUserConsent(userConsentUuid, userConsentUpdate),
  });
};
