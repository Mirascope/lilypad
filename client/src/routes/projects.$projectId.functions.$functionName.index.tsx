import { LLMFunction } from "@/components/LLMFunction";
import { createFileRoute, useParams } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/projects/$projectId/functions/$functionName/"
)({
  component: () => {
    const { projectId } = useParams({
      from: Route.id,
    });
    return <LLMFunction projectId={Number(projectId)} version={null} />;
  },
});
