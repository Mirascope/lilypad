import { LLMFunction } from "@/components/LLMFunction";
import { versionQueryOptions } from "@/utils/versions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/projects/$projectId/functions/$functionName/versions/$versionId"
)({
  component: () => {
    const { projectId, versionId } = useParams({
      from: Route.id,
    });
    const { data: version } = useSuspenseQuery(
      versionQueryOptions(Number(projectId), Number(versionId))
    );
    return <LLMFunction projectId={Number(projectId)} version={version} />;
  },
});
