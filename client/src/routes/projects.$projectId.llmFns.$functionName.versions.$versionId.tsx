import { LLMFunction } from "@/components/LLMFunction";
import { versionQueryOptions } from "@/utils/versions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/projects/$projectId/llmFns/$functionName/versions/$versionId"
)({
  component: () => {
    const { projectId, functionName, versionId } = useParams({
      from: Route.id,
    });
    const { data: version } = useSuspenseQuery(
      versionQueryOptions(Number(projectId), Number(versionId))
    );
    return (
      <LLMFunction
        projectId={Number(projectId)}
        defaultFunctionName={functionName}
        defaultVersion={version}
      />
    );
  },
});
