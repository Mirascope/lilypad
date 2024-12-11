import api from "@/api";
import { queryOptions } from "@tanstack/react-query";

export const fetchGenerations = async (projectUuid: string) => {
  return (await api.get(`/projects/${projectUuid}/traces`)).data;
};

export const generationsQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "traces"],
    queryFn: () => fetchGenerations(projectUuid),
    refetchInterval: 1000,
  });
