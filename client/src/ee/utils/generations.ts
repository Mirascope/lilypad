import api from "@/api";
import { PlaygroundParameters } from "@/types/types";
import { useMutation } from "@tanstack/react-query";
import { AxiosResponse } from "axios";

export const runPlayground = async (
  projectUuid: string,
  generationUuid: string,
  playgroundValues: PlaygroundParameters
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `/ee/projects/${projectUuid}/generations/${generationUuid}/playground`,
      playgroundValues
    )
  ).data;
};

export const useRunPlaygroundMutation = () => {
  return useMutation({
    mutationFn: async ({
      projectUuid,
      generationUuid,
      playgroundValues,
    }: {
      projectUuid: string;
      generationUuid: string;
      playgroundValues: PlaygroundParameters;
    }) => await runPlayground(projectUuid, generationUuid, playgroundValues),
  });
};
