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

export const fetchVersion = async (projectId: number, versionId: number) => {
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

export const versionsByFunctionNameQueryOptions = (
  projectId: number,
  functionName: string
) =>
  queryOptions({
    queryKey: ["projects", projectId, "functions", functionName, "versions"],
    queryFn: () => fetchVersionsByFunctionName(projectId, functionName),
    enabled: !!functionName,
  });

export const versionQueryOptions = (projectId: number, versionId: number) =>
  queryOptions({
    queryKey: ["projects", projectId, "versions", versionId],
    queryFn: () => fetchVersion(projectId, versionId),
  });

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
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: ["projects", projectId, "versions"],
      });
    },
  });
};
