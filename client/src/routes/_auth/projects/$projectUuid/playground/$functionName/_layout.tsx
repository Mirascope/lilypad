import { PlaygroundContainer } from "@/ee/components/PlaygroundContainer";
import { functionsByNameQueryOptions } from "@/utils/functions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/playground/$functionName/_layout"
)({
  component: RouteComponent,
});

function RouteComponent() {
  const { projectUuid, functionName, functionUuid } = useParams({
    from: Route.id,
  });
  const { data: functions } = useSuspenseQuery(
    functionsByNameQueryOptions(functionName, projectUuid)
  );
  const fn = functions.find((f) => f.uuid === functionUuid) ?? null;
  return <PlaygroundContainer version={fn} isCompare={false} />;
}
