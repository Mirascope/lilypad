import LilypadDialog from "@/src/components/LilypadDialog.tsx";
import { Badge } from "@/src/components/ui/badge.tsx";
import { Typography } from "@/src/components/ui/typography";
import { isLilypadCloud } from "@/src/ee/utils/common.ts";
import { licenseQueryOptions } from "@/src/ee/utils/organizations.ts";
import { Tier } from "@/src/types/types.ts";
import { useSuspenseQuery } from "@tanstack/react-query";

const tier = {
  [Tier.FREE]: "Free",
  [Tier.PRO]: "Pro",
  [Tier.TEAM]: "Team",
};

export const PlanList = () => {
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());

  return (
    <>
      <Typography variant="h4">Available Plans</Typography>
      <div className="flex flex-wrap gap-2">
        {Object.entries(tier).map(([tierKey, tierName]) => {
          const tierNumber = Number(tierKey);
          const isCurrentPlan = licenseInfo.tier.valueOf() === tierNumber;
          const deploymentType = isLilypadCloud() ? "Cloud" : "Self-Host";
          const fullPlanName = `${deploymentType} ${tierName}`;
          const isTeamOrProPlus = tierNumber === Tier.TEAM.valueOf();

          return (
            <div key={tierKey} className="inline-block">
              {isCurrentPlan ? (
                <Badge pill variant="default" className="cursor-default" size="lg">
                  {fullPlanName} (Current)
                </Badge>
              ) : (
                <LilypadDialog
                  title={`Upgrade to ${fullPlanName}`}
                  description={
                    isTeamOrProPlus
                      ? `Contact us to upgrade your plan to ${tierName} during the beta period without billing.`
                      : `Contact us to learn more about the ${tierName} plan.`
                  }
                  customTrigger={
                    <Badge
                      pill
                      variant="secondary"
                      className="cursor-pointer hover:bg-gray-100"
                      size="lg"
                    >
                      {fullPlanName}
                    </Badge>
                  }
                >
                  <div className="p-4">
                    <p>
                      Please email us at{" "}
                      <a
                        href="mailto:support@mirascope.com"
                        className="text-blue-500 hover:underline"
                      >
                        support@mirascope.com
                      </a>{" "}
                      to request an upgrade to the {tierName} plan.
                    </p>
                    {isTeamOrProPlus && (
                      <p className="mt-2">
                        During the beta period, this plan may be available without billing for
                        eligible users.
                      </p>
                    )}
                  </div>
                </LilypadDialog>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
};
