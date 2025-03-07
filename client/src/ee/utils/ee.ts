import api from "@/api";
import { Tier } from "@/ee/types/types";
import { queryOptions } from "@tanstack/react-query";

export const fetchLicense = async (projectUuid: string) => {
  return (await api.get<Tier>(`/ee/projects/${projectUuid}`)).data;
};

export const licenseQueryOptions = (projectUuid: string) =>
  queryOptions({
    queryKey: ["license"],
    queryFn: () => fetchLicense(projectUuid),
  });
