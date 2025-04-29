import { LilypadLoading } from "@/components/LilypadLoading";
import { Typography } from "@/components/ui/typography";
import { VersionedPlayground } from "@/ee/components/VersionedPlayground";
import { useFeatureAccess } from "@/hooks/use-featureaccess";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";
import { validate } from "uuid";

export interface PlaygroundRouteParams {
  projectUuid: string;
  functionName: string;
  functionUuid: string;
  secondFunctionUuid?: string;
  isCompare: boolean;
}
export const Route = createFileRoute("/_auth/projects/$projectUuid/playground")(
  {
    params: {
      stringify(params: PlaygroundRouteParams) {
        return {
          projectUuid: params.projectUuid,
          functionName: params.functionName,
        };
      },
      parse(raw: Record<string, string>): PlaygroundRouteParams {
        return {
          projectUuid: raw.projectUuid,
          functionName: raw.functionName,
          functionUuid: raw.functionUuid || raw.firstFunctionUuid,
          secondFunctionUuid: validate(raw.secondFunctionUuid)
            ? raw.secondFunctionUuid
            : undefined,
          isCompare: Boolean(raw.firstFunctionUuid),
        };
      },
    },

    component: () => <VersionedPlaygroundRoute />,
  }
);

const VersionedPlaygroundRoute = () => {
  const {
    projectUuid,
    functionName,
    functionUuid,
    secondFunctionUuid,
    isCompare,
  } = useParams({
    from: Route.id,
  });
  const features = useFeatureAccess();
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  if (!features.playground) {
    return (
      <div className="p-4">
        <Typography variant="h4">
          Not available for your current plan. Please upgrade to use this
          feature.
        </Typography>
      </div>
    );
  }
  return (
    <Suspense fallback={<LilypadLoading />}>
      <VersionedPlayground
        projectUuid={projectUuid}
        functions={functions}
        functionName={functionName}
        functionUuid={functionUuid}
        secondFunctionUuid={secondFunctionUuid}
        isCompare={isCompare}
      />
    </Suspense>
  );
};
