import api from "@/api";
import { CallArgsCreate, VersionPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
import { AxiosResponse } from "axios";

export const fetchVersionsByFunctionName = async (
  projectId: number,
  functionName: string
) => {
  return (
    await api.get<VersionPublic[]>(
      `/projects/${projectId}/llm-fns/${functionName}/versions`
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
  llmFnId: number,
  callArgsCreate: CallArgsCreate
) => {
  return await api.post<CallArgsCreate, AxiosResponse<VersionPublic>>(
    `projects/${projectId}/llm-fns/${llmFnId}/fn-params`,
    callArgsCreate
  );
};

export const versionsByFunctionNameQueryOptions = (
  projectId: number,
  functionName: string
) =>
  queryOptions({
    queryKey: ["projects", projectId, "llm-fns", functionName, "versions"],
    queryFn: () => fetchVersionsByFunctionName(projectId, functionName),
    enabled: !!functionName,
  });

export const versionQueryOptions = (projectId: number, versionId: number) =>
  queryOptions({
    queryKey: ["projects", projectId, "versions", versionId],
    queryFn: () => fetchVersion(projectId, versionId),
  });
