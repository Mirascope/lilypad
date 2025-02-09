import api from "@/api";
import { GenerationPublic, GenerationUpdate } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

const generationKeys = {
  all: ["generations"] as const,
  lists: () => [...generationKeys.all, "list"] as const,
  list: (filters: string) => [...generationKeys.lists(), { filters }] as const,
  details: () => [...generationKeys.all, "detail"] as const,
  detail: (uuid: string) => [...generationKeys.details(), uuid] as const,
};
export const fetchGenerationsByName = async (
  generationName: string,
  projectUuid?: string
) => {
  if (!projectUuid) return [];
  return (
    await api.get<GenerationPublic[]>(
      `/projects/${projectUuid}/generations/name/${generationName}`
    )
  ).data;
};

export const fetchLatestVersionUniqueGenerationNames = async (
  projectUuid?: string
) => {
  if (!projectUuid) return [];
  return (
    await api.get<GenerationPublic[]>(
      `/projects/${projectUuid}/generations/metadata/names/versions`
    )
  ).data;
};

export const patchGeneration = async (
  projectUuid: string,
  generationUuid: string,
  generationUpdate: GenerationUpdate
) => {
  return (
    await api.patch<GenerationPublic>(
      `/projects/${projectUuid}/generations/${generationUuid}`,
      generationUpdate
    )
  ).data;
};

export const archiveGeneration = async (
  projectUuid: string,
  generationUuid: string
) => {
  return (
    await api.delete<boolean>(
      `/projects/${projectUuid}/generations/${generationUuid}`
    )
  ).data;
};

export const archiveGenerationByName = async (
  projectUuid: string,
  generationName: string
) => {
  return (
    await api.delete<boolean>(
      `/projects/${projectUuid}/generations/names/${generationName}`
    )
  ).data;
};

export const usePatchGenerationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationUuid,
      generationUpdate,
    }: {
      projectUuid: string;
      generationUuid: string;
      generationUpdate: GenerationUpdate;
    }) => await patchGeneration(projectUuid, generationUuid, generationUpdate),
    onSuccess: (generation, { projectUuid }) => {
      queryClient.invalidateQueries({
        queryKey: generationKeys.list(generation.name),
      });
    },
  });
};

export const uniqueLatestVersionGenerationNamesQueryOptions = (
  projectUuid?: string
) =>
  queryOptions({
    queryKey: generationKeys.list("unique"),
    queryFn: async () =>
      await fetchLatestVersionUniqueGenerationNames(projectUuid),
  });

export const generationsByNameQueryOptions = (
  generationName: string,
  projectUuid?: string
) =>
  queryOptions({
    queryKey: generationKeys.list(generationName),
    queryFn: async () =>
      await fetchGenerationsByName(generationName, projectUuid),
  });

export const useArchiveGenerationMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationUuid,
    }: {
      projectUuid: string;
      generationUuid: string;
      generationName: string;
    }) => await archiveGeneration(projectUuid, generationUuid),
    onSuccess: (_, { projectUuid, generationName }) => {
      queryClient.invalidateQueries({
        queryKey: generationKeys.list(generationName),
      });
    },
  });
};

export const useArchiveGenerationByNameMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationName,
    }: {
      projectUuid: string;
      generationName: string;
    }) => await archiveGenerationByName(projectUuid, generationName),
    onSuccess: (_, { projectUuid }) => {
      queryClient.invalidateQueries({
        queryKey: generationKeys.all,
      });
    },
  });
};
