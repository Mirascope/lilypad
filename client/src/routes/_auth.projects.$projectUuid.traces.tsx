import { useSuspenseQuery } from "@tanstack/react-query";

import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Typography } from "@/components/ui/typography";
import { projectQueryOptions } from "@/utils/projects";
import { tracesQueryOptions } from "@/utils/traces";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";

export const Route = createFileRoute("/_auth/projects/$projectUuid/traces")({
  component: () => (
    <Suspense fallback={<div>Loading...</div>}>
      <Trace />
    </Suspense>
  ),
});

export const Trace = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  return (
    <div className='h-full flex flex-col px-2'>
      <Typography variant='h2'>{project.name}</Typography>
      <div className='flex-1 min-h-0 overflow-auto'>
        <Suspense fallback={<TableSkeleton />}>
          <TraceBody projectUuid={projectUuid} />
        </Suspense>
      </div>
    </div>
  );
};

export const TraceBody = ({ projectUuid }: { projectUuid: string }) => {
  const { data } = useSuspenseQuery(tracesQueryOptions(projectUuid));
  return <TracesTable data={data} />;
};
