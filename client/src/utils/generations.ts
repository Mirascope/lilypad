import api from "@/api";
import { GenerationPublic, GenerationUpdate } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

export const fetchGenerations = async (projectUuid: string) => {
  return (
    await api.get<GenerationPublic[]>(`/projects/${projectUuid}/generations`)
  ).data;
};

export const fetchGeneration = async (
  projectUuid: string,
  generationUuid: string
) => {
  return (
    await api.get<GenerationPublic>(
      `/projects/${projectUuid}/generations/${generationUuid}`
    )
  ).data;
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

export const generationsQueryOptions = (projectUuid: string, options = {}) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "generations"],
    queryFn: () => fetchGenerations(projectUuid),
    ...options,
  });

export const generationQueryOptions = (
  projectUuid: string,
  generationUuid: string,
  options = {}
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "generations", generationUuid],
    queryFn: () => fetchGeneration(projectUuid, generationUuid),
    ...options,
  });

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
        queryKey: ["projects", projectUuid, "generations", generation.uuid],
      });
    },
  });
};

export const uniqueLatestVersionGenerationNamesQueryOptions = (
  projectUuid?: string
) =>
  queryOptions({
    queryKey: ["project", projectUuid, "generations", "unique-names"],
    queryFn: async () =>
      await fetchLatestVersionUniqueGenerationNames(projectUuid),
  });

export const generationsByNameQueryOptions = (
  generationName: string,
  projectUuid?: string
) =>
  queryOptions({
    queryKey: [
      "project",
      projectUuid,
      "generations",
      "by-name",
      generationName,
    ],
    queryFn: async () =>
      await fetchGenerationsByName(generationName, projectUuid),
  });
