import { isLilypadCloud } from "@/ee/utils/common";
import { cloudFeatures, selfHostedFeatures } from "@/ee/utils/features";
import { licenseQueryOptions } from "@/ee/utils/organizations";
import { useSuspenseQuery } from "@tanstack/react-query";
export const useFeatureAccess = () => {
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  if (isLilypadCloud()) {
    return cloudFeatures[licenseInfo.tier];
  } else {
    return selfHostedFeatures[licenseInfo.tier];
  }
};
