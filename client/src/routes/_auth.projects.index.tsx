import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { CodeSnippet } from "@/components/CodeSnippet";
import { projectsQueryOptions } from "@/utils/projects";
import { useEffect } from "react";
import { useDeviceCodeMutation } from "@/utils/auth";
export const Route = createFileRoute("/_auth/projects/")({
  validateSearch: (search) => {
    return {
      redirect: (search.redirect as string) || undefined,
      deviceCode: (search.deviceCode as string) || undefined,
    };
  },
  component: () => <Projects />,
});

const Projects = () => {
  const { deviceCode } = Route.useSearch();
  const navigate = useNavigate();
  const addDeviceCodeMutation = useDeviceCodeMutation();
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
        <p className='text-lg'>Select a project to view its traces.</p>
        {projects.length > 0 ? (
          projects.map((project) => (
            <Link key={project.uuid} to={`/projects/${project.uuid}/functions`}>
              <Card
                key={project.uuid}
                className='flex items-center justify-center transition-colors hover:bg-gray-100 dark:hover:bg-gray-800'
              >
                <CardContent className='p-4'>{project.name}</CardContent>
              </Card>
            </Link>
          ))
        ) : (
          <>
            <div>No projects found. To create a project run</div>
            <CodeSnippet code='lilypad start' />
          </>
        )}
      </div>
    </div>
  );
};
