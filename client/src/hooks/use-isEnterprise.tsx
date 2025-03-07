import { Tier } from "@/ee/types/types";
import { licenseQueryOptions } from "@/ee/utils/ee";
import { useSuspenseQuery } from "@tanstack/react-query";

export const useIsEnterprise = (projectUuid: string) => {
  const { data: licenseInfo } = useSuspenseQuery(
    licenseQueryOptions(projectUuid)
  );
  return licenseInfo === Tier.ENTERPRISE;
};
