import { useSuspenseQuery } from "@tanstack/react-query";

import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchComponent } from "@/components/SearchComponent";
import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Typography } from "@/components/ui/typography";
import { useSearch } from "@/hooks/use-search";
import { projectQueryOptions } from "@/utils/projects";
import { tracesQueryOptions } from "@/utils/traces";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Suspense } from "react";

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
  const { spans: searchResults, isLoading } = useSearch(projectUuid);

  // Use search results if they exist, otherwise use default data
  const displayData =
    searchResults && searchResults.length > 0 ? searchResults : defaultData;

  return (
    <>
      <SearchComponent projectUuid={projectUuid} />
      {isLoading ? (
        <div>Loading search results...</div>
      ) : (
        <TracesTable
          data={displayData}
          traceUuid={traceUuid}
          path={Route.fullPath}
        />
      )}
    </>
  );
};
