import { useSuspenseQuery } from "@tanstack/react-query";

import { LilypadLoading } from "@/components/LilypadLoading";
import TableSkeleton from "@/components/TableSkeleton";
import { TracesTable } from "@/components/TracesTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Typography } from "@/components/ui/typography";
import { useSearch } from "@/hooks/use-search";
import { projectQueryOptions } from "@/utils/projects";
import { tracesQueryOptions } from "@/utils/traces";
import { createFileRoute, useParams } from "@tanstack/react-router";
import { Loader, Search, X } from "lucide-react";
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
    tracesQueryOptions(projectUuid)
  );

  // Use the existing useSearch hook
  const [searchQuery, setSearchQuery] = useState<string>("");
  const { spans: searchResults, isLoading, search } = useSearch(projectUuid);

  const displayData = searchResults ?? defaultData;

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    search(searchQuery);
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    search("");
  };

  return (
    <div className='space-y-4'>
      <div className='px-2 pt-4'>
        <form onSubmit={handleSearchSubmit} className='flex gap-2'>
          <div className='relative flex-grow'>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder='Search spans...'
              disabled={isLoading}
              className='pr-10 w-full'
            />
            {searchQuery && (
              <Button
                variant='ghost'
                size='icon'
                type='button'
                onClick={handleClearSearch}
                className='absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 h-6 w-6'
                aria-label='Clear search'
              >
                <X size={16} />
              </Button>
            )}
          </div>
          <Button
            type='submit'
            disabled={isLoading}
            className='bg-primary hover:bg-primary/80 text-white h-9'
          >
            {isLoading ? (
              <span className='flex items-center gap-2'>
                <Loader size={16} className='animate-spin' />
                Searching...
              </span>
            ) : (
              <span className='flex items-center gap-2'>
                <Search size={16} />
                Search
              </span>
            )}
          </Button>
        </form>

        {searchResults && (
          <div className='mt-2 text-sm text-gray-600'>
            Found {searchResults.length} results
          </div>
        )}
      </div>

      <TracesTable
        data={displayData}
        traceUuid={traceUuid}
        path={Route.fullPath}
      />
    </div>
  );
};
