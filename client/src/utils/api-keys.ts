import api from "@/api";
import { APIKeyCreate, APIKeyPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export const fetchApiKeys = async () => {
  return (await api.get<APIKeyPublic[]>(`/api-keys`)).data;
};

export const postApiKey = async (apiKeyCreate: APIKeyCreate) => {
  return (await api.post<string>(`/api-keys`, apiKeyCreate)).data;
};

export const deleteApiKey = async (apiKeyUuid: string) => {
  return (await api.delete<boolean>(`/api-keys/${apiKeyUuid}`)).data;
};

export const useCreateApiKeyMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (apiKeyCreate: APIKeyCreate) =>
      await postApiKey(apiKeyCreate),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["apiKeys"],
      });
    },
  });
};

export const useDeleteApiKeyMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (apiKeyUuid: string) => await deleteApiKey(apiKeyUuid),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["apiKeys"],
      });
    },
  });
};

export const apiKeysQueryOptions = () =>
  queryOptions({
    queryKey: ["apiKeys"],
    queryFn: () => fetchApiKeys(),
  });
