import api from "@/api";
import { queryOptions } from "@tanstack/react-query";

export const fetchTraces = async (projectUuid: string) => {
  return (await api.get(`/projects/${projectUuid}/traces`)).data;
};

export const tracesQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: ["projects", projectUuid, "traces"],
    queryFn: () => fetchTraces(projectUuid),
    refetchInterval: 10000,
  });
