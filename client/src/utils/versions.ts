import api from "@/api";
import { FunctionAndPromptVersionCreate, VersionPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { AxiosResponse } from "axios";

export const fetchVersionsByFunctionName = async (
  functionName: string,
  projectUuid?: string
) => {
  if (!projectUuid || !functionName) return [];

  return (
    await api.get<VersionPublic[]>(
      `/projects/${projectUuid}/functions/name/${functionName}/versions`
    )
  ).data;
};

export const fetchVersion = async (
  projectUuid: string,
  versionUuid?: string
) => {
  if (!versionUuid) return null;
  return (
    await api.get<VersionPublic>(
      `/projects/${projectUuid}/versions/${versionUuid}`
    )
  ).data;
};

export const createVersion = async (
  projectUuid: string,
  versionCreate: FunctionAndPromptVersionCreate
): Promise<VersionPublic> => {
  return (
    await api.post<
      FunctionAndPromptVersionCreate,
      AxiosResponse<VersionPublic>
    >(`projects/${projectUuid}/versions`, versionCreate)
  ).data;
};

export const patchVersion = async (
  projectUuid: string,
  versionUuid: string
): Promise<VersionPublic> => {
  return (
    await api.patch<undefined, AxiosResponse<VersionPublic>>(
      `projects/${projectUuid}/versions/${versionUuid}/active`
    )
  ).data;
};

export const runVersion = async (
  projectUuid: string,
  versionUuid: string,
  values: Record<string, string>
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `projects/${projectUuid}/versions/${versionUuid}/run`,
      values
    )
  ).data;
};

export const versionsByFunctionNameQueryOptions = (
  functionName: string,
  projectUuid?: string
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "functions", functionName, "versions"],
    queryFn: () => fetchVersionsByFunctionName(functionName, projectUuid),
    enabled: !!functionName,
  });

export const versionQueryOptions = (
  projectUuid: string,
  versionUuid?: string,
  options = {}
) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "versions", versionUuid],
    queryFn: () => fetchVersion(projectUuid, versionUuid),
    ...options,
  });

export const usePatchActiveVersion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectUuid,
      versionUuid,
    }: {
      projectUuid: string;
      versionUuid: string;
    }) => await patchVersion(projectUuid, versionUuid),
    onSuccess: (newVersion, { projectUuid }) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, "versions", newVersion.uuid],
      });
    },
  });
};

export const useCreateVersion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectUuid,
      versionCreate,
    }: {
      projectUuid: string;
      versionCreate: FunctionAndPromptVersionCreate;
    }) => await createVersion(projectUuid, versionCreate),
    onSuccess: (newVersion, { projectUuid }) => {
      queryClient.invalidateQueries({
        queryKey: [
          "projects",
          projectUuid,
          "functions",
          newVersion.function.name,
          "versions",
        ],
      });
    },
  });
};

export const useRunMutation = () => {
  return useMutation({
    mutationFn: async ({
      projectUuid,
      versionUuid,
      values,
    }: {
      projectUuid: string;
      versionUuid: string;
      values: Record<string, string>;
    }) => await runVersion(projectUuid, versionUuid, values),
  });
};
