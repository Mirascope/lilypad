import { useSuspenseQuery } from "@tanstack/react-query";
import { z } from "zod";

import { ComparePanel } from "@/components/ComparePanel";
import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchBar } from "@/components/SearchBar";
import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Button } from "@/components/ui/button";
import { Typography } from "@/components/ui/typography";
import { useInfiniteTraces } from "@/hooks/use-infinite-traces";
import {
  SelectedRowsProvider,
  useSelectedRows,
} from "@/hooks/use-selected-rows";
import { SpanPublic } from "@/types/types";
import { projectQueryOptions } from "@/utils/projects";
import { formatRelativeTime } from "@/utils/strings";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense, useState } from "react";

const INIT_LIMIT = 80;

export const Route = createFileRoute("/_auth/projects/$projectUuid/traces/$")({
  validateSearch: z.object({}).optional(),
  component: () => (
    <Suspense fallback={<LilypadLoading />}>
      <SelectedRowsProvider>
        <Trace />
      </SelectedRowsProvider>
    </Suspense>
  ),
});

const Trace = () => {
  const { projectUuid, _splat: traceUuid } = useParams({ from: Route.id });
  const { data: project } = useSuspenseQuery(projectQueryOptions(projectUuid));
  const { rows } = useSelectedRows();
  const [isComparing, setIsComparing] = useState(false);

  const [pageSize] = useState(INIT_LIMIT);
  const [searchData, setSearchData] = useState<SpanPublic[] | null>(null);
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    defaultData,
    isLoading,
    dataUpdatedAt,
  } = useInfiniteTraces(projectUuid, pageSize, order);

  const handleReachEnd = async () => {
    if (!hasNextPage || isFetchingNextPage) return;
    await fetchNextPage();
  };

  // If comparing, show the compare panel
  if (isComparing) {
    return (
      <div className="h-screen flex flex-col gap-4 p-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setIsComparing(false)}
          className="mb-4 w-fit"
        >
          ← Back to Traces
        </Button>
        <ComparePanel rows={rows} onClose={() => setIsComparing(false)} />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col gap-4 p-4">
      <div className="flex flex-col gap-1">
        <div className="flex justify-between items-center">
          <Typography variant="h3">{project.name}</Typography>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setIsComparing(true)}
            disabled={rows.length !== 2}
            className="whitespace-nowrap"
          >
            Compare
          </Button>
        </div>
        <Typography variant="span" affects="muted">
          Last updated: {formatRelativeTime(new Date(dataUpdatedAt))}
        </Typography>
      </div>

      <div className="flex-1 overflow-auto">
        <Suspense fallback={<TableSkeleton />}>
          <div className="flex flex-col h-full">
            <div className="shrink-0 py-4">
              <SearchBar
                projectUuid={projectUuid}
                onDataChange={setSearchData}
              />
            </div>
            <div className="flex-1 min-h-0 overflow-auto">
              {isLoading && (
                <div className="flex items-center justify-center h-full">
                  <LilypadLoading />
                </div>
              )}
              <TracesTable
                data={searchData ?? defaultData}
                traceUuid={traceUuid}
                path={Route.fullPath}
                isSearch={Boolean(searchData)}
                fetchNextPage={handleReachEnd}
                isFetchingNextPage={isFetchingNextPage}
                projectUuid={projectUuid}
                order={order}
                onOrderChange={setOrder}
              />
            </div>
          </div>
        </Suspense>
      </div>
    </div>
  );
};
