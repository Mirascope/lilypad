import { useSuspenseQuery } from "@tanstack/react-query";

import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchBar } from "@/components/SearchBar";
import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Typography } from "@/components/ui/typography";
import { SpanPublic } from "@/types/types";
import { projectQueryOptions } from "@/utils/projects";
import { spansQueryOptions } from "@/utils/spans";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, useState } from "react";
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
    spansQueryOptions(projectUuid)
  );

  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);
  return (
    <div className='flex flex-col h-full'>
      <div className='flex-shrink-0 py-4'>
        <SearchBar projectUuid={projectUuid} onDataChange={setDisplayData} />
      </div>
      <div className='flex-1 min-h-0 overflow-auto'>
        <TracesTable
          data={displayData ?? defaultData}
          traceUuid={traceUuid}
          path={Route.fullPath}
          isSearch={Boolean(displayData)}
          projectUuid={projectUuid}
        />
      </div>
    </div>
  );
};
