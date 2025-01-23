import { useAuth } from "@/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useDeviceCodeMutation } from "@/utils/auth";
import { projectsQueryOptions } from "@/utils/projects";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Suspense, useEffect } from "react";
export const Route = createFileRoute("/_auth/projects/")({
  validateSearch: (search) => {
    return {
      redirect: (search.redirect as string) || undefined,
      deviceCode: (search.deviceCode as string) || undefined,
    };
  },
  component: () => (
    <Suspense fallback={<div>Loading...</div>}>
      <Projects />
    </Suspense>
  ),
});

const Projects = () => {
  const { deviceCode } = Route.useSearch();
  const navigate = useNavigate();
  const addDeviceCodeMutation = useDeviceCodeMutation();
  const { setProject } = useAuth();
  useEffect(() => {
    if (!deviceCode) return;
    addDeviceCodeMutation.mutateAsync({ deviceCode });
    navigate({
      to: "/projects",
      search: { redirect: undefined, deviceCode: undefined },
    });
  }, [deviceCode]);

  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  return (
    <div className='p-4 flex flex-col items-center gap-2'>
      <div className='text-left'>
        <h1 className='text-4xl font-bold text-left'>Projects</h1>
        <p className='text-lg'>Select a project to view generations.</p>
        {projects.length > 0 ? (
          projects.map((project) => (
            <Link
              key={project.uuid}
              to={`/projects/${project.uuid}/generations`}
            >
              <Card
                key={project.uuid}
                className='flex items-center justify-center transition-colors hover:bg-gray-100 dark:hover:bg-gray-800'
                onClick={() => setProject(project)}
              >
                <CardContent className='p-4'>{project.name}</CardContent>
              </Card>
            </Link>
          ))
        ) : (
          <>
            <div>
              No projects found.
              <Button variant='ghost' asChild>
                <Link to='/settings/$' params={{ _splat: "org" }}>
                  Create a project here
                </Link>
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
