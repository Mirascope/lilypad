import api from "@/api";
import { PromptPublic, PromptUpdate } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export const fetchPromptsByName = async (
  promptName: string,
  projectUuid?: string
) => {
  if (!projectUuid || !promptName) return [];

  return (
    await api.get<PromptPublic[]>(
      `/projects/${projectUuid}/prompts/name/${promptName}`
    )
  ).data;
};

export const patchPrompt = async (
  projectUuid: string,
  promptUuid: string,
  promptUpdate: PromptUpdate
) => {
  return (
    await api.patch<PromptPublic>(
      `/projects/${projectUuid}/prompts/${promptUuid}/default`,
      promptUpdate
    )
  ).data;
};

export const fetchPrompt = async (projectUuid: string, promptUuid?: string) => {
  if (!promptUuid) return null;
  return (
    await api.get<PromptPublic>(
      `/projects/${projectUuid}/prompts/${promptUuid}`
    )
  ).data;
};

export const fetchPromptsBySignature = async (
  projectUuid: string,
  signature?: string
) => {
  if (!signature) return [];
  const params = new URLSearchParams({
    signature,
  });
  return (
    await api.get<PromptPublic[]>(
      `/projects/${projectUuid}/prompts/metadata/signature?${params.toString()}`
    )
  ).data;
};

export const fetchLatestVersionUniquePromptNames = async (
  projectUuid?: string
) => {
  if (!projectUuid) return [];
  return (
    await api.get<PromptPublic[]>(
      `/projects/${projectUuid}/prompts/metadata/names/versions`
    )
  ).data;
};

export const archivePrompt = async (
  projectUuid: string,
  promptUuid: string
) => {
  return (
    await api.delete<boolean>(`/projects/${projectUuid}/prompts/${promptUuid}`)
  ).data;
};

export const archivePromptByName = async (
  projectUuid: string,
  promptName: string
) => {
  return (
    await api.delete<boolean>(
      `/projects/${projectUuid}/prompts/names/${promptName}`
    )
  ).data;
};

export const promptsByNameQueryOptions = (
  promptName: string,
  projectUuid?: string
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "prompts", promptName],
    queryFn: () => fetchPromptsByName(promptName, projectUuid),
    enabled: !!promptName,
  });

export const promptQueryOptions = (
  projectUuid: string,
  promptUuid?: string,
  options = {}
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "prompts", promptUuid],
    queryFn: () => fetchPrompt(projectUuid, promptUuid),
    ...options,
  });

export const uniqueLatestVersionPromptNamesQueryOptions = (
  projectUuid?: string
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "prompts", "unique-names"],
    queryFn: async () => await fetchLatestVersionUniquePromptNames(projectUuid),
  });

export const promptsBySignature = (projectUuid: string, signature?: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "prompts", "signature", signature],
    queryFn: () => fetchPromptsBySignature(projectUuid, signature),
    enabled: !!signature,
  });

export const usePatchPromptMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      promptUuid,
      promptUpdate,
    }: {
      projectUuid: string;
      promptUuid: string;
      promptUpdate: PromptUpdate;
    }) => await patchPrompt(projectUuid, promptUuid, promptUpdate),
    onSuccess: (prompt, { projectUuid }) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "prompts", prompt.uuid],
      });
    },
  });
};

export const useArchivePromptMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      promptUuid,
    }: {
      projectUuid: string;
      promptUuid: string;
    }) => await archivePrompt(projectUuid, promptUuid),
    onSuccess: (_, { projectUuid, promptUuid }) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "prompts", promptUuid],
      });
    },
  });
};

export const useArchivePromptByNameMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      promptName,
    }: {
      projectUuid: string;
      promptName: string;
    }) => await archivePromptByName(projectUuid, promptName),
    onSuccess: (_, { projectUuid }) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "prompts", "unique-names"],
      });
    },
  });
};
