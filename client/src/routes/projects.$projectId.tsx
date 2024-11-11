import { createFileRoute, Outlet, useParams } from "@tanstack/react-router";
import { projectQueryOptions } from "@/utils/projects";
import { useSuspenseQuery } from "@tanstack/react-query";
export const Route = createFileRoute("/projects/$projectId")({
  component: () => <Project />,
});

export const Project = () => {
  const { projectId } = useParams({ from: Route.id });
  useSuspenseQuery(projectQueryOptions(projectId));
  return <Outlet />;
};
