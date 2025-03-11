import { licenseQueryOptions } from "@/ee/utils/organizations";
import { features } from "@/ee/utils/tier";
import { useSuspenseQuery } from "@tanstack/react-query";

export const useFeatureAccess = () => {
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  return features[licenseInfo.tier];
};
