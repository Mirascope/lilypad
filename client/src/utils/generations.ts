import api from "@/api";
import {
  GenerationCreate,
  GenerationPublic,
  GenerationUpdate,
  PlaygroundParameters,
} from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { AxiosResponse } from "axios";
import { usePostHog } from "posthog-js/react";

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

export const fetchGenerations = async (projectUuid: string) => {
  return (
    await api.get<GenerationPublic[]>(`/projects/${projectUuid}/generations/`)
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

export const createManagedGeneration = async (
  projectUuid: string,
  generationCreate: GenerationCreate
): Promise<GenerationPublic> => {
  return (
    await api.post<GenerationCreate, AxiosResponse<GenerationPublic>>(
      `/projects/${projectUuid}/managed-generations`,
      generationCreate
    )
  ).data;
};

export const runGeneration = async (
  projectUuid: string,
  playgroundValues: PlaygroundParameters
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `/projects/${projectUuid}/generations/run`,
      playgroundValues
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
    onSuccess: (generation) => {
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
    queryKey: ["projects", projectUuid, ...generationKeys.list("unique")],
    queryFn: async () =>
      await fetchLatestVersionUniqueGenerationNames(projectUuid),
  });

export const generationsQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: generationKeys.all,
    queryFn: async () => await fetchGenerations(projectUuid),
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
    onSuccess: (_, { generationName }) => {
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
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: generationKeys.all,
      });
    },
  });
};

export const useCreateManagedGeneration = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationCreate,
    }: {
      projectUuid: string;
      generationCreate: GenerationCreate;
    }) => await createManagedGeneration(projectUuid, generationCreate),
    onSuccess: (newVersion) => {
      posthog.capture("managedGenerationCreated");
      queryClient.invalidateQueries({
        queryKey: generationKeys.list(newVersion.name),
      });
    },
  });
};

export const useRunMutation = () => {
  return useMutation({
    mutationFn: async ({
      projectUuid,
      playgroundValues,
    }: {
      projectUuid: string;
      playgroundValues: PlaygroundParameters;
    }) => await runGeneration(projectUuid, playgroundValues),
  });
};
