import { useInfiniteQuery, InfiniteData } from "@tanstack/react-query";
import {
  tracesInfiniteQueryOptions,
  type TracePageParam,
} from "@/utils/traces";
import { PaginatedSpanPublic } from "@/types/types";
import { useMemo } from "react";

export const useInfiniteTraces = (projectUuid: string, pageSize: number) => {
  const query = useInfiniteQuery<
    PaginatedSpanPublic,
    Error,
    InfiniteData<PaginatedSpanPublic, TracePageParam>,
    ReturnType<typeof tracesInfiniteQueryOptions>["queryKey"],
    TracePageParam
  >(tracesInfiniteQueryOptions(projectUuid, pageSize));
  
  const defaultData = useMemo(
    () => query.data?.pages.flatMap((p) => p.items) ?? [],
    [query.data?.pages],
  );
  
  return { ...query, defaultData };
};
