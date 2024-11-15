import api from "@/api";
import { FunctionAndPromptVersionCreate, VersionPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { AxiosResponse } from "axios";

export const fetchVersionsByFunctionName = async (
  projectId: number,
  functionName: string
) => {
  return (
    await api.get<VersionPublic[]>(
      `/projects/${projectId}/functions/${functionName}/versions`
    )
  ).data;
};

export const fetchVersion = async (projectId: number, versionId?: number) => {
  if (!versionId) return null;
  return (
    await api.get<VersionPublic>(`/projects/${projectId}/versions/${versionId}`)
  ).data;
};

export const createVersion = async (
  projectId: number,
  versionCreate: FunctionAndPromptVersionCreate
): Promise<VersionPublic> => {
  return (
    await api.post<
      FunctionAndPromptVersionCreate,
      AxiosResponse<VersionPublic>
    >(`projects/${projectId}/versions`, versionCreate)
  ).data;
};

export const patchVersion = async (
  projectId: number,
  versionId: number
): Promise<VersionPublic> => {
  return (
    await api.patch<undefined, AxiosResponse<VersionPublic>>(
      `projects/${projectId}/versions/${versionId}/active`
    )
  ).data;
};

export const runVersion = async (
  projectId: number,
  versionId: number,
  values: Record<string, string>
): Promise<string> => {
  return (
    await api.post<Record<string, string>, AxiosResponse<string>>(
      `projects/${projectId}/versions/${versionId}/run`,
      values
    )
  ).data;
};

export const versionsByFunctionNameQueryOptions = (
  projectId: number,
  functionName: string
) =>
  queryOptions({
    queryKey: ["projects", projectId, "functions", functionName, "versions"],
    queryFn: () => fetchVersionsByFunctionName(projectId, functionName),
    enabled: !!functionName,
  });

export const versionQueryOptions = (
  projectId: number,
  versionId?: number,
  options = {}
) =>
  queryOptions({
    queryKey: ["projects", projectId, "versions", versionId],
    queryFn: () => fetchVersion(projectId, versionId),
    ...options,
  });

export const usePatchActiveVersion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      versionId,
    }: {
      projectId: number;
      versionId: number;
    }) => await patchVersion(projectId, versionId),
    onSuccess: (newVersion, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "versions", newVersion.id],
      });
    },
  });
};

export const useCreateVersion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      projectId,
      versionCreate,
    }: {
      projectId: number;
      versionCreate: FunctionAndPromptVersionCreate;
    }) => await createVersion(projectId, versionCreate),
    onSuccess: (newVersion, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: [
          "projects",
          projectId,
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
      projectId,
      versionId,
      values,
    }: {
      projectId: number;
      versionId: number;
      values: Record<string, string>;
    }) => await runVersion(projectId, versionId, values),
  });
};
