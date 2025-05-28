import api from "@/api";
import { FunctionCreate, FunctionPublic, FunctionUpdate } from "@/types/types";
import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { AxiosResponse } from "axios";
import { usePostHog } from "posthog-js/react";

export const functionKeys = {
  all: ["functions"] as const,
  lists: () => [...functionKeys.all, "list"] as const,
  list: (filters: string) => [...functionKeys.lists(), { filters }] as const,
  details: () => [...functionKeys.all, "detail"] as const,
  detail: (uuid: string) => [...functionKeys.details(), uuid] as const,
};

export const createVersionedFunction = async (
  projectUuid: string,
  functionCreate: FunctionCreate
): Promise<FunctionPublic> => {
  return (
    await api.post<FunctionCreate, AxiosResponse<FunctionPublic>>(
      `/projects/${projectUuid}/versioned-functions`,
      functionCreate
    )
  ).data;
};

export const fetchFunctionsByName = async (functionName: string, projectUuid: string) => {
  if (!projectUuid || !functionName) return [];
  return (
    await api.get<FunctionPublic[]>(`/projects/${projectUuid}/functions/name/${functionName}`)
  ).data;
};

export const fetchFunctions = async (projectUuid: string) => {
  return (await api.get<FunctionPublic[]>(`/projects/${projectUuid}/functions`)).data;
};

export const fetchLatestVersionUniqueFunctionNames = async (projectUuid?: string) => {
  if (!projectUuid) return [];
  return (
    await api.get<FunctionPublic[]>(`/projects/${projectUuid}/functions/metadata/names/versions`)
  ).data;
};

export const patchFunction = async (
  projectUuid: string,
  functionUuid: string,
  functionUpdate: FunctionUpdate
) => {
  return (
    await api.patch<FunctionPublic>(
      `/projects/${projectUuid}/functions/${functionUuid}`,
      functionUpdate
    )
  ).data;
};

export const archiveFunction = async (projectUuid: string, functionUuid: string) => {
  return (await api.delete<boolean>(`/projects/${projectUuid}/functions/${functionUuid}`)).data;
};

export const archiveFunctionByName = async (projectUuid: string, functionName: string) => {
  return (await api.delete<boolean>(`/projects/${projectUuid}/functions/names/${functionName}`))
    .data;
};

export const useCreateVersionedFunctionMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      functionCreate,
    }: {
      projectUuid: string;
      functionCreate: FunctionCreate;
    }) => await createVersionedFunction(projectUuid, functionCreate),
    onSuccess: async (newVersion) => {
      posthog.capture("playgroundFunctionCreated");
      await queryClient.invalidateQueries({
        queryKey: functionKeys.list(newVersion.name),
      });
    },
  });
};

export const usePatchFunctionMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      functionUuid,
      functionUpdate,
    }: {
      projectUuid: string;
      functionUuid: string;
      functionUpdate: FunctionUpdate;
    }) => await patchFunction(projectUuid, functionUuid, functionUpdate),
    onSuccess: async (fn) => {
      await queryClient.invalidateQueries({
        queryKey: functionKeys.list(fn.name),
      });
    },
  });
};

export const uniqueLatestVersionFunctionNamesQueryOptions = (projectUuid?: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, ...functionKeys.list("unique")],
    queryFn: async () => await fetchLatestVersionUniqueFunctionNames(projectUuid),
  });

export const functionsQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: functionKeys.all,
    queryFn: async () => await fetchFunctions(projectUuid),
  });

export const functionsByNameQueryOptions = (functionName: string, projectUuid: string) =>
  queryOptions({
    queryKey: functionKeys.list(functionName),
    queryFn: async () => await fetchFunctionsByName(functionName, projectUuid),
    enabled: !!functionName,
  });

export const useArchiveFunctionMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      functionUuid,
    }: {
      projectUuid: string;
      functionUuid: string;
      functionName: string;
    }) => await archiveFunction(projectUuid, functionUuid),
    onSuccess: async (_, { functionName }) => {
      await queryClient.invalidateQueries({
        queryKey: functionKeys.list(functionName),
      });
    },
  });
};

export const useArchiveFunctionByNameMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      projectUuid,
      functionName,
    }: {
      projectUuid: string;
      functionName: string;
    }) => await archiveFunctionByName(projectUuid, functionName),
    onSuccess: async (_, { projectUuid }) => {
      await queryClient.invalidateQueries({
        queryKey: ["projects", projectUuid, ...functionKeys.list("unique")],
      });
    },
  });
};
