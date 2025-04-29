import { useAuth } from "@/auth";
import { LilypadLoading } from "@/components/LilypadLoading";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
import { Route as FunctionsRoute } from "@/routes/_auth/projects/$projectUuid/functions/index";
import { projectsQueryOptions } from "@/utils/projects";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Suspense, useEffect } from "react";
import { toast } from "sonner";

interface SearchParams {
  redirect?: string;
  joined?: boolean;
}
export const Route = createFileRoute("/_auth/projects/")({
  validateSearch: (search): SearchParams => {
    return {
      redirect: (search.redirect as string) ?? undefined,
      joined: (search.joined as boolean) ?? undefined,
    };
  },
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Projects />
    </Suspense>
  ),
});

const Projects = () => {
  const { joined } = Route.useSearch();

  const { setProject } = useAuth();

  useEffect(() => {
    if (joined) {
      toast.success("Successfully joined organization");
    }
  }, [joined]);
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const activeUserOrg = user.user_organizations?.find(
    (userOrg) => userOrg.organization_uuid === user.active_organization_uuid
  );
  return (
    <div className="p-4 flex flex-col items-center gap-2">
      <div className="text-left">
        <Typography variant="h3">Projects</Typography>
        <p className="text-lg">Select a project to view functions.</p>
        {projects.length > 0 ? (
          projects.map((project) => (
            <Link
              key={project.uuid}
              to={FunctionsRoute.fullPath}
              params={{ projectUuid: project.uuid }}
            >
              <Card
                key={project.uuid}
                className="flex items-center justify-center transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => setProject(project)}
              >
                <CardContent className="p-4">{project.name}</CardContent>
              </Card>
            </Link>
          ))
        ) : !activeUserOrg ? (
          <div>
            No organization found.
            <Button variant="ghost" asChild>
              <Link to="/settings/$" params={{ _splat: "overview" }}>
                Create an organization here
              </Link>
            </Button>
          </div>
        ) : (
          <div>
            No projects found.
            <Button variant="ghost" asChild>
              <Link to="/settings/$" params={{ _splat: "org" }}>
                Create a project here
              </Link>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};
