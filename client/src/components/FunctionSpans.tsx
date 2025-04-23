import { TracesTable } from "@/components/TracesTable";
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
  projectUuid: string
  functionUuid: string
  traceUuid?: string
}) => {
  const {
    data,
    fetchNextPage,
    hasNextPage = false,
    isFetchingNextPage,
    isLoading,
  } = usePaginatedSpansByFunction(projectUuid, functionUuid)
  
  
  const flattened = useMemo(
    () => data?.pages.flatMap(p => p.items) ?? [],
    [data?.pages],
  )
  
  if (isLoading) {
    return <div className="p-4">Loading…</div>
  }
  
  return (
    <TracesTable
      data={flattened}
      traceUuid={traceUuid}
      path={Route.fullPath}
      onReachEnd={() => {
        if (hasNextPage && !isFetchingNextPage) {
          void fetchNextPage()
        }
      }}
      isFetchingNextPage={isFetchingNextPage}
    />
  )
}