import { LilypadLoading } from "@/components/LilypadLoading";
import { SearchBar } from "@/components/SearchBar";
import { TracesTable } from "@/components/traces/TracesTable";
import { usePaginatedSpansByFunction } from "@/hooks/use-paginated-query.tsx";
import { SpanPublic } from "@/types/types";
import { useState } from "react";

export const FunctionSpans = ({
  projectUuid,
  functionUuid,
  traceUuid,
}: {
  projectUuid: string;
  functionUuid: string;
  traceUuid?: string;
}) => {
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    defaultData,
  } = usePaginatedSpansByFunction(projectUuid, order, functionUuid);

  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LilypadLoading />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="shrink-0">
        <SearchBar
          projectUuid={projectUuid}
          onDataChange={setDisplayData}
          filterFunction={(data) =>
            data.filter((item) => item.function_uuid === functionUuid)
          }
        />
      </div>
      <div className="flex-1 min-h-0 overflow-auto">
        <TracesTable
          data={displayData ?? defaultData}
          traceUuid={traceUuid}
          projectUuid={projectUuid}
          fetchNextPage={() => {
            if (hasNextPage && !isFetchingNextPage) {
              void fetchNextPage();
            }
          }}
          isFetchingNextPage={isFetchingNextPage}
          isSearch={Boolean(displayData)}
          order={order}
          onOrderChange={setOrder}
        />
      </div>
    </div>
  );
};
