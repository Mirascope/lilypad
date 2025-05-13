import api from "@/api";
import { EnvironmentCreate, EnvironmentPublic } from "@/types/types";
import {
  queryOptions,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { usePostHog } from "posthog-js/react";

export const fetchEnvironments = async () => {
  return (await api.get<EnvironmentPublic[]>(`/environments`)).data;
};

export const postEnvironment = async (environmentCreate: EnvironmentCreate) => {
  return (await api.post<EnvironmentPublic>(`/environments`, environmentCreate))
    .data;
};

export const deleteEnvironment = async (environmentUuid: string) => {
  return (await api.delete<boolean>(`/environments/${environmentUuid}`)).data;
};

export const useCreateEnvironmentMutation = () => {
  const queryClient = useQueryClient();
  const posthog = usePostHog();
  return useMutation({
    mutationFn: async (environmentCreate: EnvironmentCreate) =>
      await postEnvironment(environmentCreate),
    onSuccess: async () => {
      posthog.capture("environmentCreated");
      await queryClient.invalidateQueries({
        queryKey: ["environments"],
      });
    },
  });
};

export const useDeleteEnvironmentMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (environmentUuid: string) =>
      await deleteEnvironment(environmentUuid),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["environments"],
      });
    },
  });
};

export const environmentsQueryOptions = () =>
  queryOptions({
    queryKey: ["environments"],
    queryFn: () => fetchEnvironments(),
  });
