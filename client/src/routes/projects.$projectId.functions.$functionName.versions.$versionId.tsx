import { LLMFunction } from "@/components/LLMFunction";
import { versionsByFunctionNameQueryOptions } from "@/utils/versions";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, useParams } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/projects/$projectId/functions/$functionName/versions/$versionId"
)({
  component: () => {
    const { projectId, functionName, versionId } = useParams({
      from: Route.id,
    });
    const { data: versions } = useSuspenseQuery(
      versionsByFunctionNameQueryOptions(Number(projectId), functionName)
    );
    return (
      <LLMFunction
        projectId={Number(projectId)}
        defaultFunctionName={functionName}
        versions={versions}
        versionId={Number(versionId)}
      />
    );
  },
});
