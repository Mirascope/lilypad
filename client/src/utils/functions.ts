import api from "@/api";
import { queryOptions } from "@tanstack/react-query";

export const fetchUniqueFunctionNames = async (projectUuid?: string) => {
  if (!projectUuid) return [];
  return (await api.get<string[]>(`/projects/${projectUuid}/functions/names`))
    .data;
};
export const uniqueFunctionNamesQueryOptions = (projectUuid?: string) =>
  queryOptions({
    queryKey: ["project", projectUuid, "functions"],
    queryFn: async () => await fetchUniqueFunctionNames(projectUuid),
  });
