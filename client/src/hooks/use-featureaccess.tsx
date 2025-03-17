import { features } from "@/ee/utils/features";
import { licenseQueryOptions } from "@/ee/utils/organizations";
import { useSuspenseQuery } from "@tanstack/react-query";

export const useFeatureAccess = () => {
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  return features[licenseInfo.tier];
};
