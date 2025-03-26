import { LilypadLoading } from "@/components/LilypadLoading";
import { VersionedPlayground } from "@/ee/components/VersionedPlayground";
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
export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/playground/$functionName"
)({
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
});

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
  console.log(functionUuid);
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
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
