import { Suspense, useState } from "react";
import { createFileRoute, useParams } from "@tanstack/react-router";
import {
  useInfiniteQuery,
  useSuspenseQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { z } from "zod";

import { projectQueryOptions } from "@/utils/projects";
import { tracesInfiniteQueryOptions } from "@/utils/traces";
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

const INIT_LIMIT = 80;

export const Route = createFileRoute(
  "/_auth/projects/$projectUuid/traces/$",
)({
  validateSearch: z.object({}).optional(),
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <Trace />
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
  const queryClient = useQueryClient();
  
  const [pageSize, setPageSize] = useState(INIT_LIMIT);
  
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
    isRefetching,
    defaultData,
  } = useInfiniteQuery(tracesInfiniteQueryOptions(projectUuid, pageSize));
  
  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);
  
  const pages = data?.pages ?? [];
  const flattened = pages.flatMap((p) => p.items);
  
  const ROW_HEIGHT = 45;
  
  const calcPageSize = () =>
    Math.max(20, Math.ceil((window.innerHeight / ROW_HEIGHT) * 4));
  
  const handleReachEnd = () => {
    if (!hasNextPage || isFetchingNextPage) return;
    
    setPageSize(calcPageSize());
    void fetchNextPage();
  };
  const handleLoadNewer = async () => {
    await refetch(); // refetch all pages (refetchPage not supported)
    queryClient.removeQueries({
      queryKey: ["projects", projectUuid, "traces", "infinite"],
      exact: false,
      type: "inactive",
    });
  };
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
          onReachEnd={handleReachEnd}
          isFetchingNextPage={isFetchingNextPage}
          projectUuid={projectUuid}
          onLoadNewer={handleLoadNewer}
          isLoadingNewer={isRefetching}
        />
      </div>
    </div>
  );
};
