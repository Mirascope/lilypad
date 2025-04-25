import { SearchBar } from "@/components/SearchBar";
import { TracesTable } from "@/components/TracesTable";
import {
  Route
} from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$.tsx";
import { SpanPublic } from "@/types/types";
import { spansByFunctionQueryOptions } from "@/utils/spans";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  Route
} from "@/routes/_auth/projects/$projectUuid/functions/$functionName/_workbench/$functionUuid.$tab.$.tsx";
import { usePaginatedSpansByFunction } from "@/hooks/usePaginatedQuery.tsx";
import { useMemo } from "react";


export const FunctionSpans = ({
  projectUuid,
  functionUuid,
  traceUuid,
}: {
  projectUuid: string;
  functionUuid: string;
  traceUuid?: string;
}) => {
  const {
    data,
    fetchNextPage,
    hasNextPage = false,
    isFetchingNextPage,
    isLoading,
    defaultData,
  } = usePaginatedSpansByFunction(projectUuid, functionUuid)
  
  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);
  
  const flattened = useMemo(
    () => data?.pages.flatMap(p => p.items) ?? [],
    [data?.pages],
  )
  
  if (isLoading) {
    return <div className="p-4">Loading…</div>
  }
  
  return (
    <div className='flex flex-col h-full'>
      <div className='flex-shrink-0'>
        <SearchBar
          projectUuid={projectUuid}
          onDataChange={setDisplayData}
          filterFunction={(data) =>
            data.filter((item) => item.function_uuid === functionUuid)
          }
        />
      </div>
      <div className='flex-1 min-h-0 overflow-auto'>
        <TracesTable
          data={displayData ?? defaultData}
          traceUuid={traceUuid}
          path={Route.fullPath}
          projectUuid={projectUuid}
          onReachEnd={() => {
            if (hasNextPage && !isFetchingNextPage) {
              void fetchNextPage()
            }
          }}
          isFetchingNextPage={isFetchingNextPage}
        />
      </div>
    </div>
  );
};