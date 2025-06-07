import { isLilypadCloud } from "@/src/ee/utils/common";
import { cloudFeatures, selfHostedFeatures } from "@/src/ee/utils/features";
import { licenseQueryOptions } from "@/src/ee/utils/organizations";
import { useSuspenseQuery } from "@tanstack/react-query";
export const useFeatureAccess = () => {
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  if (isLilypadCloud()) {
    return cloudFeatures[licenseInfo.tier];
  } else {
    return selfHostedFeatures[licenseInfo.tier];
  }
};
