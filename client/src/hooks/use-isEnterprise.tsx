import { Tier } from "@/ee/types/types";
import { licenseQueryOptions } from "@/ee/utils/ee";
import { useSuspenseQuery } from "@tanstack/react-query";

const tierLevels: Record<Tier, number> = {
  [Tier.FREE]: 0,
  [Tier.PRO]: 1,
  [Tier.TEAM]: 2,
  [Tier.ENTERPRISE]: 3,
};

export const useIsEnterprise = (projectUuid: string) => {
  const { data: licenseInfo } = useSuspenseQuery(
    licenseQueryOptions(projectUuid)
  );
  return licenseInfo.tier === Tier.ENTERPRISE;
};

export const hasFeatureAccess = (
  userTier: Tier,
  featureTier: Tier
): boolean => {
  return tierLevels[userTier] >= tierLevels[featureTier];
};
