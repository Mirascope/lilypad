import { TracesTable } from "@/components/TracesTable";
import { usePaginatedSpansByFunction } from "@/hooks/usePaginatedQuery.tsx";
import { useMemo } from "react";

export const CompareTracesTable = ({
  projectUuid,
  firstFunctionUuid,
  secondFunctionUuid,
}: {
  projectUuid: string;
  firstFunctionUuid: string;
  secondFunctionUuid?: string;
}) => {
  const first = usePaginatedSpansByFunction(projectUuid, firstFunctionUuid);
  const second = usePaginatedSpansByFunction(
    projectUuid,
    secondFunctionUuid ?? "__none__",
    { enabled: !!secondFunctionUuid }
  );
  
  const flattened = useMemo(() => {
    const firstPages = first.data?.pages ?? []
    const secondPages = second.data?.pages ?? []
    return [...firstPages.flatMap(p => p.items), ...secondPages.flatMap(p => p.items)]
  }, [first.data, second.data])
  
  const isFetchingNextPage =
    first.isFetchingNextPage || second.isFetchingNextPage;
  
  return (
    <TracesTable
      data={flattened}
      isFetchingNextPage={isFetchingNextPage}
      onReachEnd={() => {
        if (first.hasNextPage && !first.isFetchingNextPage) {
          void first.fetchNextPage();
        }
        if (second.hasNextPage && !second.isFetchingNextPage) {
          void second.fetchNextPage();
        }
      }}
    />
  );
};