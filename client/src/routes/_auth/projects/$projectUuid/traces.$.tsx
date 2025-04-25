import { useSuspenseQuery } from "@tanstack/react-query";
import { z } from "zod";

import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchBar } from "@/components/SearchBar";
import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Typography } from "@/components/ui/typography";
import { SpanPublic } from "@/types/types";
import { projectQueryOptions } from "@/utils/projects";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, useState } from "react";
import { useInfiniteTraces } from "@/hooks/use-infinite-traces";

const INIT_LIMIT = 80;

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/traces/$",
)({
  validateSearch: z.object({}).optional(),
  component: () => (
    <Suspense fallback={<LilypadLoading/>}>
      <Trace/>
    </Suspense>
  ),
});

const Trace = () => {
  const { projectUuid } = useParams({ from: Route.id });
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  return (
    <div className="h-screen flex flex-col px-2 pt-4 pb-1">
      <Typography variant="h2">{project.name}</Typography>
      
      <div className="flex-1 overflow-auto">
        <Suspense fallback={<TableSkeleton/>}>
          <TraceBody/>
        </Suspense>
      </div>
    </div>
  );
};


export const TraceBody = () => {
  const { projectUuid, _splat: traceUuid } = useParams({ from: Route.id });
  
  const [pageSize] = useState(INIT_LIMIT);
  const [searchData, setSearchData] = useState<SpanPublic[] | null>(null);
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    defaultData,
  } = useInfiniteTraces(projectUuid, pageSize, order);
  

  
  const handleReachEnd = async () => {
    if (!hasNextPage || isFetchingNextPage) return;
    await fetchNextPage();
  };
  return (
    <div className='flex flex-col h-full'>
      <div className='flex-shrink-0 py-4'>
        <SearchBar projectUuid={projectUuid} onDataChange={setSearchData}/>
      </div>
      <div className='flex-1 min-h-0 overflow-auto'>
        <TracesTable
          data={searchData ?? defaultData}
          traceUuid={traceUuid}
          path={Route.fullPath}
          isSearch={Boolean(searchData)}
          onReachEnd={handleReachEnd}
          isFetchingNextPage={isFetchingNextPage}
          projectUuid={projectUuid}
          order={order}
          onOrderChange={setOrder}
        />
      </div>
    </div>
  );
};
