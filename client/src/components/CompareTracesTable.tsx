import { SearchBar } from "@/components/SearchBar";
import { TracesTable } from "@/components/TracesTable";
import { SpanPublic } from "@/types/types";
import { useState, useMemo } from "react";
import { usePaginatedSpansByFunction } from "@/hooks/use-paginated-query.tsx";

export const CompareTracesTable = ({
  projectUuid,
  firstFunctionUuid,
  secondFunctionUuid,
}: {
  projectUuid: string;
  firstFunctionUuid: string;
  secondFunctionUuid?: string;
}) => {
  const q1 = usePaginatedSpansByFunction(projectUuid, firstFunctionUuid);
  const q2 = usePaginatedSpansByFunction(projectUuid, secondFunctionUuid!, {
    enabled: Boolean(secondFunctionUuid),
  });
  
  const defaultData = useMemo<SpanPublic[]>(() => {
    const p1 = q1.data?.pages ?? [];
    const p2 = q2.data?.pages ?? [];
    return [...p1.flatMap((p) => p.items), ...p2.flatMap((p) => p.items)];
  }, [q1.data?.pages, q2.data?.pages]);
  
  const [displayData, setDisplayData] = useState<SpanPublic[] | null>(null);
  
  const hasNextPage = (q1.hasNextPage || q2.hasNextPage) ?? false;
  const isFetchingNextPage = q1.isFetchingNextPage || q2.isFetchingNextPage;
  
  const handleReachEnd = async () => {
    if (!hasNextPage || isFetchingNextPage) return;
    if (q1.hasNextPage) await q1.fetchNextPage();
    else if (q2.hasNextPage) await q2.fetchNextPage();
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="py-2">
        <SearchBar
          projectUuid={projectUuid}
          onDataChange={setDisplayData}
          filterFunction={(data) =>
            data.filter(
              (item) =>
                item.function_uuid === firstFunctionUuid ||
                item.function_uuid === secondFunctionUuid,
            )
          }
        />
      </div>
      <div className="flex-1 min-h-0 overflow-auto">
        <TracesTable
          data={displayData ?? defaultData}
          projectUuid={projectUuid}
          onReachEnd={handleReachEnd}
          isFetchingNextPage={isFetchingNextPage}
          isSearch={Boolean(displayData)}
        />
      </div>
    </div>
  );
};
