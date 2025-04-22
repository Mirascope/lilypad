import { Suspense } from "react";
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
import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Typography } from "@/components/ui/typography";

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
  const queryClient = useQueryClient();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
    isRefetching,
  } = useInfiniteQuery(tracesInfiniteQueryOptions(projectUuid));

  const pages = data?.pages ?? [];
  const flattened = pages.flatMap((p) => p.items);

  const handleReachEnd = () => {
    if (hasNextPage && !isFetchingNextPage) {
      void fetchNextPage();
    }
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
    <TracesTable
      data={flattened}
      traceUuid={traceUuid}
      path={Route.fullPath}
      onReachEnd={handleReachEnd}
      isFetchingNextPage={isFetchingNextPage}
      onLoadNewer={handleLoadNewer}
      isLoadingNewer={isRefetching}
    />
  );
};
