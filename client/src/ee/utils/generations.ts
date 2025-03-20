import api from "@/api";
import {
  GenerationCreate,
  GenerationPublic,
  PlaygroundParameters,
} from "@/types/types";
import { generationKeys } from "@/utils/generations";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosResponse } from "axios";
import { usePostHog } from "posthog-js/react";
export const createManagedGeneration = async (
  projectUuid: string,
  generationCreate: GenerationCreate
): Promise<GenerationPublic> => {
  return (
    await api.post<GenerationCreate, AxiosResponse<GenerationPublic>>(
      `/ee/projects/${projectUuid}/managed-generations`,
      generationCreate
    )
  ).data;
};

export const runGeneration = async (
  projectUuid: string,
  generationUuid: string,
  playgroundValues: PlaygroundParameters
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `/ee/projects/${projectUuid}/generations/${generationUuid}/run`,
      playgroundValues
    )
  ).data;
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
      generationUuid,
      playgroundValues,
    }: {
      projectUuid: string;
      generationUuid: string;
      playgroundValues: PlaygroundParameters;
    }) => await runGeneration(projectUuid, generationUuid, playgroundValues),
  });
};
