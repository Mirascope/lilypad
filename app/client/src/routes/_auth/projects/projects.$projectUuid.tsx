import { projectQueryOptions } from "@/src/utils/projects";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Outlet, useParams } from "@tanstack/react-router";
export const Route = createFileRoute("/_auth/projects/projects/$projectUuid")({
  component: () => <Project />,
});

export const Project = () => {
  const { projectUuid } = useParams({ from: Route.id });
  useSuspenseQuery(projectQueryOptions(projectUuid));
  return <Outlet />;
};
