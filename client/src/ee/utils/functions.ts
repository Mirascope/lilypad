import api from "@/api";
import { PlaygroundParameters } from "@/types/types";
import { useMutation } from "@tanstack/react-query";
import { AxiosResponse } from "axios";

export const runPlayground = async (
  projectUuid: string,
  functionUuid: string,
  playgroundParameters: PlaygroundParameters
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `/ee/projects/${projectUuid}/functions/${functionUuid}/playground`,
      playgroundParameters
    )
  ).data;
};

export const useRunPlaygroundMutation = () => {
  return useMutation({
    mutationFn: async ({
      projectUuid,
      functionUuid,
      playgroundParameters,
    }: {
      projectUuid: string;
      functionUuid: string;
      playgroundParameters: PlaygroundParameters;
    }) => await runPlayground(projectUuid, functionUuid, playgroundParameters),
  });
};
