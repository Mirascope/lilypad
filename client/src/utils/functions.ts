import api from "@/api";
import { queryOptions } from "@tanstack/react-query";

export const fetchUniqueFunctionNames = async (projectId: number) =>
  (await api.get<string[]>(`/projects/${projectId}/functions/names`)).data;

export const uniqueFunctionNamesQueryOptions = (projectId: number) =>
  queryOptions({
    queryKey: ["project", projectId, "functions"],
    queryFn: async () => await fetchUniqueFunctionNames(projectId),
  });
