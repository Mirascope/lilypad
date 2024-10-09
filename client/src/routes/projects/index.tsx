import api from "@/api";
import { createFileRoute, Link, useLoaderData } from "@tanstack/react-router";
import { ProjectTable } from "@/types/types";
import { Card, CardContent } from "@/components/ui/card";
import { CodeSnippet } from "@/routes/-codeSnippet";

export const Route = createFileRoute("/projects/")({
  loader: async () => (await api.get<ProjectTable[]>("/projects")).data,
  component: () => <Projects />,
  pendingComponent: () => <div>Loading...</div>,
  errorComponent: ({ error }) => <div>{error.message}</div>,
});

const Projects = () => {
  const projects = useLoaderData({ from: "/projects/" }) as ProjectTable[];
  return (
    <div className='p-4 flex flex-col items-center gap-2'>
      <div className='text-left'>
        <h1 className='text-4xl font-bold text-left'>Projects</h1>
        <p className='text-lg'>Select a project to view its traces.</p>
        {projects.length > 0 ? (
          projects.map((project) => (
            <Link key={project.id} to={`/projects/${project.id}`}>
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
