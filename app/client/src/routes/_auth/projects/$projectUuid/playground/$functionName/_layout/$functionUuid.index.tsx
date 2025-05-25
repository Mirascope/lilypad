import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/playground/$functionName/_layout/$functionUuid/"
)({
  component: RouteComponent,
});

function RouteComponent() {
  return null;
}
