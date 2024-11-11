import { ProjectPublic, SpanPublic } from "@/types/types";
import { useQuery } from "@tanstack/react-query";

import { TracesTable } from "@/components/TracesTable";
import {
  createFileRoute,
  useLoaderData,
  useParams,
} from "@tanstack/react-router";
import api from "@/api";
import { Typography } from "@/components/ui/typography";

export const Route = createFileRoute("/projects/$projectId/traces")({
  loader: async ({ params: { projectId } }) =>
    (await api.get<ProjectPublic>(`/projects/${projectId}`)).data,
  pendingComponent: () => <div>Loading...</div>,
  errorComponent: ({ error }) => <div>{error.message}</div>,
  component: () => <Trace />,
});

export const Trace = () => {
  const { projectId } = useParams({ from: Route.id });
  const project = useLoaderData({ from: Route.id }) as ProjectPublic;
  const { isPending, error, data } = useQuery<SpanPublic[]>({
    queryKey: ["traces"],
    queryFn: async () => (await api.get(`/projects/${projectId}/traces`)).data,
    refetchInterval: 1000,
  });
  if (isPending) return <div>Loading...</div>;
  if (error) return <div>An error occurred: {error.message}</div>;
  return (
    <div className='h-screen p-2'>
      <Typography variant='h2'>{project.name}</Typography>
      <TracesTable data={data} />
    </div>
  );
};
