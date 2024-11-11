import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { CodeSnippet } from "@/components/CodeSnippet";
import { projectsQueryOptions } from "@/utils/projects";
export const Route = createFileRoute("/projects/")({
  loader: async ({ context }) => {
    await context.queryClient.ensureQueryData(projectsQueryOptions());
  },
  component: () => <Projects />,
});

const Projects = () => {
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  return (
    <div className='p-4 flex flex-col items-center gap-2'>
      <div className='text-left'>
        <h1 className='text-4xl font-bold text-left'>Projects</h1>
        <p className='text-lg'>Select a project to view its traces.</p>
        {projects.length > 0 ? (
          projects.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}/llmFns`}>
              <Card
                key={project.id}
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
