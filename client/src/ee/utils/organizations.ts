import api from "@/api";
import { LicenseInfo } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";

export const fetchLicense = async () => {
  return (await api.get<LicenseInfo>(`/ee/organizations/license`)).data;
};

export const licenseQueryOptions = () =>
  queryOptions({
    queryKey: ["license"],
    queryFn: () => fetchLicense(),
  });
