import api from "@/api";
import {
  ExternalAPIKeyCreate,
  ExternalAPIKeyPublic,
  ExternalAPIKeyUpdate,
} from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export const fetchExternalApiKeys = async () => {
  return (await api.get<ExternalAPIKeyPublic[]>(`/external-api-keys`)).data;
};

export const patchExternalApiKey = async (
  serviceName: string,
  externalApiKeysUpdate: ExternalAPIKeyUpdate
) => {
  return (
    await api.patch<ExternalAPIKeyPublic>(
      `/external-api-keys/${serviceName}`,
      externalApiKeysUpdate
    )
  ).data;
};

export const postExternalApiKey = async (
  externalApiKeyCreate: ExternalAPIKeyCreate
) => {
  return (await api.post<string>(`/external-api-keys`, externalApiKeyCreate))
    .data;
};

export const deleteExternalApiKey = async (serviceName: string) => {
  return (await api.delete<boolean>(`/external-api-keys/${serviceName}`)).data;
};

export const usePatchExternalApiKeyMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      serviceName,
      externalApiKeysUpdate,
    }: {
      serviceName: string;
      externalApiKeysUpdate: ExternalAPIKeyUpdate;
    }) => await patchExternalApiKey(serviceName, externalApiKeysUpdate),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["externalApiKeys"],
      });
    },
  });
};
export const useCreateExternalApiKeyMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (externalApiKeysCreate: ExternalAPIKeyCreate) =>
      await postExternalApiKey(externalApiKeysCreate),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["externalApiKeys"],
      });
    },
  });
};

export const useDeleteExternalApiKeyMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (apiKeyUuid: string) =>
      await deleteExternalApiKey(apiKeyUuid),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["externalApiKeys"],
      });
    },
  });
};

export const externalApiKeysQueryOptions = () =>
  queryOptions({
    queryKey: ["externalApiKeys"],
    queryFn: () => fetchExternalApiKeys(),
  });
