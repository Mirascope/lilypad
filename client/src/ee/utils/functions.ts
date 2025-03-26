import api from "@/api";
import { PlaygroundParameters } from "@/types/types";
import { useMutation } from "@tanstack/react-query";
import { AxiosResponse } from "axios";

export const runPlayground = async (
  projectUuid: string,
  functionUuid: string,
  playgroundValues: PlaygroundParameters
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `/ee/projects/${projectUuid}/functions/${functionUuid}/playground`,
      playgroundValues
    )
  ).data;
};

export const useRunPlaygroundMutation = () => {
  return useMutation({
    mutationFn: async ({
      projectUuid,
      functionUuid,
      playgroundValues,
    }: {
      projectUuid: string;
      functionUuid: string;
      playgroundValues: PlaygroundParameters;
    }) => await runPlayground(projectUuid, functionUuid, playgroundValues),
  });
};
