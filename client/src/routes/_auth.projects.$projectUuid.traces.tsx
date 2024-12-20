import { ProjectPublic } from "@/types/types";
import { useSuspenseQuery } from "@tanstack/react-query";

import api from "@/api";
import { TracesTable } from "@/components/TracesTable";
import { Typography } from "@/components/ui/typography";
import { tracesQueryOptions } from "@/utils/traces";
import {
  createFileRoute,
  useLoaderData,
  useParams,
} from "@tanstack/react-router";

export const Route = createFileRoute("/_auth/projects/$projectUuid/traces")({
  loader: async ({ params: { projectUuid } }) =>
    (await api.get<ProjectPublic>(`/projects/${projectUuid}`)).data,
  pendingComponent: () => <div>Loading...</div>,
  errorComponent: ({ error }) => <div>{error.message}</div>,
  component: () => <Trace />,
});

export const Trace = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const project = useLoaderData({ from: Route.id }) as ProjectPublic;
  const { data } = useSuspenseQuery(tracesQueryOptions(projectUuid));
  return (
    <div className='h-full flex flex-col px-2'>
      <Typography variant='h2'>{project.name}</Typography>
      <div className='flex-1 min-h-0 overflow-auto'>
        <TracesTable data={data} />
      </div>
    </div>
  );
};
