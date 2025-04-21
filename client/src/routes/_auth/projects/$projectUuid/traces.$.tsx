import { useSuspenseQuery } from "@tanstack/react-query";

import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchBar } from "@/components/SearchBar";
import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Typography } from "@/components/ui/typography";
import { SpanPublic } from "@/types/types";
import { projectQueryOptions } from "@/utils/projects";
import { tracesQueryOptions } from "@/utils/traces";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, useEffect, useState } from "react";
export const Route = createFileRoute("/_auth/projects/$projectUuid/traces/$")({
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Trace />
    </Suspense>
  ),
});

export const Trace = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  return (
    <div className='pt-4 pb-1 h-screen flex flex-col px-2'>
      <Typography variant='h2'>{project.name}</Typography>
      <div className='flex-1 overflow-auto'>
        <Suspense fallback={<TableSkeleton />}>
          <TraceBody />
        </Suspense>
      </div>
    </div>
  );
};

export const TraceBody = () => {
  const { projectUuid, _splat: traceUuid } = useParams({ from: Route.id });
  const { data: defaultData } = useSuspenseQuery(
    tracesQueryOptions(projectUuid)
  );

  const [displayData, setDisplayData] = useState<SpanPublic[] | undefined>(
    defaultData
  );

  useEffect(() => {
    setDisplayData(defaultData);
  }, [defaultData]);

  return (
    <div className='space-y-4'>
      <SearchBar
        projectUuid={projectUuid}
        defaultData={defaultData}
        onDataChange={setDisplayData}
      />

      <TracesTable
        data={displayData ?? []}
        traceUuid={traceUuid}
        path={Route.fullPath}
      />
    </div>
  );
};
